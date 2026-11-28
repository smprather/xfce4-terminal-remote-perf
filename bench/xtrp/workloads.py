"""Workloads: deterministic payload generators, the workload table, and the
in-terminal payload side (`python3 -m xtrp workload <name> ...`).

tmux is only ever reached through tmux_argv(), which always passes a private
`-L xtrp-...` socket; workload commands also point TMUX_TMPDIR at the run's
own directory, so the shared default tmux server is never touched.
"""

import collections
import itertools
import json
import os
import random
import shlex
import sys
import time

from xtrp import platform

CHUNK = 64 * 1024
MIB = 1 << 20
_BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(_BENCH, "conf")
NVIM_INIT = os.path.join(CONF, "nvim", "init.lua")
TMUX_CONF = os.path.join(CONF, "tmux.conf")
_POOL = 2048
_socket_counter = itertools.count(1)

DEFAULT_BYTES = 50 * MIB
TMUX_BULK_BYTES = 20 * MIB
DEFAULT_LINES = 200000
REDRAW_SECONDS = 5.0
REDRAW_FPS = 60
SCROLL_STEPS = 2000

# --------------------------------------------------------------------------- generators


def _sized(pieces, n_bytes):
    """Concatenate byte pieces into exactly n_bytes, yielding chunks of at most CHUNK.

    A piece that would overflow is dropped whole (so no UTF-8 sequence or
    escape is split) and the remainder is padded with ASCII dots and a newline.
    """
    buf = bytearray()
    total = 0
    for piece in pieces:
        if total + len(piece) > n_bytes:
            break
        buf += piece
        total += len(piece)
        while len(buf) >= CHUNK:
            yield bytes(buf[:CHUNK])
            del buf[:CHUNK]
        if total == n_bytes:
            break
    pad = n_bytes - total
    if pad:
        buf += b"." * (pad - 1) + b"\n"
    while buf:
        yield bytes(buf[:CHUNK])
        del buf[:CHUNK]


def _pooled(make_piece, n_bytes, seed):
    rng = random.Random(seed)
    pool = [make_piece(rng).encode("utf-8") for _ in range(_POOL)]
    return _sized((rng.choice(pool) for _ in itertools.count()), n_bytes)


_PRINTABLE = "".join(chr(c) for c in range(32, 127))


def _ascii_line(rng):
    return "".join(rng.choice(_PRINTABLE) for _ in range(rng.randint(40, 200))) + "\n"


def gen_bulk_ascii(n_bytes, seed=1):
    """Printable ASCII lines of 40-200 columns."""
    return _pooled(_ascii_line, n_bytes, seed)


def _sgr_line(rng):
    out, width, target = [], 0, rng.randint(60, 160)
    while width < target:
        attrs = ["0"]
        for code, p in (("1", 0.2), ("3", 0.15), ("4", 0.15)):
            if rng.random() < p:
                attrs.append(code)
        if rng.random() < 0.5:
            attrs.append("38;5;%d" % rng.randrange(256))
        else:
            attrs.append("38;2;%d;%d;%d" % (rng.randrange(256), rng.randrange(256), rng.randrange(256)))
        if rng.random() < 0.25:
            attrs.append("48;5;%d" % rng.randrange(256))
        n = rng.randint(1, 8)
        out.append("\x1b[%sm%s" % (";".join(attrs), "".join(rng.choice(_PRINTABLE) for _ in range(n))))
        width += n
    return "".join(out) + "\x1b[0m\n"


def gen_sgr(n_bytes, seed=1):
    """Runs of 1-8 characters, each with a 256-colour or truecolour SGR plus bold/italic/underline."""
    return _pooled(_sgr_line, n_bytes, seed)


