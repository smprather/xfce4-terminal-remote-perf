import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from xtrp.model import write_record
from xtrp.report import METRIC_DIRECTION, PlatformMismatch, compare, render_markdown

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rec(build, metrics, workload="shell-echo", tag="el8", iteration=0, errors=(), **key):
    k = dict(build=build, display_kind="xvnc", wm="mutter", rtt_ms=None, vnc_encoding="tight",
             size="large", font="caskaydia", variant="default", workload=workload)
    k.update(key)
    return {"schema": 1, "key": k, "iteration": iteration, "platform": {"tag": tag, "packages": {}},
            "host": {"xlat_info": None}, "metrics": metrics,
            "flags": {"drain_timeout": False, "errors": list(errors)}}


def row(rows, metric, workload="shell-echo"):
    hits = [r for r in rows if r["metric"] == metric and r["key"]["workload"] == workload]
    assert len(hits) == 1, (metric, workload, hits)
    return hits[0]


class CompareTest(unittest.TestCase):

    def test_latency_10_to_12_is_a_regression_at_zero_noise(self):
        r = row(compare([rec("b", {"latency_ms": [10.0] * 40})], [rec("c", {"latency_ms": [12.0] * 40})]),
                "latency_ms")
        self.assertAlmostEqual(r["delta_pct"], -20.0)
        self.assertEqual(r["noise_pct"], 0.0)
        self.assertTrue(r["regression"])
        self.assertEqual(r["base"]["median"], 10.0)

    def test_latency_10_to_10_4_is_not(self):
        r = row(compare([rec("b", {"latency_ms": [10.0] * 40})], [rec("c", {"latency_ms": [10.4] * 40})]),
                "latency_ms")
        self.assertAlmostEqual(r["delta_pct"], -4.0)
        self.assertFalse(r["regression"])

    def test_throughput_100_to_90_is_a_regression(self):
        r = row(compare([rec("b", {"throughput_mb_s": 100.0}, workload="bulk-ascii")],
                        [rec("c", {"throughput_mb_s": 90.0}, workload="bulk-ascii")]),
                "throughput_mb_s", workload="bulk-ascii")
        self.assertAlmostEqual(r["delta_pct"], -10.0)
        self.assertTrue(r["regression"])

    def test_improvement_has_positive_delta(self):
        r = row(compare([rec("b", {"latency_ms": [10.0]})], [rec("c", {"latency_ms": [8.0]})]), "latency_ms")
        self.assertAlmostEqual(r["delta_pct"], 20.0)
        self.assertFalse(r["regression"])

    def test_noise_30_percent_suppresses_a_minus_20_delta(self):
        # run-to-run spread: per-run medians 8.0 .. 12.0 -> median 10, p10 8.4, p90 11.6 -> noise 32%
        base = [rec("b", {"latency_ms": [8.0 + 0.4 * i] * 5}, iteration=i) for i in range(11)]
        cand = [rec("c", {"latency_ms": [12.0] * 5}, iteration=i) for i in range(11)]
        r = row(compare(base, cand), "latency_ms")
        self.assertAlmostEqual(r["noise_pct"], 32.0)
        self.assertAlmostEqual(r["delta_pct"], -20.0)
        self.assertFalse(r["regression"])

    def test_latency_noise_band_is_run_to_run_not_keystroke_jitter(self):
        # A fast terminal: every run's samples spread 0.4-1.8 ms around a stable ~1 ms median.
        jitter = [0.4, 0.6, 0.8, 0.9, 1.0, 1.0, 1.1, 1.2, 1.4, 1.8]
        base = [rec("b", {"latency_ms": jitter}, iteration=i) for i in range(4)]
        cand = [rec("c", {"latency_ms": [v * 1.5 for v in jitter]}, iteration=i) for i in range(4)]
        r = row(compare(base, cand), "latency_ms")
        self.assertEqual(r["base"]["n"], 4)                  # one median per run
        self.assertAlmostEqual(r["noise_pct"], 0.0)
        self.assertAlmostEqual(r["delta_pct"], -50.0)
        self.assertTrue(r["regression"])

    def test_scalar_metrics_summarize_across_iterations(self):
        base = [rec("b", {"total_s": v}, iteration=i) for i, v in enumerate((100.0, 110.0, 120.0))]
        cand = [rec("c", {"total_s": 150.0}, iteration=i) for i in range(3)]
        r = row(compare(base, cand), "total_s")
        self.assertEqual((r["base"]["n"], r["base"]["median"]), (3, 110.0))
        self.assertTrue(r["regression"])

    def test_gated_metric_missing_in_cand_is_a_regression(self):
        rows = compare([rec("b", {"latency_ms": [10.0]}), rec("b", {"startup_ms": 50.0}, workload="nvim-type")],
                       [rec("c", {"latency_ms": [99.0]}, workload="tmux-type")])
        notes = {(r["key"]["workload"], r.get("note"), r["regression"]) for r in rows}
        self.assertIn(("shell-echo", "missing in cand", True), notes)       # gated: the candidate lost it
        self.assertIn(("nvim-type", "missing in cand", False), notes)       # informational
        self.assertIn(("tmux-type", "missing in base", False), notes)       # new in the candidate
        self.assertFalse(any(r["regression"] for r in compare(
            [rec("b", {"latency_ms": [10.0]})], [rec("c", {"latency_ms": [99.0]}, tag="host")],
            cross_platform=True)))

    def test_errored_records_stay_out_of_the_medians(self):
        base = [rec("b", {"latency_ms": [10.0]})]
        cand = [rec("c", {"latency_ms": [10.0]}), rec("c", {"latency_ms": [50.0]}, iteration=1, errors=["boom"])]
        r = row(compare(base, cand), "latency_ms")
        self.assertEqual((r["cand"]["n"], r["cand"]["median"]), (1, 10.0))

    def test_more_failed_runs_or_drain_timeouts_in_cand_is_a_regression(self):
        base = [rec("b", {"latency_ms": [10.0]}, iteration=i) for i in range(2)]
        cand = [rec("c", {"latency_ms": [10.0]}), rec("c", {}, iteration=1, errors=["terminal died"])]
        r = row(compare(base, cand), "failed_runs")
        self.assertEqual((r["base"]["median"], r["cand"]["median"]), (0, 1))
        self.assertTrue(r["regression"])
        slow = dict(rec("c", {"latency_ms": [10.0]}, iteration=1), flags={"drain_timeout": True, "errors": []})
        r = row(compare(base, [rec("c", {"latency_ms": [10.0]}), slow]), "drain_timeouts")
        self.assertTrue(r["regression"])
        self.assertEqual([x for x in compare(base, base) if x["metric"] in ("failed_runs", "drain_timeouts")], [])

    def test_copyrect_area_is_informational_and_frames_higher_is_better(self):
        self.assertEqual(METRIC_DIRECTION["vnc_copyrect_area"], 0)
        self.assertEqual(METRIC_DIRECTION["frames"], 1)
        rows = compare([rec("b", {"vnc_copyrect_area": 1000, "frames": 300})],
                       [rec("c", {"vnc_copyrect_area": 0, "frames": 200})])
        self.assertFalse(row(rows, "vnc_copyrect_area")["regression"])
        self.assertTrue(row(rows, "frames")["regression"])

    def test_components_and_structure_counters_are_informational(self):
        # gated: outcomes; informational: their parts (drain/elapsed) and encoder/frame structure counts
        for m in ("drain_s", "elapsed_s", "vnc_rects", "vnc_updates", "damage_events", "startup_ms"):
            self.assertEqual(METRIC_DIRECTION[m], 0, m)
        for m in ("total_s", "latency_ms", "vnc_bytes", "damage_area_px", "term_cpu_s"):
            self.assertEqual(METRIC_DIRECTION[m], -1, m)

    def test_damage_area_gated_for_latency_but_not_throughput(self):
        # bulk output: area = frames x window, so one frame of phase is ~6%; per keystroke it is an outcome
        rows = compare([rec("b", {"damage_area_px": 3.2e7}, workload="box-drawing"),
                        rec("b", {"damage_area_px": 25000}, workload="shell-echo")],
                       [rec("c", {"damage_area_px": 3.4e7}, workload="box-drawing"),
                        rec("c", {"damage_area_px": 50000}, workload="shell-echo")])
        self.assertFalse(row(rows, "damage_area_px", workload="box-drawing")["regression"])
        self.assertTrue(row(rows, "damage_area_px", workload="shell-echo")["regression"])

    def test_more_multi_paint_keystrokes_in_cand_is_flagged(self):
        base = [rec("b", {"latency_ms": [10.0], "latency_multi_paint": 0}, iteration=i) for i in range(4)]
        cand = [rec("c", {"latency_ms": [10.0], "latency_multi_paint": 9}, iteration=i) for i in range(4)]
        self.assertTrue(row(compare(base, cand), "latency_multi_paint")["regression"])

    def test_unknown_metric_is_informational(self):
        r = row(compare([rec("b", {"made_up": 1.0})], [rec("c", {"made_up": 100.0})]), "made_up")
        self.assertFalse(r["regression"])

    def test_zero_base_median_does_not_divide_by_zero(self):
        r = row(compare([rec("b", {"xserver_cpu_s": 0.0})], [rec("c", {"xserver_cpu_s": 0.0})]), "xserver_cpu_s")
        self.assertIsNone(r["delta_pct"])
        self.assertFalse(r["regression"])

    def test_zero_base_flags_a_new_cost_above_the_base_spread(self):
        # e.g. a candidate adding a per-frame XSync over T2: x11_replies 0 -> 6
        base = [rec("b", {"x11_replies": 0}, workload="bulk-ascii", iteration=i) for i in range(4)]
        r = row(compare(base, [rec("c", {"x11_replies": 6}, workload="bulk-ascii")]), "x11_replies", "bulk-ascii")
        self.assertIsNone(r["delta_pct"])
        self.assertEqual(r["note"], "base median 0")
        self.assertTrue(r["regression"])
        spread = [rec("b", {"x11_replies": v}, workload="bulk-ascii", iteration=i) for i, v in enumerate((0, 0, 0, 4))]
        self.assertFalse(row(compare(spread, [rec("c", {"x11_replies": 1}, workload="bulk-ascii")]),
                             "x11_replies", "bulk-ascii")["regression"])        # within the base's p90
        self.assertFalse(row(compare([rec("b", {"frames": 0}, workload="fullscreen-redraw")],
                                     [rec("c", {"frames": 5}, workload="fullscreen-redraw")]),
                             "frames", "fullscreen-redraw")["regression"])      # higher is better

    def test_platform_mismatch(self):
        with self.assertRaises(PlatformMismatch):
            compare([rec("b", {"latency_ms": [10.0]})], [rec("c", {"latency_ms": [20.0]}, tag="host")])
        rows = compare([rec("b", {"latency_ms": [10.0]})], [rec("c", {"latency_ms": [20.0]}, tag="host")],
                       cross_platform=True)
        self.assertTrue(rows)
        self.assertFalse(any(r["regression"] for r in rows))


