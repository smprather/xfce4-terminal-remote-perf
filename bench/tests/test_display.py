import os
import shutil
import socket
import tempfile
import unittest
from unittest import mock

from tests.xenv import need_tool, pid_alive
from xtrp import display, platform, xlat
from xtrp.display import WindowManager, XServer, WM_NAMES

WM_BINARY = {"mutter": "mutter", "marco-comp": "marco", "marco-nocomp": "marco"}


def listen_addrs(port):
    """Hex local addresses (as in /proc/net/tcp{,6}) listening on TCP `port`."""
    out = []
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as f:
                lines = f.read().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            addr, hexport = fields[1].split(":")
            if int(hexport, 16) == port and fields[3] == "0A":    # 0A = LISTEN
                out.append(addr)
    return out


class DisplayTest(unittest.TestCase):

    def test_each_wm_reports_expected_compositing(self):
        need_tool("Xvfb")
        expect = {"none": (False, False), "mutter": (True, True),
                  "marco-comp": (True, True), "marco-nocomp": (True, False)}
        self.assertEqual(sorted(expect), sorted(WM_NAMES))
        for name, (has_wm, cm) in sorted(expect.items()):
            with self.subTest(wm=name):
                if name != "none":
                    need_tool(WM_BINARY[name])
                    if not WindowManager.available(name):
                        if platform.platform_tag() == "host":
                            self.skipTest("host %s cannot run as an X11 WM (Wayland-only)" % name)
                        self.fail("%s in the bench image cannot run as an X11 WM" % name)
                with XServer("xvfb") as xs, WindowManager(name, xs.display):
                    i = xlat.info(xs.display)
                    self.assertEqual(i["wm_name"] is not None, has_wm, i["wm_name"])
                    self.assertEqual(i["cm_owner"], cm)

    def test_xvnc_exposes_rfb_port_and_vnc_extension(self):
        need_tool("Xvnc")
        with XServer("xvnc") as xs:
            self.assertEqual(xs.rfb_port, 5900 + xs.number)
            exts = xlat.info(xs.display)["extensions"]
            self.assertTrue({"VNC-EXTENSION", "TIGERVNC"} & set(exts), exts)

    def test_xvnc_listens_on_loopback_only(self):
        # Xvnc runs with -SecurityTypes None; on the host it must never be reachable from the network
        need_tool("Xvnc")
        with XServer("xvnc") as xs:
            listening = listen_addrs(xs.rfb_port)
        self.assertTrue(listening, "no listener found for port %d" % xs.rfb_port)
        self.assertTrue(all(a in ("0100007F", "00000000000000000000000001000000") for a in listening), listening)

    def test_stop_leaves_no_lock_or_process(self):
        need_tool("Xvfb")
        xs = XServer("xvfb")
        xs.start()
        n, pid = xs.number, xs.pid
        xs.stop()
        self.assertFalse(os.path.exists("/tmp/.X%d-lock" % n))
        self.assertFalse(os.path.exists("/tmp/.X11-unix/X%d" % n))
        self.assertFalse(pid_alive(pid))

    def test_busy_abstract_socket_falls_through_to_next_display(self):
        # Another server holding only @/tmp/.X11-unix/XN (no lock file) must not be mistaken for ours.
        need_tool("Xvfb")
        n = display.pick_display()
        squatter = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        squatter.bind("\0/tmp/.X11-unix/X%d" % n)
        squatter.listen(1)
        try:
            with XServer("xvfb") as xs:
                self.assertNotEqual(xs.number, n)
                self.assertEqual(xlat.info(xs.display)["width"], 1920)
        finally:
            squatter.close()
        self.assertFalse(os.path.exists("/tmp/.X%d-lock" % n))

    def test_mutter_without_x11_support_is_unavailable(self):
        # mutter >= 49 (the CachyOS host has 51) is Wayland-only: no --x11, so it cannot be an X11 WM
        tmp = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, tmp, True)
        for help_text, want in (("--wayland  Run as a Wayland compositor", False),
                                ("--x11      Run with X11 backend", True)):
            fake = os.path.join(tmp, "mutter")
            with open(fake, "w") as f:
                f.write("#!/bin/sh\necho '%s'\n" % help_text)
            os.chmod(fake, 0o755)
            display._x11_wm_ok.cache_clear()
            with mock.patch.dict(os.environ, {"PATH": tmp + os.pathsep + os.environ["PATH"]}):
                self.assertEqual(WindowManager.available("mutter"), want, help_text)
        display._x11_wm_ok.cache_clear()

    def test_available(self):
        self.assertTrue(WindowManager.available("none"))
        with self.assertRaises(ValueError):
            WindowManager("twm", ":0")


if __name__ == "__main__":
    unittest.main()