def _unicode_token(rng):
    kind = rng.random()
    if kind < 0.30:
        return chr(rng.randint(0x4E00, 0x9FFF)), 2
    if kind < 0.45:
        marks = "".join(chr(rng.randint(0x0300, 0x036F)) for _ in range(rng.randint(1, 2)))
        return rng.choice("aeiouxyz") + marks, 1
    if kind < 0.60:
        return chr(rng.choice((rng.randint(0x1F600, 0x1F64F), rng.randint(0x1F300, 0x1F5FF)))), 2
    if kind < 0.75:
        return chr(rng.choice((rng.randint(0xE0A0, 0xE0D4), rng.randint(0xF000, 0xF2E0)))), 1
    word = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(1, 6)))
    return word + " ", len(word) + 1


def _unicode_line(rng):
    out, width, target = [], 0, rng.randint(50, 100)
    while width < target:
        token, w = _unicode_token(rng)
        out.append(token)
        width += w
    return "".join(out) + "\n"


def gen_unicode(n_bytes, seed=1):
    """CJK (wide), combining marks, emoji, and Nerd Font PUA glyphs mixed with ASCII words."""
    return _pooled(_unicode_line, n_bytes, seed)


_BOX_STYLES = (
    # corners/tees/cross, horizontal, vertical: light, heavy, double
    ("┌┬┐├┼┤└┴┘", "─", "│"),
    ("┏┳┓┣╋┫┗┻┛", "━", "┃"),
    ("╔╦╗╠╬╣╚╩╝", "═", "║"),
)
_BLOCKS = "▀▄█▌▐░▒▓▖▗▘▙▚▛▜▝▞▟ "


def _box_table(rng):
    joints, h, v = rng.choice(_BOX_STYLES)
    widths = [rng.randint(3, 14) for _ in range(rng.randint(2, 6))]

    def rule(left, mid, right):
        return left + mid.join(h * w for w in widths) + right + "\n"

    def cells():
        return v + v.join("".join(rng.choice(_BLOCKS) for _ in range(w)) for w in widths) + v + "\n"

    rows = [cells() for _ in range(rng.randint(1, 4))]
    return (rule(joints[0], joints[1], joints[2])
            + rule(joints[3], joints[4], joints[5]).join(rows)
            + rule(joints[6], joints[7], joints[8]))


def gen_box(n_bytes, seed=1):
    """Tables and borders from U+2500-U+259F (light, heavy, double lines; block-element fills)."""
    return _pooled(_box_table, n_bytes, seed)


_DIRS = ("core", "net", "ui", "util", "io", "vte", "render", "parse")
_NAMES = ("buffer", "screen", "ring", "parser", "widget", "draw", "cell", "row", "utf8", "keymap")
_MESSAGES = (
    "unused variable 'tmp' [-Wunused-variable]",
    "comparison of integer expressions of different signedness [-Wsign-compare]",
    "implicit conversion changes signedness [-Wsign-conversion]",
    "'len' may be used uninitialized in this function [-Wmaybe-uninitialized]",
    "control reaches end of non-void function [-Wreturn-type]",
    "passing argument 1 of 'memcpy' discards 'const' qualifier [-Wdiscarded-qualifiers]",
    "in expansion of macro 'G_STATIC_ASSERT'",
    "declared here",
    "expected ';' before '}' token",
)


def gen_compile_log(n_lines, seed=1):
    """gcc-like `path:line:col: severity: message` lines, about a quarter colourised like gcc."""
    rng = random.Random(seed)
    buf = bytearray()
    for _ in range(n_lines):
        loc = "src/%s/%s%d.c:%d:%d:" % (rng.choice(_DIRS), rng.choice(_NAMES), rng.randrange(100),
                                        rng.randint(1, 5000), rng.randint(1, 120))
        r = rng.random()
        sev, colour = ("warning", "01;35") if r < 0.7 else (("note", "01;36") if r < 0.9 else ("error", "01;31"))
        msg = rng.choice(_MESSAGES)
        if rng.random() < 0.25:
            line = "\x1b[01m\x1b[K%s\x1b[m\x1b[K \x1b[%sm\x1b[K%s:\x1b[m\x1b[K %s\n" % (loc, colour, sev, msg)
        else:
            line = "%s %s: %s\n" % (loc, sev, msg)
        buf += line.encode()
        while len(buf) >= CHUNK:
            yield bytes(buf[:CHUNK])
            del buf[:CHUNK]
    while buf:
        yield bytes(buf[:CHUNK])
        del buf[:CHUNK]


