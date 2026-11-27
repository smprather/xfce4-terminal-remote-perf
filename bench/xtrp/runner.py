"""Matrix runner: presets, one measured run per (RunKey, iteration), schema-1 records.

One X server + WM (+ RFB client, + X11 proxy) is set up per group of runs
sharing (display_kind, wm, vnc_encoding, rtt_ms) and reused; every run gets a
fresh terminal. Cleanup is an ExitStack per group and per run, and SIGTERM is
turned into KeyboardInterrupt, so every resource stops on any exit path.
"""

import collections
import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

from xtrp import platform, workloads, xlat
from xtrp.display import WM_NAMES, WindowManager, XServer
from xtrp.metrics import DamageWatch, proc_cpu_s
from xtrp.model import SCHEMA, RunKey, load_builds, write_record
from xtrp.rfb import RfbClient
from xtrp.terminal import SIZES, Terminal
from xtrp.x11proxy import X11Proxy

MIB = 1 << 20
ALL_WORKLOADS = list(workloads.WORKLOADS)
LATENCY_SAMPLES = 40
E2E_SAMPLES = 20
KEY_INTERVAL_MS = 120
KEYSYMS = (0x61, 0xff08)            # a, BackSpace
QUIET_MS = 300
SETTLE_CAP_S = 10.0
DRAIN_CAP_S = 10.0

PRESETS = collections.OrderedDict((
    ("smoke", [dict(displays=["xvfb"], wms=["none"], sizes=["small"], fonts=["dejavu"],
                    workloads=["shell-echo", "bulk-ascii"], iterations=1, n_bytes=5 * MIB)]),
    ("quick", [dict(displays=["xvnc"], vnc_encodings=["tight"], wms=["mutter"], sizes=["large"],
                    fonts=["caskaydia"], workloads=ALL_WORKLOADS, iterations=3)]),
    ("full", [dict(displays=["xvfb", "xvnc", "xvnc+x11remote"], rtts=[0.25], vnc_encodings=["tight", "zrle"],
                   wms=list(WM_NAMES), sizes=["large"], fonts=["caskaydia"], workloads=ALL_WORKLOADS,
                   iterations=7),
              dict(displays=["xvnc"], vnc_encodings=["tight"], wms=["mutter"], sizes=["small", "large"],
                   fonts=["caskaydia", "dejavu"], workloads=ALL_WORKLOADS, iterations=5)]),
    ("rtt-sweep", [dict(displays=["xvnc+x11remote"], vnc_encodings=["tight"], rtts=[0, 0.25, 2, 20],
                        wms=["mutter"], sizes=["large"], fonts=["caskaydia"],
                        workloads=["shell-echo", "nvim-type", "nvim-scroll", "bulk-ascii"], iterations=5)]),
))


def expand(preset, builds, iterations=None):
    """[(RunKey, iteration, n_bytes)] for a preset name or a list of preset blocks.

    A key already produced by an earlier block is not repeated. Within a block,
    runs are ordered iteration-major so builds and workloads interleave over time.
    """
    blocks = PRESETS[preset] if isinstance(preset, str) else preset
    seen, runs = set(), []
    for block in blocks:
        keys = []
        for disp in block["displays"]:
            encodings = [None] if disp == "xvfb" else block.get("vnc_encodings", ["tight"])
            rtts = block.get("rtts", [0.25]) if disp == "xvnc+x11remote" else [None]
            for enc in encodings:
                for rtt in rtts:
                    for wm in block["wms"]:
                        for build in builds:
                            for size in block["sizes"]:
                                for font in block["fonts"]:
                                    for wl in block["workloads"]:
                                        k = RunKey(build, disp, wm, rtt, enc, size, font, "default", wl)
                                        if k not in seen:
                                            seen.add(k)
                                            keys.append(k)
        for it in range(iterations or block["iterations"]):
            runs.extend((k, it, block.get("n_bytes")) for k in keys)
    return runs


def _short_exc(e):
    text = "%s: %s" % (type(e).__name__, e)
    return text if len(text) <= 2000 else text[:2000] + "..."


def _park_pointer(display):
    subprocess.run([platform.tool("xdotool") or "xdotool", "mousemove", "0", "0"],
                   env=platform.helper_env(display), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                   check=True, timeout=10)


def _read_status(path):
    try:
        with open(path) as f:
            return [json.loads(line) for line in f if line.strip().endswith("}")]
    except OSError:
        return []


