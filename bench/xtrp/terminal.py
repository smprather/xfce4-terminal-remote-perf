"""Launch an xfce4-terminal build on a test display with pinned settings.

Settings are written twice from bench/conf/terminalrc.in: as terminalrc
(read by 1.0.4) and as an xfconf channel file (read by 1.1+, e.g. the
host's 1.2.0). The terminal runs under its own dbus-run-session so xfconfd
starts against the per-run HOME and nothing reaches a desktop session bus.
"""

import fcntl
import itertools
import os
import re
import signal
import struct
import termios
import time
from xml.sax.saxutils import quoteattr

from xtrp import platform, xlat
from xtrp.display import exited, spawn, stop_group

# The spec's two window sizes: 120x40, and 1920x1080 maximised. "large" is asked of the WM with
# --maximize; with no WM the window is moved and sized to the whole screen once it maps.
SIZES = {"small": "120x40", "large": "maximised"}
_SIZE_ARGS = {"small": ["--geometry", "120x40"], "large": ["--maximize"]}
FONTS = {"caskaydia": "CaskaydiaCove Nerd Font Mono 12", "dejavu": "DejaVu Sans Mono 12"}

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RC_TEMPLATE = os.path.join(_REPO, "bench", "conf", "terminalrc.in")
_counter = itertools.count(1)


class TerminalStartError(RuntimeError):
    pass


def _kebab(key):
    return re.sub(r"(?<!^)([A-Z])", r"-\1", key).lower()


def _xfconf_value(value):
    if value in ("TRUE", "FALSE"):
        return "bool", value.lower()
    if value.isdigit():
        return "uint", value
    return "string", value


def render_settings(font):
    """(terminalrc text, xfconf channel XML text) for FONTS[font]."""
    with open(RC_TEMPLATE) as f:
        rc = f.read().replace("@FONT@", FONTS[font])
    props = []
    for line in rc.splitlines():
        line = line.strip()
        if not line or line.startswith(("[", "#")) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        kind, xvalue = _xfconf_value(value)
        props.append('  <property name=%s type="%s" value=%s/>' % (quoteattr(_kebab(key)), kind, quoteattr(xvalue)))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n\n<channel name="xfce4-terminal" version="1.0">\n'
           + "\n".join(props) + "\n</channel>\n")
    return rc, xml


def proc_stat(pid):
    """(ppid, starttime, comm) from /proc/<pid>/stat, or None if gone."""
    try:
        with open("/proc/%d/stat" % pid) as f:
            data = f.read()
    except OSError:
        return None
    comm = data[data.index("(") + 1:data.rindex(")")]
    fields = data[data.rindex(")") + 2:].split()
    return int(fields[1]), int(fields[19]), comm


def descendants(pid):
    """[(pid, starttime)] of every live descendant of `pid`."""
    children = {}
    for name in os.listdir("/proc"):
        if name.isdigit():
            st = proc_stat(int(name))
            if st:
                children.setdefault(st[0], []).append((int(name), st[1]))
    out, todo = [], [pid]
    while todo:
        for child in children.get(todo.pop(), []):
            out.append(child)
            todo.append(child[0])
    return out


def _signal_if_same(pid, starttime, sig):
    st = proc_stat(pid)
    if st and st[1] == starttime:
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            pass
        return True
    return False