def gen_source_file(n_lines=50000, seed=1):
    """A C-like source file of exactly n_lines lines, for nvim."""
    rng = random.Random(seed)
    lines = ["/* generated by xtrp for nvim-scroll */", "#include <stdio.h>", ""]
    n = 0
    while len(lines) < n_lines:
        n += 1
        a, b = rng.randint(1, 99), rng.randint(1, 9)
        lines += [
            "static int fn_%d(int a, int b)" % n,
            "{",
            "    int x = a + %d;  /* offset */" % a,
            "    if (x > b) {",
            "        x -= b * %d;" % b,
            "    }",
            "    for (int i = 0; i < %d; i++)" % rng.randint(2, 64),
            "        x ^= i << %d;" % rng.randint(1, 7),
            '    printf("fn_%d %%d\\n", x);' % n,
            "    return x;",
            "}",
            "",
        ]
    return "\n".join(lines[:n_lines]) + "\n"


GENERATORS = {"bulk-ascii": gen_bulk_ascii, "sgr-color": gen_sgr, "unicode": gen_unicode, "box-drawing": gen_box}

# --------------------------------------------------------------------------- workload table

# region: (col, row, cols, rows) of the terminal where latency is taken, pixel-checked (None: the
# first damage anywhere); e2e: also measure end to end over VNC; load: the command starts background
# output on the go file, which the runner creates before the latency probes.
Workload = collections.namedtuple("Workload", "name kind command timeout_s region e2e load")
Workload.__new__.__defaults__ = (None, True, False)


class WorkloadCtx(object):
    """Per-run inputs to a workload's command."""

    def __init__(self, status_path, workdir, sync=False, n_bytes=None):
        self.status_path = status_path
        self.workdir = workdir
        self.sync = sync
        self.n_bytes = n_bytes
        self.go_path = os.path.join(workdir, "go")      # throughput payloads start when this exists
        self.tmux_socket = "xtrp-%d-%d" % (os.getpid(), next(_socket_counter))


def tmux_argv(socket, *args):
    """The only way to build a tmux command line: always on a private xtrp-* socket."""
    if not socket.startswith("xtrp-"):
        raise ValueError("tmux sockets must be private xtrp-* sockets, not %r" % socket)
    exe = platform.tool("tmux") or "tmux"
    return [exe, "-L", socket] + list(args)


def _env_prefix(ctx, *assignments):
    return ["env"] + list(assignments) + (["XTRP_SYNC=1"] if ctx.sync else [])


def _payload(ctx, name, *extra):
    return (_env_prefix(ctx, "PYTHONPATH=" + _BENCH)
            + [sys.executable, "-m", "xtrp", "workload", name, "--status", ctx.status_path,
               "--go", ctx.go_path] + list(extra))


def _nvim():
    return platform.tool("nvim") or "nvim"


def _tmux_env(ctx):
    return "TMUX_TMPDIR=" + ctx.workdir


def _bulk(name):
    return lambda ctx: _payload(ctx, name, "--bytes", str(ctx.n_bytes or DEFAULT_BYTES))


def _tmux_bulk_split(ctx):
    left = " ".join(shlex.quote(a) for a in _payload(ctx, "bulk-ascii", "--bytes",
                                                     str(ctx.n_bytes or TMUX_BULK_BYTES)))
    return _env_prefix(ctx, _tmux_env(ctx)) + tmux_argv(ctx.tmux_socket, "-f", TMUX_CONF, "new-session", "cat",
                                                        ";", "split-window", "-h", "-b", left)


