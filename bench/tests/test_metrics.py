import os
import time
import unittest

from tests.xenv import XvfbFixture
from xtrp.metrics import DamageWatch, proc_cpu_s, summarize


class SummarizeTest(unittest.TestCase):

    def test_summarize(self):
        self.assertEqual(summarize([3, 1, 2, None]), {"n": 3, "median": 2, "p10": 1.2, "p90": 2.8})

    def test_summarize_empty_and_single(self):
        self.assertEqual(summarize([None]), {"n": 0, "median": None, "p10": None, "p90": None})
        self.assertEqual(summarize([5.0]), {"n": 1, "median": 5.0, "p10": 5.0, "p90": 5.0})

    def test_summarize_even_count_median(self):
        self.assertEqual(summarize([1, 2, 3, 4])["median"], 2.5)

    def test_proc_cpu_s_counts_own_cpu(self):
        before = proc_cpu_s(os.getpid())
        t0 = time.monotonic()
        while time.monotonic() - t0 < 0.3:
            pass
        self.assertGreater(proc_cpu_s(os.getpid()) - before, 0.1)


class DamageWatchTest(XvfbFixture):

    def test_drain_timeout_is_flagged_not_hung(self):
        win = self.start_testwin(title="busy", delay_ms=0, rect="10x10", damage_forever=True)
        dw = DamageWatch(self.display, win).start()
        try:
            t0 = time.monotonic()
            self.assertFalse(dw.wait_quiet(quiet_ms=300, cap_s=1.0))
            self.assertLess(time.monotonic() - t0, 2.0)
        finally:
            st = dw.stop()
        self.assertGreater(st["events"], 5)
        self.assertEqual(st["area_px"], 100 * st["events"])

    def test_idle_window_goes_quiet(self):
        win = self.start_testwin(title="calm", delay_ms=0, rect="10x10")
        dw = DamageWatch(self.display, win).start()
        try:
            t0 = time.monotonic()
            self.assertTrue(dw.wait_quiet(quiet_ms=300, cap_s=5.0))
            self.assertGreaterEqual(time.monotonic() - t0, 0.3)
            self.assertIsNone(dw.last_event_t)
        finally:
            self.assertEqual(dw.stop(), {"events": 0, "area_px": 0})


if __name__ == "__main__":
    unittest.main()