class _Context(object):
    """Per-preset constants that go into every record."""

    def __init__(self, total):
        self.total = total
        self.done = 0
        self.platform = {"tag": platform.platform_tag(), "packages": platform.packages()}

    def tick(self, key, iteration):
        self.done += 1
        sys.stderr.write("run %d/%d %s %s %s rtt=%s enc=%s %s %s %s it=%d\n" % (
            self.done, self.total, key.build, key.display_kind, key.wm, key.rtt_ms, key.vnc_encoding,
            key.size, key.font, key.workload, iteration))
        sys.stderr.flush()

    def record(self, key, iteration, metrics, flags, xlat_info):
        return {"schema": SCHEMA, "key": dict(key._asdict()), "iteration": iteration,
                "platform": self.platform, "host": {"xlat_info": xlat_info},
                "metrics": metrics, "flags": flags}


def _measure_latency(term, xs, dw, rfb, metrics, flags):
    xlat.focus(xs.display, term.window)
    if not dw.wait_quiet(QUIET_MS, SETTLE_CAP_S):
        flags["drain_timeout"] = True
    cpu0 = proc_cpu_s(term.pid)
    metrics["latency_ms"] = xlat.latency(xs.display, term.window, LATENCY_SAMPLES, KEY_INTERVAL_MS)
    if rfb is not None:
        e2e = []
        for i in range(E2E_SAMPLES):
            t0 = time.monotonic()
            e2e.append(rfb.key_roundtrip_ms(KEYSYMS[i % 2]))
            time.sleep(max(0.0, t0 + KEY_INTERVAL_MS / 1000.0 - time.monotonic()))
        metrics["e2e_latency_ms"] = e2e
    metrics["term_cpu_s"] = proc_cpu_s(term.pid) - cpu0


def _measure_throughput(term, dw, ctx, wl, metrics, flags):
    deadline = time.monotonic() + wl.timeout_s
    start = end = None
    cpu_start = cpu_end = None
    while time.monotonic() < deadline:
        for ev in _read_status(ctx.status_path):
            if ev["event"] == "start" and start is None:
                start, cpu_start = ev, proc_cpu_s(term.pid)
            elif ev["event"] == "end":
                end = ev
        if end is not None:
            cpu_end = proc_cpu_s(term.pid)
            break
        time.sleep(0.02)
    if start is None or end is None:
        raise RuntimeError("%s: no %s event within %d s" % (wl.name, "start" if start is None else "end",
                                                           wl.timeout_s))
    if not dw.wait_quiet(QUIET_MS, DRAIN_CAP_S):
        flags["drain_timeout"] = True
    last = dw.last_event_t
    elapsed = end["t"] - start["t"]
    drain = max(0.0, (last if last is not None else end["t"]) - end["t"])
    metrics["elapsed_s"] = elapsed
    metrics["drain_s"] = drain
    metrics["total_s"] = elapsed + drain
    if end.get("bytes"):
        metrics["throughput_mb_s"] = end["bytes"] / 1e6 / max(elapsed + drain, 1e-9)
    if end.get("frames") is not None:
        metrics["frames"] = end["frames"]
    tc = end.get("term_cpu_s")
    metrics["term_cpu_s"] = tc if tc is not None else (cpu_end - cpu_start)


