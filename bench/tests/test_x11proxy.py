import socket
import struct
import subprocess
import unittest

from tests.xenv import XvfbFixture, need_tool
from xtrp import platform, xlat
from xtrp.x11proxy import X11Proxy, X11StreamParser

SETUP_LE = b"l\x00" + struct.pack("<HHHH2x", 11, 0, 0, 0)
SETUP_REPLY_LE = b"\x01\x00" + struct.pack("<HHH", 11, 0, 2) + b"\x00" * 8


def core_request(opcode, extra_words=0, big=False, big_len=None, data=0):
    if big:
        return struct.pack("<BBHI", opcode, data, 0, big_len) + b"\x00" * (big_len * 4 - 8)
    return struct.pack("<BBH", opcode, data, 1 + extra_words) + b"\x00" * (4 * extra_words)


def query_extension(name):
    name = name.encode()
    pad = (4 - len(name) % 4) % 4
    return struct.pack("<BxHH2x", 98, 2 + (len(name) + pad) // 4, len(name)) + name + b"\x00" * pad


def query_extension_reply(seq, present, major):
    return struct.pack("<BxHIBBBB", 1, seq, 0, present, major, 0, 0) + b"\x00" * 20


def event(code=12):
    return bytes([code]) + b"\x00" * 31


def generic_event(extra_words):
    return struct.pack("<BBHI", 35, 0, 0, extra_words) + b"\x00" * 24 + b"\x00" * (4 * extra_words)


def _recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise EOFError
        data += chunk
    return data


def raw_query_extension(display_number, name):
    """`present` byte of QueryExtension(name), over a raw TCP X connection to localhost:N."""
    with socket.create_connection(("127.0.0.1", 6000 + display_number), timeout=10) as s:
        s.sendall(SETUP_LE)
        head = _recv_exact(s, 8)
        _recv_exact(s, 4 * struct.unpack("<H", head[6:8])[0])
        s.sendall(query_extension(name))
        return _recv_exact(s, 32)[8]


class ParserTest(unittest.TestCase):

    def test_big_requests_length_and_opcode_names(self):
        p = X11StreamParser()
        p.feed_c2s(SETUP_LE)
        p.feed_s2c(SETUP_REPLY_LE)
        p.feed_c2s(core_request(72, big=True, big_len=5000))  # PutImage via BIG-REQUESTS
        self.assertEqual(p.stats["requests"]["core:PutImage"], 1)
        self.assertEqual(p.stats["image_bytes"], 5000 * 4)

    def test_mit_shm_hidden(self):
        p = X11StreamParser(hide_shm=True)
        p.feed_c2s(SETUP_LE)
        p.feed_s2c(SETUP_REPLY_LE)
        p.feed_c2s(query_extension("MIT-SHM"))                 # sequence 1
        out = p.feed_s2c(query_extension_reply(seq=1, present=1, major=130))
        self.assertEqual(out[8], 0)
        p.feed_c2s(core_request(130, extra_words=1, data=3))   # would-be ShmPutImage
        self.assertIn("ext130:3", p.stats["requests"])         # never learned as MIT-SHM

    def test_mit_shm_visible_when_not_hidden(self):
        p = X11StreamParser(hide_shm=False)
        p.feed_c2s(SETUP_LE)
        p.feed_s2c(SETUP_REPLY_LE)
        p.feed_c2s(query_extension("MIT-SHM"))
        out = p.feed_s2c(query_extension_reply(seq=1, present=1, major=130))
        self.assertEqual(out[8], 1)
        p.feed_c2s(core_request(130, extra_words=9, data=3))
        self.assertEqual(p.stats["requests"]["MIT-SHM:3"], 1)
        self.assertEqual(p.stats["image_bytes"], 40)

    def test_fd_passing_extensions_are_hidden(self):
        # DRI3Open replies carry a file descriptor (SCM_RIGHTS); a TCP client can never get it and
        # would hang. A real remote display does not offer DRI to a remote client either.
        p = X11StreamParser(hide_shm=True)
        p.feed_c2s(SETUP_LE)
        p.feed_s2c(SETUP_REPLY_LE)
        names = ("DRI3", "DRI2", "XFree86-DRI", "Present")
        for seq, name in enumerate(names, 1):
            p.feed_c2s(query_extension(name))
        got = [p.feed_s2c(query_extension_reply(seq=seq, present=1, major=140 + seq))[8]
               for seq in range(1, len(names) + 1)]
        self.assertEqual(got, [0, 0, 0, 1])

    def test_render_addglyphs_counts_as_image_bytes(self):
        p = X11StreamParser()
        p.feed_c2s(SETUP_LE)
        p.feed_s2c(SETUP_REPLY_LE)
        p.feed_c2s(core_request(43))                           # seq 1: GetInputFocus
        p.feed_c2s(query_extension("RENDER"))                  # seq 2
        p.feed_s2c(query_extension_reply(seq=2, present=1, major=139))
        p.feed_c2s(core_request(139, extra_words=99, data=20))
        self.assertEqual(p.stats["requests"]["RENDER:20"], 1)
        self.assertEqual(p.stats["image_bytes"], 400)

    def test_server_messages_are_classified(self):
        p = X11StreamParser()
        p.feed_c2s(SETUP_LE)
        p.feed_s2c(SETUP_REPLY_LE)
        p.feed_s2c(event(12) + event(12 | 0x80) + b"\x00" * 32 + generic_event(3)
                   + struct.pack("<BxHI", 1, 7, 2) + b"\x00" * 24 + b"\x00" * 8)
        self.assertEqual((p.stats["events"], p.stats["errors"], p.stats["replies"]), (3, 1, 1))
        self.assertEqual(p.stats["s2c_bytes"], len(SETUP_REPLY_LE) + 32 * 3 + 44 + 40)

    def test_split_feeds_parse_identically(self):
        c2s = SETUP_LE + query_extension("MIT-SHM") + core_request(72, big=True, big_len=40) + core_request(43)
        s2c = SETUP_REPLY_LE + query_extension_reply(1, 1, 130) + event() + generic_event(5)
        whole = X11StreamParser()
        out_c = whole.feed_c2s(c2s)
        out_s = whole.feed_s2c(s2c)
        split = X11StreamParser()
        got_c = b"".join(split.feed_c2s(c2s[i:i + 1]) for i in range(len(c2s)))
        got_s = b"".join(split.feed_s2c(s2c[i:i + 1]) for i in range(len(s2c)))
        self.assertEqual(split.stats, whole.stats)
        self.assertEqual((got_c, got_s), (out_c, out_s))
        self.assertEqual(out_c, c2s)
        self.assertEqual(len(out_s), len(s2c))


class ProxyTest(XvfbFixture):

    def test_proxy_adds_rtt_to_keypress_latency(self):
        with X11Proxy(self.display, rtt_ms=20) as proxy:
            win = self.start_testwin(title="slow", delay_ms=0, rect="20x20", display=proxy.display)
            xlat.focus(self.display, win)
            ms = xlat.latency(self.display, win, samples=6)
        self.assertTrue(all(v is not None and v >= 20.0 for v in ms), ms)

    def test_xdpyinfo_through_proxy(self):
        need_tool("xdpyinfo")
        with X11Proxy(self.display) as proxy:
            r = subprocess.run(["xdpyinfo", "-display", proxy.display], env=platform.helper_env(proxy.display),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            st = proxy.stats()
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        self.assertGreater(st["replies"], 0)
        self.assertGreater(st["requests"].get("core:QueryExtension", 0), 0)

    def test_real_server_reply_hides_mit_shm(self):
        # xdpyinfo prints opcodes even for absent extensions, so ask the way XShmQueryExtension does.
        for hide, expect in ((True, 0), (False, 1)):
            with self.subTest(hide_shm=hide), X11Proxy(self.display, hide_shm=hide) as proxy:
                self.assertEqual(raw_query_extension(proxy.number, "MIT-SHM"), expect)
                self.assertEqual(raw_query_extension(proxy.number, "RENDER"), 1)

    def test_proxy_display_is_on_loopback_in_range(self):
        with X11Proxy(self.display) as proxy:
            host, num = proxy.display.split(":")
            self.assertEqual(host, "localhost")
            self.assertTrue(150 <= int(num) <= 199)


if __name__ == "__main__":
    unittest.main()
