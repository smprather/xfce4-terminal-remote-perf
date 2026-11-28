import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

from tests.xenv import need_tool, pid_alive
from xtrp.display import XServer
from xtrp.model import load_builds
from xtrp.terminal import Terminal, descendants
from xtrp.workloads import (CHUNK, WORKLOADS, WorkloadCtx, gen_box, gen_bulk_ascii, gen_compile_log,
                            cleanup, gen_sgr, gen_source_file, gen_unicode, tmux_argv)

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELEVEN = ["shell-echo", "nvim-type", "tmux-type", "bulk-ascii", "sgr-color", "unicode", "box-drawing",
          "compile-log", "fullscreen-redraw", "nvim-scroll", "tmux-bulk-split"]


def read_status(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


class GeneratorTest(unittest.TestCase):

    def test_generators_are_deterministic_and_exact_size(self):
        for gen in (gen_bulk_ascii, gen_sgr, gen_unicode, gen_box):
            with self.subTest(gen=gen.__name__):
                a = b"".join(gen(1 << 20, seed=7))
                b = b"".join(gen(1 << 20, seed=7))
                self.assertEqual(a, b)
                self.assertEqual(len(a), 1 << 20)
                a.decode("utf-8")  # never splits a code point at the size boundary
                self.assertNotEqual(a, b"".join(gen(1 << 20, seed=8)))

    def test_odd_sizes_are_exact_and_valid_utf8(self):
        for gen in (gen_unicode, gen_box, gen_sgr):
            for n in (1, 2, 3, 4, 5, 1000, 65537):
                data = b"".join(gen(n, seed=3))
                self.assertEqual(len(data), n, (gen.__name__, n))
                data.decode("utf-8")

    def test_chunks_are_at_most_64k(self):
        for gen in (gen_bulk_ascii, gen_sgr, gen_unicode, gen_box):
            self.assertTrue(all(0 < len(c) <= CHUNK for c in gen(300000, seed=1)), gen.__name__)
        self.assertTrue(all(0 < len(c) <= CHUNK for c in gen_compile_log(5000, seed=1)))

    def test_bulk_ascii_is_printable_ascii_lines(self):
        data = b"".join(gen_bulk_ascii(1 << 18))
        self.assertTrue(all(32 <= c < 127 or c == 10 for c in data))
        lengths = [len(l) for l in data.split(b"\n")[:-1]]
        self.assertTrue(lengths and all(40 <= n <= 200 for n in lengths[:-1]), lengths[:5])

    def test_sgr_uses_256_and_truecolour(self):
        text = b"".join(gen_sgr(1 << 16)).decode()
        self.assertTrue(re.search(r"\x1b\[[0-9;]*38;5;\d+[;m]", text), "256-colour SGR")
        self.assertTrue(re.search(r"\x1b\[[0-9;]*38;2;\d+;\d+;\d+[;m]", text), "truecolour SGR")
        self.assertTrue(re.search(r"\x1b\[0;[134];", text), "bold/italic/underline")

    def test_unicode_mixes_wide_combining_emoji_and_pua(self):
        text = b"".join(gen_unicode(1 << 16)).decode()
        self.assertTrue(any(0x4E00 <= ord(c) <= 0x9FFF for c in text), "CJK")
        self.assertTrue(any(0x0300 <= ord(c) <= 0x036F for c in text), "combining")
        self.assertTrue(any(0x1F300 <= ord(c) <= 0x1FAFF for c in text), "emoji")
        self.assertTrue(any(0xE0A0 <= ord(c) <= 0xE0D4 or 0xF000 <= ord(c) <= 0xF2E0 for c in text), "PUA")

    def test_box_drawing_stays_in_range(self):
        text = b"".join(gen_box(1 << 16)).decode()
        drawn = [c for c in text if ord(c) > 127]
        self.assertTrue(drawn)
        self.assertTrue(all(0x2500 <= ord(c) <= 0x259F for c in drawn))

    def test_compile_log_line_count_and_shape(self):
        lines = b"".join(gen_compile_log(1000, seed=2)).decode().splitlines()
        self.assertEqual(len(lines), 1000)
        plain = [re.sub(r"\x1b\[[0-9;]*[mK]", "", l) for l in lines]
        self.assertTrue(all(re.match(r"^[\w/.-]+:\d+:\d+: (warning|error|note): ", l) for l in plain), plain[:3])
        self.assertTrue(any("\x1b[" in l for l in lines))

    def test_source_file_is_c_like(self):
        src = gen_source_file(n_lines=500, seed=1)
        self.assertEqual(len(src.splitlines()), 500)
        self.assertIn("{", src)
        self.assertIn("return", src)


class WorkloadTableTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def ctx(self, **kw):
        return WorkloadCtx(status_path=os.path.join(self.tmp, "status.jsonl"), workdir=self.tmp, **kw)

    def test_workload_table_is_exactly_the_eleven(self):
        self.assertEqual(sorted(WORKLOADS), sorted(ELEVEN))
        kinds = {n: w.kind for n, w in WORKLOADS.items()}
        self.assertEqual(sorted(n for n, k in kinds.items() if k == "latency"),
                         ["nvim-type", "shell-echo", "tmux-type"])

    def test_every_command_is_an_argv_list(self):
        for name, w in sorted(WORKLOADS.items()):
            argv = w.command(self.ctx())
            self.assertTrue(argv and all(isinstance(a, str) for a in argv), name)
            self.assertGreater(w.timeout_s, 0)

    def test_tmux_workloads_use_a_private_socket_and_tmpdir(self):
        for name in ("tmux-type", "tmux-bulk-split"):
            ctx = self.ctx()
            argv = WORKLOADS[name].command(ctx)
            self.assertIn("-L", argv)
            self.assertTrue(argv[argv.index("-L") + 1].startswith("xtrp-"))
            self.assertIn("TMUX_TMPDIR=%s" % ctx.workdir, argv)

    def test_tmux_argv_refuses_shared_sockets(self):
        self.assertEqual(tmux_argv("xtrp-1-2", "kill-server")[1:], ["-L", "xtrp-1-2", "kill-server"])
        for bad in ("default", "", "scratch"):
            with self.assertRaises(ValueError):
                tmux_argv(bad, "kill-server")

    def test_sync_variant_sets_env(self):
        self.assertIn("XTRP_SYNC=1", WORKLOADS["nvim-type"].command(self.ctx(sync=True)))
        self.assertNotIn("XTRP_SYNC=1", WORKLOADS["nvim-type"].command(self.ctx(sync=False)))

    def test_bytes_override_reaches_the_payload(self):
        argv = WORKLOADS["bulk-ascii"].command(self.ctx(n_bytes=5 << 20))
        self.assertEqual(argv[argv.index("--bytes") + 1], str(5 << 20))


class PayloadTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.status = os.path.join(self.tmp, "status.jsonl")

    def run_payload(self, *args):
        # The payload sleeps forever after its end event; --exit makes it return for tests.
        env = dict(os.environ, PYTHONPATH=BENCH)
        with open(os.devnull, "wb") as null:
            subprocess.run([sys.executable, "-m", "xtrp", "workload"] + list(args)
                           + ["--status", self.status, "--exit"],
                           stdout=null, env=env, check=True, timeout=60)
        return read_status(self.status)

    def test_payload_writes_start_and_end_status(self):
        ev = self.run_payload("bulk-ascii", "--bytes", "65536")
        self.assertEqual([e["event"] for e in ev], ["start", "end"])
        self.assertGreaterEqual(ev[1]["t"], ev[0]["t"])
        self.assertEqual(ev[1]["bytes"], 65536)

    def test_payload_waits_for_the_go_file(self):
        go = os.path.join(self.tmp, "go")
        env = dict(os.environ, PYTHONPATH=BENCH)
        with open(os.devnull, "wb") as null:
            proc = subprocess.Popen([sys.executable, "-m", "xtrp", "workload", "bulk-ascii", "--bytes", "4096",
                                     "--status", self.status, "--go", go, "--exit"], stdout=null, env=env)
            try:
                time.sleep(0.7)
                self.assertFalse(os.path.exists(self.status) and read_status(self.status))
                open(go, "w").close()
                proc.wait(timeout=30)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait()
        self.assertEqual([e["event"] for e in read_status(self.status)], ["start", "end"])

    def test_throughput_commands_carry_the_go_path(self):
        ctx = WorkloadCtx(status_path=self.status, workdir=self.tmp)
        for name, w in sorted(WORKLOADS.items()):
            argv = w.command(ctx)
            if w.kind == "throughput":
                self.assertIn(ctx.go_path, " ".join(argv), name)

    def test_fullscreen_redraw_uses_alt_screen(self):
        ev = self.run_payload("fullscreen-redraw", "--seconds", "0.2", "--cols", "40", "--rows", "10")
        self.assertEqual(ev[1]["event"], "end")
        self.assertGreater(ev[1]["frames"], 3)
        self.assertGreater(ev[1]["bytes"], 3 * 40 * 10)

    def test_fullscreen_redraw_fills_the_real_terminal_size(self):
        # No --cols/--rows: frames must match the pty's size, or every row wraps and the frame scrolls.
        import fcntl
        import pty
        import struct
        import termios
        import tty
        master, slave = pty.openpty()
        try:
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 8, 30, 0, 0))
            tty.setraw(slave)
            env = dict(os.environ, PYTHONPATH=BENCH)
            proc = subprocess.Popen([sys.executable, "-m", "xtrp", "workload", "fullscreen-redraw", "--seconds",
                                     "0.1", "--status", self.status, "--exit"], stdout=slave, env=env)
            out = b""
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                import select
                if select.select([master], [], [], 0.1)[0]:
                    out += os.read(master, 65536)
                elif proc.poll() is not None:
                    break
            proc.wait(timeout=10)
        finally:
            os.close(master)
            os.close(slave)
        first = out.split(b"\x1b[H")[1]
        lines = first.split(b"\r\n")[:8]
        self.assertEqual([len(line) for line in lines], [30] * 8, lines[:2])

    def test_compile_log_payload_counts_bytes(self):
        ev = self.run_payload("compile-log", "--lines", "200")
        self.assertEqual(ev[1]["bytes"], len(b"".join(gen_compile_log(200))))



