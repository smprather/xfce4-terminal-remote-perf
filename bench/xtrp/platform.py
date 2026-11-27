"""Platform detection, tool lookup, and environments for child processes.

Three platforms: "el8" and "el9" (the bench containers, or real EL hosts) and
"host" (anything else, e.g. the CachyOS dev box). Every process the harness
starts gets an environment built here from scratch, so nothing leaks to or
from a live desktop session on the host.
"""

import os
import shutil
import subprocess

PACMAN_PKG = {
    "Xvfb": "xorg-server-xvfb",
    "Xvnc": "tigervnc",
    "xprop": "xorg-xprop",
    "xdpyinfo": "xorg-xdpyinfo",
    "dbus-run-session": "dbus",
}

_PREFERRED = {
    "nvim": "/opt/nvim/bin/nvim",
    "tmux": "/usr/local/bin/tmux",
}

_INHERIT = ("PATH", "LANG", "TZ")
_DEFAULT_PATH = "/usr/local/bin:/usr/bin:/bin"


def _read_os_release(path):
    info = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                info[key] = value
    except OSError:
        pass
    return info


def platform_tag(os_release="/etc/os-release"):
    """'el<major>' for RHEL-family systems, else 'host'."""
    info = _read_os_release(os_release)
    words = (info.get("ID", "") + " " + info.get("ID_LIKE", "")).split()
    major = info.get("VERSION_ID", "").split(".")[0]
    if ("rhel" in words or "centos" in words) and major.isdigit():
        return "el" + major
    return "host"


def tool(name):
    """Absolute path of tool `name`, or None. nvim/tmux prefer the bench-image builds."""
    preferred = _PREFERRED.get(name)
    if preferred and os.access(preferred, os.X_OK):
        return preferred
    if os.path.isabs(name):
        return name if os.access(name, os.X_OK) else None
    return shutil.which(name)


def plain_env():
    """PATH/LANG/TZ only: for non-X helper commands (rpm, pacman, cc)."""
    env = {k: os.environ[k] for k in _INHERIT if k in os.environ}
    env.setdefault("PATH", _DEFAULT_PATH)
    return env


def child_env(display, workdir, extra=None):
    """Fresh environment for an X server, WM, or terminal under test.

    Creates <workdir>/home (with XDG dirs) and <workdir>/run (mode 0700).
    Never sets WAYLAND_DISPLAY, DBUS_SESSION_BUS_ADDRESS, XAUTHORITY or
    SESSION_MANAGER.
    """
    home = os.path.join(workdir, "home")
    run = os.path.join(workdir, "run")
    env = plain_env()
    env.update({
        "DISPLAY": display,
        "HOME": home,
        "XDG_CONFIG_HOME": os.path.join(home, ".config"),
        "XDG_CACHE_HOME": os.path.join(home, ".cache"),
        "XDG_DATA_HOME": os.path.join(home, ".local", "share"),
        "XDG_RUNTIME_DIR": run,
        "GDK_BACKEND": "x11",
        "NO_AT_BRIDGE": "1",
    })
    for d in (env["XDG_CONFIG_HOME"], env["XDG_CACHE_HOME"], env["XDG_DATA_HOME"]):
        os.makedirs(d, exist_ok=True)
    os.makedirs(run, exist_ok=True)
    os.chmod(run, 0o700)
    if extra:
        env.update(extra)
    return env


def helper_env(display):
    """Environment for our own xlat helper: DISPLAY plus what Xlib needs to authenticate."""
    env = plain_env()
    for k in ("XAUTHORITY", "HOME"):
        if k in os.environ:
            env[k] = os.environ[k]
    env["DISPLAY"] = display
    return env


def packages():
    """Installed versions of the terminal and VTE: {'xfce4-terminal': str|None, 'vte': str|None}."""
    if platform_tag() == "host":
        cmd, names = ["pacman", "-Q"], {"xfce4-terminal": "xfce4-terminal", "vte": "vte3"}
    else:
        cmd, names = ["rpm", "-q"], {"xfce4-terminal": "xfce4-terminal", "vte": "vte291"}
    out = {}
    for key, pkg in sorted(names.items()):
        try:
            r = subprocess.run(cmd + [pkg], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               env=plain_env(), universal_newlines=True, timeout=10)
            out[key] = r.stdout.strip() if r.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            out[key] = None
    return out
