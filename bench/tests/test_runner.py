import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from tests.xenv import need_tool, pid_alive
from xtrp import platform
from xtrp.model import RunKey, load_records, write_record
from xtrp.runner import PRESETS, expand, run_preset
from xtrp.terminal import descendants

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL11 = 11


def key(**kw):
    base = dict(build="baseline", display_kind="xvfb", wm="none", rtt_ms=None, vnc_encoding=None,
                size="small", font="dejavu", variant="default", workload="shell-echo")
    base.update(kw)
    return RunKey(**base)


class RecordTest(unittest.TestCase):

    def setUp(self):
        self.out = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.out, True)

    def test_record_roundtrip_and_filename(self):
        rec = {"schema": 1, "key": key()._asdict(), "iteration": 2, "metrics": {"startup_ms": 1.0},
               "flags": {"drain_timeout": False, "errors": []}}
        path = write_record(self.out, rec)
        name = os.path.basename(path)
        self.assertRegex(name, r"^[0-9a-f]{40}-2\.json$")
        self.assertEqual(load_records(self.out), [rec])
        rec2 = dict(rec, iteration=3)
        self.assertNotEqual(write_record(self.out, rec2), path)
        self.assertEqual(len(load_records(self.out)), 2)


class PresetTest(unittest.TestCase):

    def test_matrix_sizes(self):
        self.assertEqual(len(expand("smoke", ["baseline"])), 2)
        self.assertEqual(len(expand("quick", ["baseline"])), ALL11 * 3)
        self.assertEqual(len(expand("rtt-sweep", ["baseline"])), 4 * 4 * 5)
        # main block: (xvfb + xvnc*2 enc + x11remote*2 enc) * 4 WMs * 11 * 7, plus the sensitivity
        # block's 4 size/font combos minus the one already in the main block, * 11 * 5
        self.assertEqual(len(expand("full", ["baseline"])), 5 * 4 * ALL11 * 7 + 3 * ALL11 * 5)
        # comparing builds: iteration counts round up to even so A-B / B-A order is balanced
        self.assertEqual(len(expand("quick", ["baseline", "other"])), 2 * ALL11 * 4)
        self.assertEqual(len(expand("quick", ["baseline", "other"], iterations=1)), 2 * ALL11 * 2)
        self.assertEqual(len(expand("quick", ["baseline"], iterations=1)), ALL11)

    def test_keys_follow_the_rules(self):
        for preset in PRESETS:
            runs = expand(preset, ["baseline"])
            keys = set()
            for k, it, _ in runs:
                self.assertEqual(k.rtt_ms is not None, k.display_kind == "xvnc+x11remote", k)
                self.assertEqual(k.vnc_encoding is not None, k.display_kind != "xvfb", k)
                self.assertEqual(k.variant, "default")
                keys.add((k, it))
            self.assertEqual(len(keys), len(runs), preset)       # no duplicate (key, iteration)

    def test_builds_run_back_to_back_and_alternate_order(self):
        runs = expand("quick", ["a", "b"])
        first = [(k.workload, k.build, it) for k, it, _ in runs[:4]]
        self.assertEqual(first, [("shell-echo", "a", 0), ("shell-echo", "b", 0),
                                 ("nvim-type", "a", 0), ("nvim-type", "b", 0)])
        it1 = [(k.workload, k.build) for k, it, _ in runs if it == 1][:2]
        self.assertEqual(it1, [("shell-echo", "b"), ("shell-echo", "a")])

    def test_wm_override_replaces_every_block(self):
        runs = expand("quick", ["baseline"], wms=["marco-comp"])
        self.assertEqual(len(runs), ALL11 * 3)
        self.assertEqual({k.wm for k, _, _ in runs}, {"marco-comp"})

    def test_smoke_shrinks_bulk_bytes(self):
        bulk = [r for r in expand("smoke", ["baseline"]) if r[0].workload == "bulk-ascii"]
        self.assertEqual(bulk[0][2], 5 << 20)


