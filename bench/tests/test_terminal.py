import os
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

from tests.xenv import group_members, need_tool, pid_alive, wait_gone
from xtrp import platform, xlat
from xtrp.display import XServer
from xtrp.model import Build, load_builds
from xtrp.terminal import FONTS, SIZES, Terminal

PLANTED = {"WAYLAND_DISPLAY": "wayland-77", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/4242/bus",
           "XDG_RUNTIME_DIR": "/run/user/4242", "XDG_SESSION_TYPE": "wayland"}


def proc_environ(pid):
    with open("/proc/%d/environ" % pid, "rb") as f:
        items = f.read().split(b"\0")
    return dict(i.decode("utf-8", "replace").split("=", 1) for i in items if b"=" in i)


class BuildRegistryTest(unittest.TestCase):

    def test_baseline_is_the_packaged_terminal(self):
        b = load_builds()["baseline"]
        self.assertIsInstance(b, Build)
        self.assertEqual((b.name, b.exec_path, b.env), ("baseline", "/usr/bin/xfce4-terminal", {}))

    def test_noise_twin_is_the_same_binary(self):
        builds = load_builds()
        self.assertEqual(builds["baseline-twin"].exec_path, builds["baseline"].exec_path)
        self.assertEqual(builds["baseline-twin"].env, builds["baseline"].env)

    def test_sizes_and_fonts(self):
        self.assertEqual(SIZES, {"small": "120x40", "large": "maximised"})
        self.assertEqual(FONTS["caskaydia"], "CaskaydiaCove Nerd Font Mono 12")
        self.assertEqual(FONTS["dejavu"], "DejaVu Sans Mono 12")


class TerminalTest(unittest.TestCase):

    def setUp(self):
        need_tool("Xvfb")
        need_tool("dbus-run-session")
        need_tool("xfce4-terminal")
        self.tmp = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.xs = XServer("xvfb").start()
        self.addCleanup(self.xs.stop)

    def _terminal(self, font="dejavu", command=("sleep", "60")):
        return Terminal(load_builds()["baseline"], self.xs.display, "small", font, list(command), self.tmp)

    def test_baseline_maps_titled_window_and_stops_cleanly(self):
        with self._terminal() as t:
            self.assertGreater(t.window, 0)
            self.assertLess(t.startup_ms, 15000)
            self.assertGreater(t.startup_ms, 0)
            with open("/proc/%d/comm" % t.pid) as f:
                self.assertTrue(f.read().startswith("xfce4-termina"))
            pid = t.pid
            children = t.descendants()
            self.assertTrue(children, "the `sleep 60` child should be running")
        self.assertFalse(pid_alive(pid))
        for child, _ in children:
            self.assertFalse(pid_alive(child), child)

    def test_interrupt_or_x_error_during_startup_leaves_no_terminal(self):
        from xtrp import terminal as terminal_mod
        for exc in (KeyboardInterrupt(), xlat.XlatError("xlat wait-window exited 1: boom", 1, [])):
            with self.subTest(exc=type(exc).__name__):
                spawned = []
                real = terminal_mod.spawn

                def spy(*args, **kw):
                    proc = real(*args, **kw)
                    spawned.append(proc)
                    return proc
                t = self._terminal()
                with mock.patch.object(terminal_mod, "spawn", spy), \
                        mock.patch.object(terminal_mod.xlat, "wait_window", side_effect=exc):
                    with self.assertRaises(type(exc)):
                        t.start()
                self.assertEqual(len(spawned), 1)
                self.assertEqual(wait_gone(lambda: group_members(spawned[0].pid)), [])

    def test_small_is_120x40_and_large_fills_the_screen_with_or_without_a_wm(self):
        # The spec's sizes: 120x40, and 1920x1080 maximised. Nothing may hang off the screen.
        from xtrp.display import WindowManager
        wms = ["none"] + (["marco-nocomp"] if WindowManager.available("marco-nocomp") else [])
        for wm in wms:
            for size in ("small", "large"):
                with self.subTest(wm=wm, size=size), WindowManager(wm, self.xs.display):
                    t = Terminal(load_builds()["baseline"], self.xs.display, size, "caskaydia",
                                 ["sleep", "60"], self.tmp).start()
                    try:
                        g = t.geometry(settle_s=3.0)
                        cols, rows = t.cells()
                    finally:
                        t.stop()
                    self.assertGreaterEqual(min(g["x"], g["y"]), 0, g)
                    self.assertLessEqual(g["x"] + g["width"], 1920, g)
                    self.assertLessEqual(g["y"] + g["height"], 1080, g)
                    if size == "small":
                        self.assertEqual((cols, rows), (120, 40))
                    else:
                        self.assertGreaterEqual(g["width"], 1800, g)
                        self.assertGreaterEqual(g["height"], 950, g)
                        self.assertGreater(cols, 150)
                        self.assertGreater(rows, 40)

    def test_stop_is_idempotent(self):
        t = self._terminal().start()
        t.stop()
        t.stop()

    def test_rc_file_carries_font_and_blink_off(self):
        with self._terminal(font="caskaydia"):
            rc_path = os.path.join(self.tmp, "home", ".config", "xfce4", "terminal", "terminalrc")
            with open(rc_path) as f:
                rc = f.read().splitlines()
            self.assertIn("FontName=CaskaydiaCove Nerd Font Mono 12", rc)
            self.assertIn("MiscCursorBlinks=FALSE", rc)
            xml_path = os.path.join(self.tmp, "home", ".config", "xfce4", "xfconf",
                                    "xfce-perchannel-xml", "xfce4-terminal.xml")
            props = {p.get("name"): (p.get("type"), p.get("value"))
                     for p in ET.parse(xml_path).getroot().iter("property")}
            self.assertEqual(props["font-name"], ("string", "CaskaydiaCove Nerd Font Mono 12"))
            self.assertEqual(props["misc-cursor-blinks"], ("bool", "false"))
            self.assertEqual(props["scrolling-bar"], ("string", "TERMINAL_SCROLLBAR_NONE"))

    def test_idle_terminal_is_damage_quiet(self):
        with self._terminal() as t:
            time.sleep(1.0)
            proc = subprocess.Popen([xlat.XLAT, "damage", "--window", str(t.window)],
                                    env=platform.helper_env(self.xs.display), stdout=subprocess.PIPE)
            time.sleep(2.0)
            proc.send_signal(signal.SIGTERM)
            out, _ = proc.communicate(timeout=5)
            rects = out.decode().strip().splitlines()[1:]       # first line: {"ready": ...}
            self.assertEqual(rects, [], "idle terminal kept repainting (cursor blink?)")

    def test_terminal_never_touches_host_session(self):
        with mock.patch.dict(os.environ, PLANTED):
            t = self._terminal().start()
        try:
            env = proc_environ(t.pid)
            self.assertNotIn("WAYLAND_DISPLAY", env)
            self.assertNotIn("XDG_SESSION_TYPE", env)
            self.assertEqual(env["DISPLAY"], self.xs.display)
            self.assertEqual(env["XDG_RUNTIME_DIR"], os.path.join(self.tmp, "run"))
            self.assertEqual(env["GDK_BACKEND"], "x11")
            self.assertIn("DBUS_SESSION_BUS_ADDRESS", env)  # the private dbus-run-session bus
            self.assertNotEqual(env["DBUS_SESSION_BUS_ADDRESS"], PLANTED["DBUS_SESSION_BUS_ADDRESS"])
            self.assertNotIn("4242", " ".join(env.values()))
            for v in env.values():
                self.assertNotIn("/run/user/", v)
        finally:
            t.stop()


if __name__ == "__main__":
    unittest.main()