class WorkloadInTerminalTest(unittest.TestCase):
    """Workloads run for real inside the baseline terminal on Xvfb."""

    def setUp(self):
        for tool in ("Xvfb", "dbus-run-session", "xfce4-terminal"):
            need_tool(tool)
        self.tmp = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.xs = XServer("xvfb").start()
        self.addCleanup(self.xs.stop)

    def run_in_terminal(self, name, timeout_s, **ctx_kw):
        ctx = WorkloadCtx(status_path=os.path.join(self.tmp, "status.jsonl"), workdir=self.tmp, **ctx_kw)
        term = Terminal(load_builds()["baseline"], self.xs.display, "small", "dejavu",
                        WORKLOADS[name].command(ctx), self.tmp).start()
        self.addCleanup(cleanup, ctx)
        self.addCleanup(term.stop)
        time.sleep(0.3)
        open(ctx.go_path, "w").close()          # what the runner does once startup has settled
        deadline = time.monotonic() + timeout_s
        events = []
        while time.monotonic() < deadline:
            if os.path.exists(ctx.status_path):
                events = read_status(ctx.status_path)
                if events and events[-1]["event"] == "end":
                    break
            time.sleep(0.05)
        return ctx, term, events

    def test_bulk_payload_reports_start_and_end_in_the_terminal(self):
        _, _, ev = self.run_in_terminal("bulk-ascii", 60, n_bytes=1 << 20)
        self.assertEqual([e["event"] for e in ev], ["start", "end"])
        self.assertEqual(ev[1]["bytes"], 1 << 20)

    def test_nvim_scroll_reports_start_and_end(self):
        need_tool("nvim")
        _, _, ev = self.run_in_terminal("nvim-scroll", 120)
        self.assertEqual([e["event"] for e in ev], ["start", "end"], ev)
        self.assertGreater(ev[1]["t"], ev[0]["t"])

    def test_tmux_bulk_split_runs_and_cleanup_stops_its_server(self):
        need_tool("tmux")
        ctx, term, ev = self.run_in_terminal("tmux-bulk-split", 120, n_bytes=1 << 20)
        self.assertEqual([e["event"] for e in ev], ["start", "end"], ev)
        sock = os.path.join(ctx.workdir, "tmux-%d" % os.getuid(), ctx.tmux_socket)
        self.assertTrue(os.path.exists(sock))
        servers = [p for p, _ in descendants(1)
                   if os.path.basename(_cmdline(p).split(" ")[0]) == "tmux" and ctx.tmux_socket in _cmdline(p)]
        self.assertTrue(servers, "the private tmux server should be running")
        term.stop()
        cleanup(ctx)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and any(pid_alive(p) for p in servers):
            time.sleep(0.05)
        self.assertFalse(any(pid_alive(p) for p in servers), servers)


def _cmdline(pid):
    try:
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        return ""

if __name__ == "__main__":
    unittest.main()
