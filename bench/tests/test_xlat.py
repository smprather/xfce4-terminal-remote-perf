import json
import signal
import subprocess
import time
import unittest

from tests.xenv import XvfbFixture
from xtrp import platform, xlat


class XlatTest(XvfbFixture):

    def test_latency_matches_testwin_delay(self):
        win = self.start_testwin(title="tw", delay_ms=30, rect="50x20")
        xlat.focus(self.display, win)
        ms = xlat.latency(self.display, win, samples=10)
        self.assertEqual(len(ms), 10)
        self.assertTrue(all(v is not None and 30.0 <= v <= 60.0 for v in ms), ms)

    def test_a_separate_later_paint_is_counted(self):
        # The first damage is only the echo when a key paints once; a second, later paint means it
        # may not be (e.g. a cursor repaint before the echo), and the sample says so.
        once = self.start_testwin(title="once", delay_ms=5, rect="20x20")
        xlat.focus(self.display, once)
        s1 = xlat.latency(self.display, once, samples=6, detail=True)
        self.assertEqual([s["paints"] for s in s1], [1] * 6, s1)
        twice = self.start_testwin(title="twice", delay_ms=5, rect="20x20", second_paint_ms=30)
        xlat.focus(self.display, twice)
        s2 = xlat.latency(self.display, twice, samples=6, detail=True)
        self.assertEqual([s["paints"] for s in s2], [2] * 6, s2)
        self.assertTrue(all(5.0 <= s["ms"] < 30.0 for s in s2), s2)

    def test_region_ignores_damage_elsewhere(self):
        # testwin --damage-forever paints (200,200) every 50 ms; the key paints (0,0) after 20 ms.
        win = self.start_testwin(title="busy", delay_ms=20, rect="50x20", damage_forever=True)
        xlat.focus(self.display, win)
        anywhere = xlat.latency(self.display, win, samples=12)
        self.assertTrue(any(v < 18.0 for v in anywhere), anywhere)         # the ticker wins sometimes
        region = xlat.latency(self.display, win, samples=12, region=(0, 0, 100, 50))
        self.assertTrue(all(20.0 <= v <= 50.0 for v in region), region)

    def test_verify_pixels_skips_damage_that_changes_nothing(self):
        # testwin --noop-first repaints the rect in its current colour at once (damage, no change),
        # then really changes it 25 ms later: only the pixel check sees the real echo.
        win = self.start_testwin(title="noop", delay_ms=25, rect="40x20", noop_first=True)
        xlat.focus(self.display, win)
        first = xlat.latency(self.display, win, samples=6, region=(0, 0, 40, 20))
        self.assertTrue(all(v < 10.0 for v in first), first)
        real = xlat.latency(self.display, win, samples=6, region=(0, 0, 40, 20), verify_pixels=True)
        self.assertTrue(all(25.0 <= v <= 55.0 for v in real), real)

    def test_require_focus_refuses_and_injects_nothing(self):
        win = self.start_testwin(title="tw2", delay_ms=0, rect="10x10")
        other = self.start_testwin(title="other", delay_ms=0, rect="10x10")
        xlat.focus(self.display, other)
        with self.assertRaises(xlat.NotFocusedError):
            xlat.latency(self.display, win, samples=3, require_focus=True)
        self.assertEqual(self.stop_testwin(win)["keys"], 0)

    def test_geometry_and_fill_screen(self):
        win = self.start_testwin(title="geo", delay_ms=0, rect="10x10")
        g = xlat.geometry(self.display, win)
        self.assertEqual((g["x"], g["y"], g["width"], g["height"]), (0, 0, 400, 300))
        root = (g["root_width"], g["root_height"])
        self.assertGreater(root, (400, 300))
        xlat.fill_screen(self.display, win)
        g = xlat.geometry(self.display, win)
        self.assertEqual((g["x"], g["y"], g["width"], g["height"]), (0, 0) + root)

    def test_info_reports_no_wm_on_bare_xvfb(self):
        i = xlat.info(self.display)
        self.assertIsNone(i["wm_name"])
        self.assertFalse(i["cm_owner"])
        self.assertFalse(i["frame_drawn"])
        self.assertIn("DAMAGE", i["extensions"])
        self.assertGreater(i["rtt_us_median"], 0)
        self.assertEqual((i["width"], i["height"], i["depth"]), (1024, 768, 24))

    def test_damage_reports_rect_area(self):
        win = self.start_testwin(title="tw3", delay_ms=0, rect="10x10", damage_forever=True)
        proc = subprocess.Popen([xlat.XLAT, "damage", "--window", str(win)],
                                env=platform.helper_env(self.display), stdout=subprocess.PIPE)
        time.sleep(1.0)
        proc.send_signal(signal.SIGTERM)
        out, _ = proc.communicate(timeout=5)
        self.assertEqual(proc.returncode, 0)
        lines = [json.loads(l) for l in out.decode().splitlines()]
        self.assertTrue(lines[0]["ready"])
        rects = lines[1:]
        tens = [r for r in rects if (r["w"], r["h"]) == (10, 10)]
        self.assertGreaterEqual(len(tens), 15, rects[:5])
        self.assertTrue(all(isinstance(r["t_ns"], int) for r in rects))

    def test_damage_on_idle_window_reports_nothing(self):
        # DamageCreate on a window reports its whole visible area once; that is not drawing.
        win = self.start_testwin(title="idle", delay_ms=0, rect="10x10")
        proc = subprocess.Popen([xlat.XLAT, "damage", "--window", str(win)],
                                env=platform.helper_env(self.display), stdout=subprocess.PIPE)
        time.sleep(0.5)
        proc.send_signal(signal.SIGTERM)
        out, _ = proc.communicate(timeout=5)
        lines = [json.loads(l) for l in out.decode().splitlines()]
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0]["ready"])        # armed, then nothing: creation report dropped
        self.assertIsInstance(lines[0]["t_ns"], int)

    def test_wait_window_times_out(self):
        with self.assertRaises(xlat.WindowTimeout):
            xlat.wait_window(self.display, "never-mapped", timeout_ms=200)


if __name__ == "__main__":
    unittest.main()
