"""Measurement primitives: process CPU time, summaries, and damage watching."""

import json
import os
import signal
import subprocess
import threading
import time

from xtrp import platform, xlat

_CLK_TCK = float(os.sysconf("SC_CLK_TCK"))


_threads_seen = {}      # (pid, starttime) -> {tid: last schedstat ns}


def proc_cpu_s(pid):
    """CPU seconds used by process `pid`, monotonic within this Python process.

    Sums /proc/<pid>/task/*/schedstat (nanoseconds on CPU per thread);
    /proc/<pid>/stat only counts 10 ms ticks, which made small deltas (40
    keypresses) pure quantization noise. A thread that has exited keeps its
    last reading, so CPU it used before the window never vanishes from a
    delta (GLib pool threads exit ~15 s after going idle). Falls back to
    utime + stime when schedstat is unavailable.
    """
    with open("/proc/%d/stat" % pid) as f:
        data = f.read()
    fields = data[data.rindex(")") + 2:].split()
    known = _threads_seen.setdefault((pid, fields[19]), {})
    found = False
    try:
        tids = os.listdir("/proc/%d/task" % pid)
    except OSError:
        tids = []
    for tid in tids:
        try:
            with open("/proc/%d/task/%s/schedstat" % (pid, tid)) as f:
                ns = int(f.read().split()[0])
        except (OSError, ValueError, IndexError):
            continue
        known[tid] = max(ns, known.get(tid, 0))
        found = True
    if found:
        return sum(known.values()) / 1e9
    return (int(fields[11]) + int(fields[12])) / _CLK_TCK


def _percentile(ordered, p):
    """Linear interpolation between closest ranks (numpy's default)."""
    idx = p * (len(ordered) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def summarize(values):
    """{"n", "median", "p10", "p90"} of `values`, ignoring None."""
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return {"n": 0, "median": None, "p10": None, "p90": None}
    return {"n": len(vals), "median": _percentile(vals, 0.5),
            "p10": _percentile(vals, 0.1), "p90": _percentile(vals, 0.9)}


class DamageWatch(object):
    """Counts XDamage rectangles on a window via `xlat damage`, from start() until stop()."""

    def __init__(self, display, window):
        self.display, self.window = display, window
        self.events = 0
        self.area_px = 0
        self.last_event_t = None          # CLOCK_MONOTONIC seconds of the latest rectangle
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._proc = None
        self._thread = None
        self._result = None

    def start(self, timeout_s=5.0):
        xlat.ensure_built()
        self._proc = subprocess.Popen([xlat.XLAT, "damage", "--window", str(self.window)],
                                      env=platform.helper_env(self.display),
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self._thread = threading.Thread(target=self._reader, name="damage-watch", daemon=True)
        self._thread.start()
        try:
            ready = self._ready.wait(timeout_s)
        except BaseException:
            self.stop()
            raise
        if not ready:
            self.stop()
            raise RuntimeError("xlat damage did not arm on window %s" % self.window)
        return self

    def _reader(self):
        for line in self._proc.stdout:
            rec = json.loads(line.decode())
            if "ready" in rec:
                self._ready.set()
                continue
            with self._lock:
                self.events += 1
                self.area_px += rec["w"] * rec["h"]
                self.last_event_t = rec["t_ns"] / 1e9

    def reset(self):
        """Zero the counters (start of the measured phase)."""
        with self._lock:
            self.events = 0
            self.area_px = 0
            self.last_event_t = None

    def wait_quiet(self, quiet_ms=300, cap_s=10.0):
        """Block until no damage for `quiet_ms` (counted from this call at the earliest).
        Returns False if `cap_s` passed first."""
        called = time.monotonic()
        deadline = called + cap_s
        quiet = quiet_ms / 1000.0
        while True:
            with self._lock:
                last = self.last_event_t
            now = time.monotonic()
            if now - max(last or 0.0, called) >= quiet:
                return True
            if now >= deadline:
                return False
            time.sleep(0.01)

    def stop(self):
        """Stop watching (idempotent); return {"events", "area_px"}."""
        if self._result is None:
            if self._proc is not None:
                if self._proc.poll() is None:
                    self._proc.send_signal(signal.SIGTERM)
                    try:
                        self._proc.wait(5)
                    except subprocess.TimeoutExpired:
                        self._proc.kill()
                        self._proc.wait()
                self._thread.join(5)
                self._proc.stdout.close()
            with self._lock:
                self._result = {"events": self.events, "area_px": self.area_px}
        return dict(self._result)