def _tmux_pane_switch(ctx):
    """Two idle panes; `a` and BackSpace are bound (no prefix) to switch to the other pane."""
    switch = ["select-pane", "-t", ":.+"]
    return _env_prefix(ctx, _tmux_env(ctx)) + tmux_argv(
        ctx.tmux_socket, "-f", TMUX_CONF, "new-session", "cat", ";", "split-window", "-v", "cat",
        ";", "bind-key", "-n", "a", *switch, ";", "bind-key", "-n", "BSpace", *switch)


def _tmux_type_load(ctx):
    """Typing in the top pane (a cursor-hidden key marker) while the bottom pane pours out output."""
    marker = " ".join(shlex.quote(a) for a in _payload(ctx, "key-marker"))
    load = " ".join(shlex.quote(a) for a in _payload(ctx, "bulk-loop"))
    return _env_prefix(ctx, _tmux_env(ctx)) + tmux_argv(ctx.tmux_socket, "-f", TMUX_CONF, "new-session", marker,
                                                        ";", "split-window", "-d", "-v", load)


WORKLOADS = {w.name: w for w in (
    Workload("shell-echo", "latency",
             lambda ctx: _env_prefix(ctx, "PS1=$ ") + ["bash", "--norc", "--noprofile", "-i"], 60),
    Workload("nvim-type", "latency",
             lambda ctx: _env_prefix(ctx) + [_nvim(), "-u", NVIM_INIT, "-i", "NONE", "-n", "+startinsert"], 60),
    Workload("tmux-type", "latency",
             lambda ctx: _env_prefix(ctx, _tmux_env(ctx)) + tmux_argv(ctx.tmux_socket, "-f", TMUX_CONF,
                                                                     "new-session", "cat"), 60),
    Workload("bulk-ascii", "throughput", _bulk("bulk-ascii"), 600),
    Workload("sgr-color", "throughput", _bulk("sgr-color"), 600),
    Workload("unicode", "throughput", _bulk("unicode"), 600),
    Workload("box-drawing", "throughput", _bulk("box-drawing"), 600),
    Workload("compile-log", "throughput", lambda ctx: _payload(ctx, "compile-log", "--lines", str(DEFAULT_LINES)), 600),
    Workload("fullscreen-redraw", "throughput", lambda ctx: _payload(ctx, "fullscreen-redraw"), 120),
    Workload("nvim-scroll", "throughput",
             lambda ctx: _payload(ctx, "nvim-scroll", "--steps", str(SCROLL_STEPS)), 300),
    Workload("tmux-bulk-split", "throughput", _tmux_bulk_split, 600),
    Workload("tmux-pane-switch", "latency", _tmux_pane_switch, 60),
    # Under load the terminal repaints most of the window many times a second, so the sample is the
    # first paint that changes the marker's 16 cells (row 1 of the top pane).
    Workload("tmux-type-load", "latency", _tmux_type_load, 60, region=(0, 0, 20, 1), e2e=False, load=True),
)}


def cleanup(ctx):
    """Stop the run's private tmux server, if one was started."""
    sock_dir = os.path.join(ctx.workdir, "tmux-%d" % os.getuid())
    if not os.path.exists(os.path.join(sock_dir, ctx.tmux_socket)):
        return
    env = platform.plain_env()
    env["TMUX_TMPDIR"] = ctx.workdir
    import subprocess
    subprocess.run(tmux_argv(ctx.tmux_socket, "kill-server"), env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)

# --------------------------------------------------------------------------- payload side (runs in the pty)


def _emit(status_path, event):
    with open(status_path, "a") as f:
        f.write(json.dumps(event) + "\n")


def _write_all(data):
    view = memoryview(data)
    off = 0
    while off < len(view):
        off += os.write(1, view[off:off + CHUNK])


