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
        base = [8.0 + 0.4 * i for i in range(11)]          # median 10, p10 8.4, p90 11.6 -> noise 32%
        r = row(compare([rec("b", {"latency_ms": base})], [rec("c", {"latency_ms": [12.0] * 11})]), "latency_ms")
        self.assertAlmostEqual(r["noise_pct"], 32.0)
        self.assertAlmostEqual(r["delta_pct"], -20.0)
        self.assertFalse(r["regression"])

    def test_scalar_metrics_summarize_across_iterations(self):
        base = [rec("b", {"startup_ms": v}, iteration=i) for i, v in enumerate((100.0, 110.0, 120.0))]
        cand = [rec("c", {"startup_ms": 150.0}, iteration=i) for i in range(3)]
        r = row(compare(base, cand), "startup_ms")
        self.assertEqual((r["base"]["n"], r["base"]["median"]), (3, 110.0))
        self.assertTrue(r["regression"])

    def test_missing_key_gets_a_note_and_no_flag(self):
        rows = compare([rec("b", {"latency_ms": [10.0]}), rec("b", {"startup_ms": 50.0}, workload="nvim-type")],
                       [rec("c", {"latency_ms": [99.0]}, workload="tmux-type")])
        notes = {(r["key"]["workload"], r.get("note")) for r in rows}
        self.assertIn(("shell-echo", "missing in cand"), notes)
        self.assertIn(("nvim-type", "missing in cand"), notes)
        self.assertIn(("tmux-type", "missing in base"), notes)
        self.assertFalse(any(r["regression"] for r in rows))

    def test_copyrect_area_is_informational_and_frames_higher_is_better(self):
        self.assertEqual(METRIC_DIRECTION["vnc_copyrect_area"], 0)
        self.assertEqual(METRIC_DIRECTION["frames"], 1)
        rows = compare([rec("b", {"vnc_copyrect_area": 1000, "frames": 300})],
                       [rec("c", {"vnc_copyrect_area": 0, "frames": 200})])
        self.assertFalse(row(rows, "vnc_copyrect_area")["regression"])
        self.assertTrue(row(rows, "frames")["regression"])

    def test_components_and_structure_counters_are_informational(self):
        # gated: outcomes; informational: their parts (drain/elapsed) and encoder/frame structure counts
        for m in ("drain_s", "elapsed_s", "vnc_rects", "vnc_updates", "damage_events"):
            self.assertEqual(METRIC_DIRECTION[m], 0, m)
        for m in ("total_s", "latency_ms", "vnc_bytes", "damage_area_px", "term_cpu_s"):
            self.assertEqual(METRIC_DIRECTION[m], -1, m)

    def test_unknown_metric_is_informational(self):
        r = row(compare([rec("b", {"made_up": 1.0})], [rec("c", {"made_up": 100.0})]), "made_up")
        self.assertFalse(r["regression"])

    def test_zero_base_median_does_not_divide_by_zero(self):
        r = row(compare([rec("b", {"xserver_cpu_s": 0.0})], [rec("c", {"xserver_cpu_s": 0.5})]), "xserver_cpu_s")
        self.assertIsNone(r["delta_pct"])
        self.assertFalse(r["regression"])

    def test_platform_mismatch(self):
        with self.assertRaises(PlatformMismatch):
            compare([rec("b", {"latency_ms": [10.0]})], [rec("c", {"latency_ms": [20.0]}, tag="host")])
        rows = compare([rec("b", {"latency_ms": [10.0]})], [rec("c", {"latency_ms": [20.0]}, tag="host")],
                       cross_platform=True)
        self.assertTrue(rows)
        self.assertFalse(any(r["regression"] for r in rows))


class MarkdownTest(unittest.TestCase):

    def test_markdown_puts_regressions_first(self):
        rows = compare([rec("b", {"latency_ms": [10.0], "startup_ms": 100.0}),
                        rec("b", {"latency_ms": [10.0]}, wm="marco-comp")],
                       [rec("c", {"latency_ms": [12.0], "startup_ms": 100.0}),
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