class RunnerTest(unittest.TestCase):

    def setUp(self):
        for tool in ("Xvfb", "dbus-run-session", "xfce4-terminal"):
            need_tool(tool)
        self.out = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.out, True)

    def test_smoke_preset_writes_valid_records(self):
        n = run_preset("smoke", ["baseline"], self.out)
        recs = load_records(self.out)
        self.assertEqual(n, 2)
        self.assertEqual(len(recs), 2)
        echo = [r for r in recs if r["key"]["workload"] == "shell-echo"][0]
        self.assertEqual(len(echo["metrics"]["latency_ms"]), 40)
        self.assertTrue(all(v is not None and 0 < v < 1000 for v in echo["metrics"]["latency_ms"]))
        bulk = [r for r in recs if r["key"]["workload"] == "bulk-ascii"][0]
        self.assertGreater(bulk["metrics"]["throughput_mb_s"], 0)
        self.assertAlmostEqual(bulk["metrics"]["total_s"], bulk["metrics"]["elapsed_s"] + bulk["metrics"]["drain_s"])
        self.assertFalse(bulk["flags"]["errors"])
        for r in recs:
            self.assertEqual(r["schema"], 1)
            self.assertEqual(r["platform"]["tag"], platform.platform_tag())
            self.assertIn("vte", r["platform"]["packages"])
            for m in ("startup_ms", "term_cpu_s", "xserver_cpu_s", "damage_events", "damage_area_px"):
                self.assertIn(m, r["metrics"], (r["key"]["workload"], m))

    def test_remote_kinds_measure_vnc_and_x11_traffic(self):
        need_tool("Xvnc")
        block = {"displays": ["xvnc+x11remote"], "rtts": [2], "vnc_encodings": ["tight"], "wms": ["none"],
                 "sizes": ["small"], "fonts": ["dejavu"], "workloads": ["shell-echo", "bulk-ascii"],
                 "iterations": 1, "n_bytes": 1 << 20}
        self.assertEqual(run_preset([block], ["baseline"], self.out), 2)
        recs = {r["key"]["workload"]: r for r in load_records(self.out)}
        for r in recs.values():
            self.assertEqual(r["flags"]["errors"], [])
            m = r["metrics"]
            self.assertGreater(m["vnc_bytes"], 0)
            self.assertGreater(m["x11_c2s_bytes"], 0)
            self.assertGreater(m["startup_x11_replies"], 0)
            self.assertEqual(r["key"]["rtt_ms"], 2)
        e2e = recs["shell-echo"]["metrics"]["e2e_latency_ms"]
        self.assertEqual(len(e2e), 20)
        self.assertTrue(all(v is not None and v > 0 for v in e2e), e2e)

    def test_broken_build_is_recorded_and_matrix_continues(self):
        builds = os.path.join(self.out, "builds.json")
        with open(builds, "w") as f:
            json.dump({"broken": {"exec": "/nonexistent/xfce4-terminal", "env": {}}}, f)
        n = run_preset("smoke", ["broken"], os.path.join(self.out, "recs"), builds_path=builds)
        recs = load_records(os.path.join(self.out, "recs"))
        self.assertEqual((n, len(recs)), (2, 2))
        self.assertTrue(all(r["flags"]["errors"] for r in recs))

    def test_sigint_mid_matrix_leaves_nothing_running(self):
        locks_before = {f for f in os.listdir("/tmp") if f.startswith(".X") and f.endswith("-lock")}
        env = dict(os.environ, PYTHONPATH=BENCH)
        proc = subprocess.Popen([sys.executable, "-m", "xtrp", "run", "--preset", "smoke", "--build", "baseline",
                                 "--out", self.out], env=env, stderr=subprocess.PIPE, start_new_session=True)
        try:
            deadline = time.monotonic() + 60
            line = b""
            while b"run 1/" not in line and time.monotonic() < deadline:
                line = proc.stderr.readline()
                if not line and proc.poll() is not None:
                    break
            self.assertIn(b"run 1/", line)
            time.sleep(1.5)                                   # mid-run: terminal + latency probe active
            spawned = descendants(proc.pid)
            self.assertTrue(spawned, "runner should have children mid-run")
            os.kill(proc.pid, signal.SIGINT)
            proc.wait(timeout=30)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            proc.stderr.close()
        self.assertEqual(proc.returncode, 130)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and any(pid_alive(p) for p, _ in spawned):
            time.sleep(0.05)
        self.assertEqual([p for p, _ in spawned if pid_alive(p)], [])
        locks_after = {f for f in os.listdir("/tmp") if f.startswith(".X") and f.endswith("-lock")}
        self.assertEqual(locks_after - locks_before, set())


if __name__ == "__main__":
    unittest.main()
