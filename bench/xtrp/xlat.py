"""Thin wrappers over the xlat C helper (bench/helpers/xlat.c).

xlat prints one JSON object per line; its times are CLOCK_MONOTONIC
nanoseconds, converted to seconds or milliseconds here.
"""

import json
import os
import subprocess
import threading

from xtrp import platform

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HELPERS = os.path.join(_REPO, "bench", "helpers")
BUILD_SH = os.path.join(_HELPERS, "build.sh")

if os.environ.get("XTRP_XLAT"):
    XLAT = os.environ["XTRP_XLAT"]
    BIN_DIR = os.path.dirname(XLAT)
else:
    BIN_DIR = os.path.join(_HELPERS, "bin", platform.platform_tag())
    XLAT = os.path.join(BIN_DIR, "xlat")

_PROGRAMS = ("xlat", "testwin")
_build_lock = threading.Lock()


class XlatError(RuntimeError):
    def __init__(self, message, returncode=None, records=None):
        RuntimeError.__init__(self, message)
        self.returncode = returncode
        self.records = records or []


class WindowTimeout(XlatError):
    pass


class NotFocusedError(RuntimeError):
    pass


def _stale():
    newest_src = 0.0
    for name in os.listdir(_HELPERS):
        if name.endswith((".c", ".h")):
            newest_src = max(newest_src, os.path.getmtime(os.path.join(_HELPERS, name)))
    for prog in _PROGRAMS:
        path = os.path.join(BIN_DIR, prog)
        if not os.access(path, os.X_OK) or os.path.getmtime(path) < newest_src:
            return True
    return False


def ensure_built():
    """Build xlat/testwin for this platform if missing or older than their sources."""
    if os.environ.get("XTRP_XLAT"):
        return
    with _build_lock:
        if _stale():
            subprocess.check_call(["sh", BUILD_SH], env=platform.plain_env())


def _parse(out):
    return [json.loads(line) for line in out.decode("utf-8", "replace").splitlines() if line.strip()]


def run_json(args, display, timeout_s):
    """Run `xlat <args>` against `display`; return its JSON lines as dicts."""
    ensure_built()
    proc = subprocess.Popen([XLAT] + [str(a) for a in args], env=platform.helper_env(display),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        raise XlatError("xlat %s timed out after %.1f s" % (args[0], timeout_s), None, _parse(out))
    records = _parse(out)
    if proc.returncode != 0:
        raise XlatError("xlat %s exited %d: %s" % (args[0], proc.returncode,
                                                  err.decode("utf-8", "replace").strip()[-500:]),
                        proc.returncode, records)
    return records


def info(display):
    return run_json(["info"], display, 10.0)[0]


def wait_window(display, title, timeout_ms=15000):
    """(window id, CLOCK_MONOTONIC seconds) of the viewable window titled `title`."""
    try:
        rec = run_json(["wait-window", "--title", title, "--timeout-ms", timeout_ms], display,
                       timeout_ms / 1000.0 + 5.0)[0]
    except XlatError as e:
        if e.returncode == 3:
            raise WindowTimeout("no window titled %r within %d ms" % (title, timeout_ms), 3)
        raise
    return rec["window"], rec["t_ns"] / 1e9


def focus(display, window):
    run_json(["focus", "--window", window], display, 5.0)


def latency(display, window, samples, interval_ms=120, timeout_ms=2000, require_focus=False):
    """Keypress-to-damage latency per sample, in ms (None when no damage arrived)."""
    args = ["latency", "--window", window, "--samples", samples,
            "--interval-ms", interval_ms, "--timeout-ms", timeout_ms]
    if require_focus:
        args.append("--require-focus")
    budget = samples * (interval_ms + timeout_ms) / 1000.0 + 10.0
    try:
        records = run_json(args, display, budget)
    except XlatError as e:
        if e.returncode == 2:
            raise NotFocusedError("window %d does not have input focus" % window)
        raise
    out = []
    for r in records:
        if "i" in r:
            out.append(None if r["damage_ns"] is None else (r["damage_ns"] - r["inject_ns"]) / 1e6)
    return out
