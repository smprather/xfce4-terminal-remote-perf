"""Live measurements on a user's real desktop (`xtrp live ...`).

live_latency types only `a` and BackSpace, in equal numbers, and only while
the target window has keyboard focus: xlat checks focus before every key and
refuses (NotFocusedError) otherwise, so nothing ever lands in another window.
"""

import os
import time

from xtrp import xlat
from xtrp.metrics import DamageWatch, proc_cpu_s, summarize

_SERVER_COMMS = ("Xvnc", "Xorg", "Xvfb", "nxagent")


def live_latency(display, window=None, pick=False, samples=40):
    """Keypress-to-damage latency on `window` (default: this terminal, $WINDOWID); requires focus."""
    if pick:
        window = xlat.run_json(["pick"], display, 120.0)[0]["window"]
    if window is None:
        if not os.environ.get("WINDOWID"):
            raise RuntimeError("no --window/--pick and $WINDOWID is not set")
        window = int(os.environ["WINDOWID"])
    samples += samples % 2              # equal numbers of 'a' and BackSpace: no net input
    raw = xlat.latency(display, window, samples, require_focus=True)
    return {"window": window, "latency_ms": summarize(raw), "raw": raw}


def _cmdline(pid):
    try:
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            return f.read().decode("utf-8", "replace").split("\0")
    except OSError:
        return []


def xserver_pid(display):
    """pid of the local X server for `display` (Xvnc, Xorg, Xvfb, nxagent, etx*), or None."""
    if not display or display.rsplit(":", 1)[0] not in ("", "unix"):
        return None
    number = display.rsplit(":", 1)[1].split(".")[0]
    found = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open("/proc/%s/comm" % name) as f:
                comm = f.read().strip()
        except OSError:
            continue
        if comm in _SERVER_COMMS or comm.startswith("etx"):
            if ":" + number in _cmdline(int(name)):
                found.append(int(name))
    return found[0] if len(found) == 1 else None


def live_watch(display, window, seconds):
    """Damage on `window` (and the X server's CPU, when it is local) while the user drives it."""
    pid = xserver_pid(display)
    cpu0 = proc_cpu_s(pid) if pid else None
    dw = DamageWatch(display, window).start()
    try:
        time.sleep(seconds)
    finally:
        st = dw.stop()
    return {"damage_events": st["events"], "damage_area_px": st["area_px"],
            "xserver_cpu_s": (proc_cpu_s(pid) - cpu0) if pid else None}