class Terminal(object):
    """One xfce4-terminal window on `display`. Context manager."""

    def __init__(self, build, display, size, font, command, workdir, env=None, xlat_display=None):
        """`xlat_display` is where the window is looked for (default `display`); the runner passes
        the real server when the terminal itself connects through the X11 proxy."""
        if size not in SIZES:
            raise ValueError("unknown size %r" % size)
        if font not in FONTS:
            raise ValueError("unknown font %r" % font)
        self.build, self.display, self.size, self.font = build, display, size, font
        self.command, self.workdir, self.env = list(command), workdir, dict(env or {})
        self.xlat_display = xlat_display or display
        self.window = self.pid = self.startup_ms = self.title = None
        self._proc = None

    def _write_settings(self):
        rc, xml = render_settings(self.font)
        cfg = os.path.join(self.workdir, "home", ".config", "xfce4")
        for sub, name, text in (("terminal", "terminalrc", rc),
                                (os.path.join("xfconf", "xfce-perchannel-xml"), "xfce4-terminal.xml", xml)):
            os.makedirs(os.path.join(cfg, sub), exist_ok=True)
            with open(os.path.join(cfg, sub, name), "w") as f:
                f.write(text)

    def _find_pid(self, timeout_s=2.0):
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            for pid, _ in descendants(self._proc.pid):
                st = proc_stat(pid)
                if st and st[2].startswith("xfce4-termina"):
                    return pid
            time.sleep(0.02)
        return None

    def start(self, timeout_s=15):
        self.title = "xtrp-%d-%d" % (os.getpid(), next(_counter))
        self._write_settings()
        extra = dict(self.build.env)
        extra.update(self.env)
        env = platform.child_env(self.display, self.workdir, extra)
        argv = (["dbus-run-session", "--", self.build.exec_path, "--disable-server"]
                + _SIZE_ARGS[self.size] + ["--title", self.title,
                 "--hide-menubar", "--hide-toolbar", "-x"] + self.command)
        log_path = os.path.join(self.workdir, "%s.log" % self.title)
        t0 = time.monotonic()
        self._proc = spawn(argv, env, log_path)
        try:
            return self._await_window(t0, timeout_s, log_path)
        except BaseException:              # Ctrl-C or an xlat failure: never leave it on the display
            self.stop()
            raise

    def _await_window(self, t0, timeout_s, log_path):
        deadline = t0 + timeout_s
        while True:
            left_ms = int((deadline - time.monotonic()) * 1000)
            if left_ms <= 0:
                self._fail("no window titled %s within %d s" % (self.title, timeout_s), log_path)
            try:
                self.window, t_win = xlat.wait_window(self.xlat_display, self.title, timeout_ms=min(2000, left_ms))
                break
            except xlat.WindowTimeout:
                if exited(self._proc):
                    self._fail("terminal exited before mapping its window", log_path)
        self.startup_ms = (t_win - t0) * 1000.0
        self.pid = self._find_pid()
        if self.pid is None:
            self._fail("window mapped but no xfce4-terminal process found", log_path)
        if self.size == "large" and xlat.info(self.xlat_display)["wm_name"] is None:
            xlat.fill_screen(self.xlat_display, self.window)
        return self

    def _fail(self, why, log_path):
        try:
            with open(log_path, "rb") as f:
                tail = f.read()[-1500:].decode("utf-8", "replace")
        except OSError:
            tail = ""
        self.stop()
        raise TerminalStartError("%s\n%s" % (why, tail))

    def geometry(self, settle_s=0.0):
        """xlat.geometry of the window, once it has stopped changing for 0.3 s (or `settle_s` passed)."""
        deadline = time.monotonic() + settle_s
        last, since = xlat.geometry(self.xlat_display, self.window), time.monotonic()
        while time.monotonic() < deadline and time.monotonic() - since < 0.3:
            time.sleep(0.05)
            g = xlat.geometry(self.xlat_display, self.window)
            if g != last:
                last, since = g, time.monotonic()
        return last

    def cells(self):
        """(cols, rows) of the terminal's pty, read from the first child attached to one; None if none."""
        for pid, _ in self.descendants():
            try:
                tty_path = os.readlink("/proc/%d/fd/0" % pid)
            except OSError:
                continue
            if not tty_path.startswith("/dev/pts/"):
                continue
            try:
                fd = os.open(tty_path, os.O_RDONLY | os.O_NOCTTY)
            except OSError:
                continue
            try:
                rows, cols = struct.unpack("HHHH", fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\0" * 8))[:2]
            finally:
                os.close(fd)
            return cols, rows
        return None

    def descendants(self):
        """[(pid, starttime)] of the terminal's live child processes (shell, workload)."""
        return descendants(self.pid) if self.pid else []

    def stop(self):
        if self._proc is None:
            return
        kids = self.descendants()
        stop_group(self._proc)
        self._proc = None
        # The terminal's children run in their own session (pty); SIGHUP normally ends them.
        # Backstop: signal any that survive, matched by start time so a recycled pid is never hit.
        deadline = time.monotonic() + 2.0
        pending = [k for k in kids if _signal_if_same(k[0], k[1], signal.SIGTERM)]
        while pending and time.monotonic() < deadline:
            time.sleep(0.02)
            pending = [k for k in pending if (proc_stat(k[0]) or (0, None))[1] == k[1]
                       and _zombie_free(k[0])]
        for pid, starttime in pending:
            _signal_if_same(pid, starttime, signal.SIGKILL)

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False


def _zombie_free(pid):
    """True while `pid` is alive and not a zombie."""
    try:
        with open("/proc/%d/stat" % pid) as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return False