def run_one(key, iteration, n_bytes, registry, xs, xlat_info, rfb, proxy, rc):
    """One measured run; always returns a record (errors go to flags.errors)."""
    metrics = {}
    flags = {"drain_timeout": False, "errors": []}
    wl = workloads.WORKLOADS[key.workload]
    cols, rows = (int(v) for v in SIZES[key.size].split("x"))
    try:
        with contextlib.ExitStack() as stack:
            workdir = tempfile.mkdtemp(prefix="xtrp-run-")
            stack.callback(shutil.rmtree, workdir, True)
            ctx = workloads.WorkloadCtx(os.path.join(workdir, "status.jsonl"), workdir,
                                        sync=(key.variant == "sync"), cols=cols, rows=rows, n_bytes=n_bytes)
            stack.callback(workloads.cleanup, ctx)
            build = registry[key.build]
            _park_pointer(xs.display)
            if rfb is not None:
                rfb.reset_stats()
            x11_0 = proxy.stats() if proxy is not None else None
            xcpu0 = proc_cpu_s(xs.pid)
            term = Terminal(build, proxy.display if proxy is not None else xs.display, key.size, key.font,
                            wl.command(ctx), workdir, xlat_display=xs.display)
            term.start()
            stack.callback(term.stop)
            metrics["startup_ms"] = term.startup_ms
            if proxy is not None:
                metrics["startup_x11_replies"] = proxy.stats()["replies"] - x11_0["replies"]
            dw = DamageWatch(xs.display, term.window).start()
            stack.callback(dw.stop)
            if wl.kind == "latency":
                _measure_latency(term, xs, dw, rfb, metrics, flags)
            else:
                _measure_throughput(term, dw, ctx, wl, metrics, flags)
            dmg = dw.stop()
            metrics["damage_events"] = dmg["events"]
            metrics["damage_area_px"] = dmg["area_px"]
            metrics["xserver_cpu_s"] = proc_cpu_s(xs.pid) - xcpu0
            if rfb is not None:
                st = rfb.stats()
                metrics.update(vnc_bytes=st["bytes"], vnc_updates=st["updates"],
                               vnc_rects=sum(st["rects"].values()), vnc_copyrect_area=st["copyrect_area"])
            if proxy is not None:
                x11_1 = proxy.stats()
                for m in ("c2s_bytes", "s2c_bytes", "replies", "image_bytes"):
                    metrics["x11_" + m] = x11_1[m] - x11_0[m]
                metrics["x11_requests"] = sum(x11_1["requests"].values()) - sum(x11_0["requests"].values())
    except Exception as e:  # noqa: BLE001 - one broken run must not stop the matrix
        flags["errors"].append(_short_exc(e))
    return rc.record(key, iteration, metrics, flags, xlat_info)


def _run_group(gkey, runs, registry, out_dir, rc):
    display_kind, wm, encoding, rtt = gkey
    written = 0
    with contextlib.ExitStack() as stack:
        try:
            xs = stack.enter_context(XServer("xvfb" if display_kind == "xvfb" else "xvnc"))
            stack.enter_context(WindowManager(wm, xs.display))
            _park_pointer(xs.display)
            info = xlat.info(xs.display)
            rfb = proxy = None
            if display_kind != "xvfb":
                rfb = RfbClient("127.0.0.1", xs.rfb_port, [encoding, "copyrect"])
                stack.callback(rfb.close)
                rfb.connect()
                rfb.start()
            if display_kind == "xvnc+x11remote":
                proxy = stack.enter_context(X11Proxy(xs.display, rtt_ms=rtt))
        except Exception as e:  # noqa: BLE001 - recorded on every run of the group
            err = "group setup failed (%s/%s): %s" % (display_kind, wm, _short_exc(e))
            for key, it, _ in runs:
                rc.tick(key, it)
                write_record(out_dir, rc.record(key, it, {}, {"drain_timeout": False, "errors": [err]}, None))
                written += 1
            return written
        for key, it, n_bytes in runs:
            rc.tick(key, it)
            write_record(out_dir, run_one(key, it, n_bytes, registry, xs, info, rfb, proxy, rc))
            written += 1
    return written


def _interrupt(signum, frame):
    raise KeyboardInterrupt("signal %d" % signum)


def run_preset(preset, builds, out_dir, iterations=None, builds_path=None):
    """Run every (key, iteration) of `preset` (a name or a list of blocks); return records written."""
    registry = load_builds(builds_path)
    runs = expand(preset, builds, iterations)
    if platform.platform_tag() == "host":
        missing = sorted({k.wm for k, _, _ in runs if not WindowManager.available(k.wm)})
        for wm in missing:
            sys.stderr.write("skipped wm %s: not installed\n" % wm)
        runs = [r for r in runs if r[0].wm not in missing]
    groups = collections.OrderedDict()
    for run in runs:
        k = run[0]
        groups.setdefault((k.display_kind, k.wm, k.vnc_encoding, k.rtt_ms), []).append(run)
    rc = _Context(len(runs))
    main = threading.current_thread() is threading.main_thread()
    previous = signal.signal(signal.SIGTERM, _interrupt) if main else None
    written = 0
    try:
        for gkey, gruns in groups.items():
            written += _run_group(gkey, gruns, registry, out_dir, rc)
    finally:
        if main:
            signal.signal(signal.SIGTERM, previous)
    return written