def _redraw_frames(cols, rows, seconds, sync):
    """Write alternate-screen full repaints at REDRAW_FPS for `seconds`; return (frames, bytes)."""
    total = 0
    enter = b"\x1b[?1049h\x1b[?25l"
    _write_all(enter)
    total += len(enter)
    t0 = time.monotonic()
    frames = 0
    while time.monotonic() - t0 < seconds:
        ch = chr(33 + frames % 94)
        body = "\r\n".join((ch * cols)[:cols] for _ in range(rows))
        frame = "\x1b[H" + body
        if sync:
            frame = "\x1b[?2026h" + frame + "\x1b[?2026l"
        data = frame.encode()
        _write_all(data)
        total += len(data)
        frames += 1
        wait = t0 + frames / float(REDRAW_FPS) - time.monotonic()
        if wait > 0:
            time.sleep(wait)
    return frames, total


def _key_marker():
    """Typing target for tmux-type-load: cursor hidden (so tmux's redraws of the other pane never
    repaint it here), and every read from the keyboard toggles a block at row 1."""
    import tty
    tty.setraw(0)
    _write_all(b"\x1b[?25l\x1b[2J")
    on = False
    while os.read(0, 1024):
        on = not on
        _write_all(b"\x1b[1;1H" + (b"#" * 16 if on else b" " * 16))


def _await_go(go, timeout_s=600.0):
    """Block until the runner creates the go file (startup has settled), if one was given."""
    if not go:
        return
    deadline = time.monotonic() + timeout_s
    while not os.path.exists(go) and time.monotonic() < deadline:
        time.sleep(0.005)


def run_payload(name, status, n_bytes=None, lines=None, seconds=None, cols=None, rows=None, steps=None,
                exit_after=False, go=None):
    """The in-terminal side of a throughput workload. Sleeps forever afterwards unless exit_after.

    The data is generated first; the start event and the writing wait for the go file."""
    sync = os.environ.get("XTRP_SYNC") == "1"
    if name == "key-marker":
        return _key_marker()
    if name == "bulk-loop":
        data = b"".join(gen_bulk_ascii(8 * MIB))
        _await_go(go)
        while True:                       # until the run's tmux server is stopped
            _write_all(data)
    if name == "nvim-scroll":
        src = os.path.join(os.path.dirname(os.path.abspath(status)), "xtrp-scroll.c")
        with open(src, "w") as f:
            f.write(gen_source_file())
        env = dict(os.environ, XTRP_STATUS=status)
        if go:
            env["XTRP_GO"] = go
        lua = "lua vim.defer_fn(function() XtrpScroll(%d) end, 300)" % (steps or SCROLL_STEPS)
        os.execvpe(_nvim(), [_nvim(), "-u", NVIM_INIT, "-i", "NONE", "-n", src, "-c", lua], env)
    extra = {}
    if name in GENERATORS:
        data = b"".join(GENERATORS[name](n_bytes or DEFAULT_BYTES))
    elif name == "compile-log":
        data = b"".join(gen_compile_log(lines or DEFAULT_LINES))
    elif name == "fullscreen-redraw":
        data = None
    else:
        raise SystemExit("xtrp workload: %s has no payload side" % name)
    _await_go(go)
    _emit(status, {"event": "start", "t": time.monotonic()})
    if data is None:
        size = os.get_terminal_size(1) if cols is None or rows is None else None   # the real pty size
        frames, nbytes = _redraw_frames(cols or size.columns, rows or size.lines,
                                        REDRAW_SECONDS if seconds is None else seconds, sync)
        extra["frames"] = frames
    else:
        _write_all(data)
        nbytes = len(data)
    t_end = time.monotonic()
    event = {"event": "end", "t": t_end, "bytes": nbytes}
    event.update(extra)
    _emit(status, event)
    sys.stdout.flush()
    if exit_after:
        return
    while True:
        time.sleep(3600)
