"""Shared fixtures for the xtrp test suite (X servers, testwin, tool checks)."""

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
import unittest

from xtrp import platform, xlat


def pid_alive(pid):
    """True if `pid` exists and is not a zombie."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        with open("/proc/%d/stat" % pid) as f:
            state = f.read().rsplit(")", 1)[1].split()[0]
    except (OSError, IndexError):
        return False
    return state != "Z"


def need_tool(name):
    """Path of `name`; fail in a container, skip on the host, when it is missing."""
    path = platform.tool(name)
    if path:
        return path
    if platform.platform_tag() == "host":
        raise unittest.SkipTest("host lacks %s (pacman -S %s)"
                                % (name, platform.PACMAN_PKG.get(name, name)))
    raise AssertionError("bench image lacks %s" % name)


def _free_display():
    for n in range(50, 100):
        if not (os.path.exists("/tmp/.X%d-lock" % n) or os.path.exists("/tmp/.X11-unix/X%d" % n)):
            return n
    raise RuntimeError("no free display in :50..:99")


class XvfbFixture(unittest.TestCase):
    """Starts a private Xvfb (1024x768x24) per test; tracks testwin processes."""

    def setUp(self):
        need_tool("Xvfb")
        self.tmp = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._testwins = {}
        self._start_xvfb()
        self.addCleanup(self._stop_all)

    def _start_xvfb(self):
        last = None
        for _ in range(5):
            n = _free_display()
            display = ":%d" % n
            proc = subprocess.Popen(
                ["Xvfb", display, "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-noreset"],
                env=platform.child_env(display, self.tmp),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            deadline = time.monotonic() + 10.0
            while time.monotonic() < deadline and proc.poll() is None:
                try:
                    xlat.info(display)
                except xlat.XlatError as e:
                    last = e
                    time.sleep(0.05)
                    continue
                self.display, self.display_number, self._xvfb = display, n, proc
                return
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
        raise RuntimeError("Xvfb did not start: %s" % last)

    def start_testwin(self, title, delay_ms, rect, damage_forever=False):
        argv = [os.path.join(xlat.BIN_DIR, "testwin"), "--title", title,
                "--delay-ms", str(delay_ms), "--rect", rect]
        if damage_forever:
            argv.append("--damage-forever")
        xlat.ensure_built()
        proc = subprocess.Popen(argv, env=platform.child_env(self.display, self.tmp),
                                stdout=subprocess.PIPE, start_new_session=True)
        window, _ = xlat.wait_window(self.display, title, timeout_ms=10000)
        self._testwins[window] = proc
        return window

    def stop_testwin(self, window):
        proc = self._testwins.pop(window)
        proc.send_signal(signal.SIGTERM)
        out, _ = proc.communicate(timeout=10)
        return json.loads(out.decode().strip().splitlines()[-1])

    def _stop_all(self):
        for proc in self._testwins.values():
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            if proc.stdout:
                proc.stdout.close()
        self._testwins = {}
        proc = getattr(self, "_xvfb", None)
        if proc is not None and proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