class MarkdownTest(unittest.TestCase):

    def test_markdown_puts_regressions_first(self):
        rows = compare([rec("b", {"latency_ms": [10.0], "total_s": 100.0}),
                        rec("b", {"latency_ms": [10.0]}, wm="marco-comp")],
                       [rec("c", {"latency_ms": [12.0], "total_s": 100.0}),
                        rec("c", {"latency_ms": [10.0]}, wm="marco-comp")])
        md = render_markdown(rows)
        self.assertIn("Regressions", md)
        self.assertLess(md.index("Regressions"), md.index("| workload"))
        summary = md[:md.index("| workload")]
        self.assertIn("shell-echo", summary)
        self.assertIn("latency_ms", summary)
        self.assertEqual(md.count("| workload"), 2)            # one table per (display_kind, wm, rtt_ms)

    def test_markdown_says_none_when_clean(self):
        md = render_markdown(compare([rec("b", {"latency_ms": [10.0]})], [rec("c", {"latency_ms": [10.0]})]))
        self.assertIn("No regressions", md)

    def test_cross_platform_banner(self):
        rows = compare([rec("b", {"latency_ms": [10.0]})], [rec("c", {"latency_ms": [20.0]}, tag="host")],
                       cross_platform=True)
        self.assertIn("informational", render_markdown(rows, cross_platform=True))


class CliTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, name, recs):
        d = os.path.join(self.tmp, name)
        for r in recs:
            write_record(d, r)
        return d

    def run_cli(self, *args, **env):
        r = subprocess.run([sys.executable, "-m", "xtrp", "report"] + list(args),
                           env=dict(os.environ, PYTHONPATH=BENCH, **env), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=60)
        r.stdout, r.stderr = r.stdout.decode("utf-8"), r.stderr.decode("utf-8")
        return r

    def test_build_filters_compare_interleaved_runs_from_one_directory(self):
        d = self.write("mixed", [rec("baseline", {"latency_ms": [10.0]}), rec("cand", {"latency_ms": [13.0]})])
        r = self.run_cli(d, d, "--base-build", "baseline", "--cand-build", "cand")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("base: 1 records", r.stdout)
        r = self.run_cli(d, d, "--base-build", "baseline", "--cand-build", "nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no records for build nope", r.stderr)

    def test_refuses_empty_or_missing_inputs(self):
        base = self.write("base", [rec("b", {"latency_ms": [10.0]})])
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        for args in ((base, empty), (empty, base), (base, os.path.join(self.tmp, "typo"))):
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 2, (args, r.stdout, r.stderr))
            self.assertIn("no records", r.stderr)

    def test_refuses_mixed_builds_without_filters(self):
        d = self.write("mixed", [rec("baseline", {"latency_ms": [10.0]}), rec("cand", {"latency_ms": [13.0]})])
        r = self.run_cli(d, d)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("--base-build", r.stderr)

    def test_markdown_prints_under_the_c_locale(self):
        base = self.write("b", [rec("b", {"latency_ms": [10.0]})])
        r = self.run_cli(base, base, LANG="C", LC_ALL="C", PYTHONIOENCODING="")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Δ%", r.stdout)

    def test_exit_codes(self):
        base = self.write("base", [rec("b", {"latency_ms": [10.0]})])
        same = self.write("same", [rec("c", {"latency_ms": [10.1]})])
        worse = self.write("worse", [rec("c", {"latency_ms": [13.0]})])
        host = self.write("host", [rec("c", {"latency_ms": [10.0]}, tag="host")])
        self.assertEqual(self.run_cli(base, same).returncode, 0)
        self.assertEqual(self.run_cli(base, worse).returncode, 1)
        r = self.run_cli(base, host)
        self.assertEqual(r.returncode, 2)
        self.assertIn("refusing to compare el8 with host", r.stderr)
        r = self.run_cli(base, host, "--cross-platform")
        self.assertEqual(r.returncode, 0)
        out = os.path.join(self.tmp, "r.md")
        self.assertEqual(self.run_cli(base, worse, "--out", out).returncode, 1)
        with open(out) as f:
            self.assertIn("Regressions", f.read())


if __name__ == "__main__":
    unittest.main()
