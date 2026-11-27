"""Shared fixtures for the xtrp test suite (X servers, testwin, tool checks)."""

import json
import os
import shutil
import signal
import subprocess
import tempfile
import unittest

from xtrp import platform, xlat
from xtrp.display import XServer


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


class XvfbFixture(unittest.TestCase):
    """Starts a private X server (1024x768x24; Xvfb unless server_kind says xvnc) per test;
    tracks testwin processes."""

    server_kind = "xvfb"

    def setUp(self):
        need_tool({"xvfb": "Xvfb", "xvnc": "Xvnc"}[self.server_kind])
        self.tmp = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._testwins = {}
        self._xserver = XServer(self.server_kind, 1024, 768, 24).start()
        self.xserver = self._xserver
        self.display = self._xserver.display
        self.display_number = self._xserver.number
        self.addCleanup(self._stop_all)

    def start_testwin(self, title, delay_ms, rect, damage_forever=False, display=None):
        """Start testwin (connected to `display`, default the fixture's server); return its window."""
        argv = [os.path.join(xlat.BIN_DIR, "testwin"), "--title", title,
                "--delay-ms", str(delay_ms), "--rect", rect]
        if damage_forever:
            argv.append("--damage-forever")
        xlat.ensure_built()
        proc = subprocess.Popen(argv, env=platform.child_env(display or self.display, self.tmp),
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
        self._xserver.stop()
