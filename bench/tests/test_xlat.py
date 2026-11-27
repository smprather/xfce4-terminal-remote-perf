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

    def test_require_focus_refuses_and_injects_nothing(self):
        win = self.start_testwin(title="tw2", delay_ms=0, rect="10x10")
        other = self.start_testwin(title="other", delay_ms=0, rect="10x10")
        xlat.focus(self.display, other)
        with self.assertRaises(xlat.NotFocusedError):
            xlat.latency(self.display, win, samples=3, require_focus=True)
        self.assertEqual(self.stop_testwin(win)["keys"], 0)

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
        rects = [json.loads(l) for l in out.decode().splitlines()]
        tens = [r for r in rects if (r["w"], r["h"]) == (10, 10)]
        self.assertGreaterEqual(len(tens), 15, rects[:5])
        self.assertTrue(all(isinstance(r["t_ns"], int) for r in rects))

    def test_wait_window_times_out(self):
        with self.assertRaises(xlat.WindowTimeout):
            xlat.wait_window(self.display, "never-mapped", timeout_ms=200)


if __name__ == "__main__":
    unittest.main()
