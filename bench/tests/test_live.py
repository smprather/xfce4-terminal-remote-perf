import unittest
from unittest import mock

from tests.xenv import XvfbFixture, group_members, need_tool, wait_gone
from xtrp import display, platform, xlat
from xtrp.live import live_latency, live_startup, live_watch


class LiveTest(XvfbFixture):

    def test_live_refuses_unfocused_window(self):
        target = self.start_testwin(title="target", delay_ms=0, rect="10x10")
        other = self.start_testwin(title="elsewhere", delay_ms=0, rect="10x10")
        xlat.focus(self.display, other)
        with self.assertRaises(xlat.NotFocusedError):
            live_latency(self.display, window=target, samples=6)
        self.assertEqual(self.stop_testwin(target)["keys"], 0)
        self.assertEqual(self.stop_testwin(other)["keys"], 0)

    def test_live_latency_on_focused_window_leaves_no_net_input(self):
        target = self.start_testwin(title="target", delay_ms=5, rect="10x10")
        xlat.focus(self.display, target)
        res = live_latency(self.display, window=target, samples=7)    # odd: rounded up to stay balanced
        self.assertEqual(res["latency_ms"]["n"], 8)
        self.assertEqual(len(res["raw"]), 8)
        self.assertEqual(self.stop_testwin(target)["keys"], 8)       # 4 x 'a' + 4 x BackSpace

    def test_live_latency_reports_keys_that_painted_twice(self):
        # On a real desktop a blinking cursor can repaint before the echo; the result must say so.
        once = self.start_testwin(title="once", delay_ms=5, rect="10x10")
        xlat.focus(self.display, once)
        self.assertEqual(live_latency(self.display, window=once, samples=4)["multi_paint"], 0)
        twice = self.start_testwin(title="twice", delay_ms=5, rect="10x10", second_paint_ms=30)
        xlat.focus(self.display, twice)
        self.assertEqual(live_latency(self.display, window=twice, samples=4)["multi_paint"], 4)

    def test_live_startup_times_new_windows_and_leaves_nothing(self):
        # The spec's live startup: launch a terminal on the real display, time its first mapped
        # window, close it again.
        for tool in ("dbus-run-session", "xfce4-terminal"):
            need_tool(tool)
        spawned = []
        real = display.spawn

        def spy(*args, **kw):
            proc = real(*args, **kw)
            spawned.append(proc)
            return proc
        env = platform.child_env(self.display, self.tmp)          # tests never use the host session
        with mock.patch.object(display, "spawn", spy):
            res = live_startup(self.display, samples=2, env=env,
                               launcher=["dbus-run-session", "--", "xfce4-terminal"])
        self.assertEqual(len(res["raw"]), 2)
        self.assertTrue(all(0 < v < 30000 for v in res["raw"]), res)
        self.assertEqual(res["startup_ms"]["n"], 2)
        self.assertEqual(len(spawned), 2)
        for proc in spawned:
            self.assertEqual(wait_gone(lambda: group_members(proc.pid)), [])

    def test_live_watch_counts_damage_and_server_cpu(self):
        win = self.start_testwin(title="busy", delay_ms=0, rect="10x10", damage_forever=True)
        res = live_watch(self.display, win, 0.5)
        self.assertGreater(res["damage_events"], 3)
        self.assertEqual(res["damage_area_px"], 100 * res["damage_events"])
        self.assertIsNotNone(res["xserver_cpu_s"])                   # our Xvfb is visible locally


if __name__ == "__main__":
    unittest.main()
