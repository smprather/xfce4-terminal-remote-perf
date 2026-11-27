import io
import socket
import struct
import threading
import time
import unittest

from tests.xenv import XvfbFixture
from xtrp import xlat
from xtrp.rfb import RfbClient, RfbProtocolError, parse_rect_payload

ENC_RAW, ENC_COPYRECT, ENC_TIGHT, ENC_ZRLE, ENC_LASTRECT = 0, 1, 7, 16, -224


def reader(data):
    buf = io.BytesIO(data)

    def read(n):
        out = buf.read(n)
        if len(out) != n:
            raise EOFError("short read")
        return out
    return read, buf


def rect(x, y, w, h, enc):
    return struct.pack(">HHHHi", x, y, w, h, enc)


class FakeRfbServer(object):
    """Speaks just enough RFB 3.8 to hand one scripted FramebufferUpdate to a client."""

    def __init__(self, update):
        self.update = update
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.client_msgs = b""
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _recv(self, conn, n):
        data = b""
        while len(data) < n:
            chunk = conn.recv(n - len(data))
            if not chunk:
                raise EOFError
            data += chunk
        return data

    def _serve(self):
        conn, _ = self.listener.accept()
        with conn:
            conn.sendall(b"RFB 003.008\n")
            self._recv(conn, 12)
            conn.sendall(b"\x01\x01")                     # one security type: None
            self._recv(conn, 1)
            conn.sendall(struct.pack(">I", 0))            # SecurityResult OK
            self._recv(conn, 1)                           # ClientInit
            pf = struct.pack(">BBBBHHHBBB3x", 32, 24, 0, 1, 255, 255, 255, 16, 8, 0)
            conn.sendall(struct.pack(">HH", 64, 64) + pf + struct.pack(">I", 4) + b"fake")
            msgs = self._recv(conn, 20)                   # SetPixelFormat
            hdr = self._recv(conn, 4)                     # SetEncodings header
            n = struct.unpack(">xxH", hdr)[0]
            msgs += hdr + self._recv(conn, 4 * n)
            msgs += self._recv(conn, 10)                  # first FramebufferUpdateRequest
            self.client_msgs = msgs
            conn.sendall(self.update)
            try:
                while conn.recv(4096):
                    pass
            except OSError:
                pass

    def close(self):
        self.listener.close()


class RfbParseTest(unittest.TestCase):

    def test_tight_fill_is_three_byte_tpixel(self):
        read, buf = reader(b"\x80" + b"\x01\x02\x03" + b"tail")
        self.assertEqual(parse_rect_payload(ENC_TIGHT, 100, 50, read), 4)
        self.assertEqual(buf.read(), b"tail")

    def test_tight_palette_small_raw_and_compact_length(self):
        # 2-colour palette 8x1 -> 1 bit/pixel -> 1 data byte (<12: raw, no length)
        data = b"\x40" + b"\x01" + b"\x01" + b"\xaa" * 6 + b"\x55"
        read, buf = reader(data + b"tail")
        self.assertEqual(parse_rect_payload(ENC_TIGHT, 8, 1, read), len(data))
        self.assertEqual(buf.read(), b"tail")
        # 16x16 copy filter -> 768 raw bytes -> compact length 0x81 0x01 (129) + 129 zlib bytes
        data = b"\x40" + b"\x00" + b"\x81\x01" + b"z" * 129
        read, buf = reader(data + b"tail")
        self.assertEqual(parse_rect_payload(ENC_TIGHT, 16, 16, read), len(data))
        self.assertEqual(buf.read(), b"tail")

    def test_tight_palette_of_many_colours_is_8_bit(self):
        # 16 colours, 4x2 -> 8 bits/pixel -> 8 bytes (<12: raw)
        data = b"\x40\x01" + bytes([15]) + b"\x00" * 48 + b"\x07" * 8
        read, _ = reader(data)
        self.assertEqual(parse_rect_payload(ENC_TIGHT, 4, 2, read), len(data))

    def test_tight_without_filter_byte_is_copy(self):
        # no explicit filter: 24 bpp; 2x1 -> 6 bytes (<12: raw)
        data = b"\x00" + b"\x01" * 6
        read, _ = reader(data)
        self.assertEqual(parse_rect_payload(ENC_TIGHT, 2, 1, read), len(data))

    def test_tight_three_byte_compact_length(self):
        n = 0x7f | (0x7f << 7) | (3 << 14)
        data = b"\x00" + b"\xff\xff\x03" + b"z" * n
        read, _ = reader(data)
        self.assertEqual(parse_rect_payload(ENC_TIGHT, 200, 200, read), len(data))

    def test_tight_jpeg_is_a_protocol_error(self):
        read, _ = reader(b"\x90" + b"\x00" * 16)
        with self.assertRaises(RfbProtocolError):
            parse_rect_payload(ENC_TIGHT, 8, 8, read)

    def test_simple_encodings(self):
        read, _ = reader(b"\x00" * 64)
        self.assertEqual(parse_rect_payload(ENC_RAW, 2, 2, read), 16)
        read, _ = reader(b"\x00" * 4)
        self.assertEqual(parse_rect_payload(ENC_COPYRECT, 64, 32, read), 4)
        read, _ = reader(struct.pack(">I", 100) + b"z" * 100)
        self.assertEqual(parse_rect_payload(ENC_ZRLE, 64, 64, read), 104)
        read, _ = reader(b"")
        self.assertEqual(parse_rect_payload(ENC_LASTRECT, 0, 0, read), 0)

    def test_unknown_encoding_is_a_protocol_error(self):
        read, _ = reader(b"\x00" * 64)
        with self.assertRaises(RfbProtocolError):
            parse_rect_payload(5, 2, 2, read)


