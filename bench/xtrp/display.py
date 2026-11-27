"""X servers (Xvfb, TigerVNC Xvnc) and window managers (mutter, marco).

The matrix runner is the only caller that starts X servers. Displays come
from :50..:99. Every process is spawned in its own session with an
environment from platform.child_env(), and is stopped by process group
while its leader is still unreaped, so a recycled pid is never signalled.
"""

import os
import select
import shutil
import signal
import subprocess
import tempfile
import time

from xtrp import platform, xlat

DISPLAY_RANGE = range(50, 100)
WM_NAMES = ("none", "mutter", "marco-comp", "marco-nocomp")
_WM_BINARY = {"mutter": "mutter", "marco-comp": "marco", "marco-nocomp": "marco"}
_START_ATTEMPTS = 5


class XServerStartError(RuntimeError):
    pass


class WmStartError(RuntimeError):
    pass


def _lock_path(n):
    return "/tmp/.X%d-lock" % n


def _socket_path(n):
    return "/tmp/.X11-unix/X%d" % n


def pick_display(exclude=()):
    """First N in 50..99 with neither a lock file nor a socket, skipping `exclude`."""
    for n in DISPLAY_RANGE:
        if n in exclude:
            continue
        if not os.path.exists(_lock_path(n)) and not os.path.exists(_socket_path(n)):
            return n
    raise XServerStartError("no free display in :%d..:%d" % (DISPLAY_RANGE[0], DISPLAY_RANGE[-1]))


def spawn(argv, env, log_path, pass_fds=()):
    with open(log_path, "ab") as log:
        return subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                pass_fds=pass_fds, start_new_session=True)


def exited(proc):
    """True once the leader has exited; does not reap it (its pid stays reserved)."""
    if proc.returncode is not None:
        return True
    return os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None


def _killpg(pgid, sig):
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        pass


def stop_group(proc, grace_s=5.0):
    """SIGTERM the process group led by `proc`, SIGKILL after `grace_s`, then reap the leader."""
    if proc.returncode is not None:
        return
    _killpg(proc.pid, signal.SIGTERM)
    deadline = time.monotonic() + grace_s
    while not exited(proc) and time.monotonic() < deadline:
        time.sleep(0.02)
    _killpg(proc.pid, signal.SIGKILL)
    proc.wait()


def _tail(path, n=2000):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - n))
            return f.read().decode("utf-8", "replace").strip()
    except OSError:
        return ""


