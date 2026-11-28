"""Target diagnostics (`xtrp diag`) and the scrubber every report from a real site passes through.

collect() only reads: X server info, fonts and font-rendering settings, Xft
resources, package versions, session variables, and the CPU model. Its output
always goes through scrub(), which replaces host names, user names, IP
addresses, and site paths with placeholders.
"""

import getpass
import ipaddress
import os
import re
import socket
import subprocess

from xtrp import platform, xlat
from xtrp.terminal import FONTS

PACKAGES = ("vte291", "gtk3", "xfce4-terminal", "mutter", "marco", "tigervnc-server-minimal", "gnome-shell")
FONT_FAMILIES = tuple(FONTS[k].rsplit(" ", 1)[0] for k in ("caskaydia", "dejavu")) + ("monospace",)
FONT_RENDERING = (
    ("gnome", "org.gnome.desktop.interface", ("font-antialiasing", "font-hinting", "font-rgba-order")),
    # GNOME 3.32 (EL8) keeps these under its xsettings plugin
    ("gnome-xsettings", "org.gnome.settings-daemon.plugins.xsettings", ("antialiasing", "hinting", "rgba-order")),
    ("mate", "org.mate.font-rendering", ("antialiasing", "hinting", "rgba-order")),
)

_PATH_RE = re.compile(r"/(?:home|vols|proj|net|nfs)/[^\s\"'`,;)]*")
# 3+ dot-separated labels whose last label is alphabetic (a TLD): keeps versions like 0.52.4-2.el8.x86_64
_HOST_RE = re.compile(r"(?<![\w.-])[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\.[A-Za-z]{2,63}(?![\w-])")
_IPV4_RE = re.compile(r"(?<![\d.])\d{1,3}(?:\.\d{1,3}){3}(?![\d.])")
_IPV6_RE = re.compile(r"(?<![\w:])[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?![\w:])")


def _valid_ip(text):
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def _word_re(term):
    return re.compile(r"(?<![\w])%s(?![\w])" % re.escape(term))


def _scrub_str(s, extra_terms, hosts, users):
    for term in extra_terms:
        s = s.replace(term, "<redacted>")
    s = _PATH_RE.sub("<path>", s)
    s = _IPV4_RE.sub(lambda m: "<ip>" if _valid_ip(m.group(0)) else m.group(0), s)
    s = _IPV6_RE.sub(lambda m: "<ip>" if _valid_ip(m.group(0)) else m.group(0), s)
    s = _HOST_RE.sub("<host>", s)
    for h in hosts:
        s = h.sub("<host>", s)
    for u in users:
        s = u.sub("<user>", s)
    return s


def scrub(obj, extra_terms=()):
    """A scrubbed deep copy of `obj` (dict keys included)."""
    host = socket.gethostname()
    host_names = {host, host.split(".")[0]}
    user_names = {getpass.getuser(), os.environ.get("USER", ""), os.environ.get("LOGNAME", "")}
    hosts = [_word_re(h) for h in sorted(host_names, key=len, reverse=True) if len(h) >= 2]
    users = [_word_re(u) for u in sorted(user_names, key=len, reverse=True) if len(u) >= 2]
    extra = [t for t in extra_terms if t]

    def walk(o):
        if isinstance(o, str):
            return _scrub_str(o, extra, hosts, users)
        if isinstance(o, dict):
            return {walk(k): walk(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [walk(v) for v in o]
        return o
    return walk(obj)


def display_transport(display):
    """"unix" or "tcp" for a DISPLAY string (never the host itself); None when unset."""
    if not display:
        return None
    host = display.rsplit(":", 1)[0]
    return "unix" if host in ("", "unix") else "tcp"


def _run(argv, display):
    env = platform.helper_env(display)
    # No bus: gsettings would otherwise autolaunch a dbus-daemon on the user's real desktop. Settings
    # are still read (dconf reads its database files directly).
    env["DBUS_SESSION_BUS_ADDRESS"] = "disabled:"
    try:
        r = subprocess.run(argv, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, universal_newlines=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _xft(display):
    out = _run(["xrdb", "-query"], display)
    if out is None:
        return None
    res = {}
    for line in out.splitlines():
        if line.startswith("Xft.") and ":" in line:
            k, v = line.split(":", 1)
            res[k.strip()] = v.strip()
    return res


def _cpu_model():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def collect():
    """Scrubbed diagnostics for the display in $DISPLAY."""
    display = os.environ.get("DISPLAY", "")
    try:
        info = xlat.info(display)
    except xlat.XlatError as e:
        info = {"error": str(e)}
    d = {
        "xlat_info": info,
        "display_transport": display_transport(display),
        # fc-match takes family names; "DejaVu Sans Mono 12" would match nothing and fall back silently
        "fonts": {family: _run(["fc-match", family], display) for family in FONT_FAMILIES},
        "font_rendering": {label: {k: _run(["gsettings", "get", schema, k], display) for k in keys}
                           for label, schema, keys in FONT_RENDERING},
        "xft": _xft(display),
        "packages": {p: _run(["rpm", "-q", p], display) for p in PACKAGES},
        "session": {k: os.environ.get(k) for k in ("XDG_SESSION_TYPE", "XDG_CURRENT_DESKTOP", "DESKTOP_SESSION")},
        "cpu": {"nproc": os.cpu_count(), "model": _cpu_model()},
    }
    return scrub(d)