class RfbClientTest(unittest.TestCase):

    def test_zrle_copyrect_raw_accounting(self):
        update = (struct.pack(">BxH", 0, 3)
                  + rect(0, 0, 64, 64, ENC_ZRLE) + struct.pack(">I", 100) + b"z" * 100
                  + rect(0, 0, 64, 32, ENC_COPYRECT) + struct.pack(">HH", 0, 32)
                  + rect(0, 0, 2, 2, ENC_RAW) + b"\x00" * 16)
        server = FakeRfbServer(update)
        self.addCleanup(server.close)
        client = RfbClient("127.0.0.1", server.port, ["zrle", "copyrect", "raw"])
        client.connect()
        client.start()
        self.addCleanup(client.close)
        deadline = time.monotonic() + 5
        while client.stats()["updates"] < 1 and time.monotonic() < deadline:
            time.sleep(0.01)
        st = client.stats()
        self.assertEqual(st["updates"], 1)
        self.assertEqual(st["rects"], {"zrle": 1, "copyrect": 1, "raw": 1})
        self.assertEqual(st["copyrect_area"], 64 * 32)
        self.assertEqual(st["bytes"], len(update))

    def test_client_never_asks_for_cursor_or_jpeg(self):
        server = FakeRfbServer(struct.pack(">BxH", 0, 0))
        self.addCleanup(server.close)
        client = RfbClient("127.0.0.1", server.port, ["tight", "copyrect"])
        client.connect()
        client.start()
        self.addCleanup(client.close)
        deadline = time.monotonic() + 5
        while not server.client_msgs and time.monotonic() < deadline:
            time.sleep(0.01)
        msgs = server.client_msgs
        n = struct.unpack(">xxH", msgs[20:24])[0]
        encs = struct.unpack(">%di" % n, msgs[24:24 + 4 * n])
        self.assertIn(ENC_TIGHT, encs)
        self.assertNotIn(-239, encs)                       # Cursor
        self.assertFalse([e for e in encs if -32 <= e <= -23])  # JPEG quality levels
        self.assertEqual(msgs[24 + 4 * n:][:2], b"\x03\x00")   # first request is non-incremental


class RfbXvncTest(XvfbFixture):
    server_kind = "xvnc"

    def test_key_roundtrip_against_xvnc(self):
        win = self.start_testwin(title="rfb", delay_ms=0, rect="40x20")
        xlat.focus(self.display, win)
        client = RfbClient("127.0.0.1", self.xserver.rfb_port, ["tight", "copyrect"])
        client.connect()
        client.start()
        self.addCleanup(client.close)
        time.sleep(0.3)
        client.reset_stats()
        ms = [client.key_roundtrip_ms(0x61 if i % 2 == 0 else 0xff08) for i in range(5)]
        self.assertTrue(all(isinstance(v, float) and 0 < v < 500 for v in ms), ms)
        self.assertGreater(client.stats()["bytes"], 0)
        self.assertEqual(self.stop_testwin(win)["keys"], 5)


if __name__ == "__main__":
    unittest.main()