class XServer(object):
    """Xvfb or Xvnc on a free display in :50..:99. Context manager."""

    def __init__(self, kind, width=1920, height=1080, depth=24):
        if kind not in ("xvfb", "xvnc"):
            raise ValueError("XServer kind must be 'xvfb' or 'xvnc', not %r" % kind)
        self.kind, self.width, self.height, self.depth = kind, width, height, depth
        self.display = self.number = self.pid = self.rfb_port = None
        self._proc = None
        self._workdir = None

    def _argv(self, n, displayfd):
        if self.kind == "xvfb":
            argv = ["Xvfb", ":%d" % n, "-screen", "0", "%dx%dx%d" % (self.width, self.height, self.depth)]
        else:
            argv = ["Xvnc", ":%d" % n, "-geometry", "%dx%d" % (self.width, self.height),
                    "-depth", str(self.depth), "-SecurityTypes", "None", "-rfbport", str(5900 + n),
                    "-AlwaysShared"]
        # -nopn: exit if any listening socket (e.g. the abstract one) is taken, instead of
        # running half-listening while clients reach another server. -displayfd: say when ready.
        return argv + ["-nolisten", "tcp", "-noreset", "-nopn", "-displayfd", str(displayfd)]

    def _await_ready(self, proc, n, read_fd, timeout_s=10.0):
        deadline = time.monotonic() + timeout_s
        got = b""
        while time.monotonic() < deadline:
            ready, _, _ = select.select([read_fd], [], [], max(0.0, deadline - time.monotonic()))
            if not ready:
                break
            chunk = os.read(read_fd, 64)
            if not chunk:
                return False
            got += chunk
            if got.endswith(b"\n"):
                break
        if got.strip() != str(n).encode():
            return False
        while time.monotonic() < deadline and not exited(proc):
            try:
                xlat.info(":%d" % n)
                return True
            except xlat.XlatError:
                time.sleep(0.05)
        return False

    def _cleanup_leftovers(self, n, pid):
        try:
            with open(_lock_path(n)) as f:
                owner = f.read().strip()
        except OSError:
            return
        if owner == str(pid):
            for path in (_lock_path(n), _socket_path(n)):
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def start(self):
        self._workdir = tempfile.mkdtemp(prefix="xtrp-x-")
        tried, errors = set(), []
        for _ in range(_START_ATTEMPTS):
            n = pick_display(exclude=tried)
            tried.add(n)
            log_path = os.path.join(self._workdir, "server-%d.log" % n)
            read_fd, write_fd = os.pipe()
            try:
                proc = spawn(self._argv(n, write_fd), platform.child_env(":%d" % n, self._workdir),
                              log_path, pass_fds=(write_fd,))
            finally:
                os.close(write_fd)
            try:
                ok = self._await_ready(proc, n, read_fd)
            finally:
                os.close(read_fd)
            if ok:
                self._proc, self.number, self.pid = proc, n, proc.pid
                self.display = ":%d" % n
                self.rfb_port = 5900 + n if self.kind == "xvnc" else None
                return self
            stop_group(proc)
            self._cleanup_leftovers(n, proc.pid)
            errors.append(":%d: %s" % (n, _tail(log_path, 400)))
        shutil.rmtree(self._workdir, ignore_errors=True)
        raise XServerStartError("%s failed to start:\n%s" % (self.kind, "\n".join(errors)))

    def stop(self):
        if self._proc is not None:
            stop_group(self._proc)
            self._cleanup_leftovers(self.number, self._proc.pid)
            self._proc = None
        if self._workdir:
            shutil.rmtree(self._workdir, ignore_errors=True)
            self._workdir = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False


class WindowManager(object):
    """mutter or marco (compositing on/off) on `display`; "none" is a no-op. Context manager."""

    def __init__(self, name, display):
        if name not in WM_NAMES:
            raise ValueError("unknown window manager %r (want one of %s)" % (name, ", ".join(WM_NAMES)))
        self.name, self.display = name, display
        self._proc = None
        self._workdir = None

    @staticmethod
    def available(name):
        return name == "none" or platform.tool(_WM_BINARY[name]) is not None

    def _argv(self):
        if self.name == "mutter":
            return ["dbus-run-session", "--", "mutter", "--x11", "--replace", "--sm-disable"]
        flag = "--composite" if self.name == "marco-comp" else "--no-composite"
        return ["dbus-run-session", "--", "marco", "--replace", flag]

    def start(self, timeout_s=15.0):
        if self.name == "none":
            return self
        self._workdir = tempfile.mkdtemp(prefix="xtrp-wm-")
        log_path = os.path.join(self._workdir, "wm.log")
        self._proc = spawn(self._argv(), platform.child_env(self.display, self._workdir), log_path)
        want_cm = self.name in ("mutter", "marco-comp")
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if exited(self._proc):
                tail = _tail(log_path)
                self.stop()
                raise WmStartError("%s exited during startup:\n%s" % (self.name, tail))
            try:
                i = xlat.info(self.display)
            except xlat.XlatError:
                i = None
            if i and i["wm_name"] is not None and (i["cm_owner"] or not want_cm):
                return self
            time.sleep(0.1)
        tail = _tail(log_path)
        self.stop()
        raise WmStartError("%s not ready within %.0f s:\n%s" % (self.name, timeout_s, tail))

    def stop(self):
        if self._proc is not None:
            stop_group(self._proc)
            self._proc = None
        if self._workdir:
            shutil.rmtree(self._workdir, ignore_errors=True)
            self._workdir = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False
