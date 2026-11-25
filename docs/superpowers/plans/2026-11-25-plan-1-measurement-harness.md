# Plan 1: Measurement Harness + Baseline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `xtrp`, a harness that measures keypress latency, throughput, VNC bytes, X11 protocol
bytes, damage, CPU, and startup for xfce4-terminal builds in an EL8 container. It also runs reduced
modes (`diag`, `live`) on real target VMs. Use it to record the baseline: EPEL 1.0.4 + VTE 0.52.4.

**Architecture:** An EL8 container image provides X servers (Xvfb, TigerVNC Xvnc), WMs (mutter,
marco), the baseline terminal, nvim, tmux, and fonts. A small C helper (`xlat`) does the X-side
timing: XTest injection, XDamage, window discovery, and display info. A Python 3.6 stdlib-only
package does everything else: display/WM lifecycle, terminal launch, workload payloads, an RFB
client, a counting/delaying X11 proxy, the matrix runner, and reporting. Each run writes one JSON
record. `report` compares two sets of records.

**Tech Stack:** C (Xlib, XTest, XDamage, XFixes), Python 3.6 stdlib (`unittest`, `socket`,
`selectors`, `threading`, `subprocess`, `json`), Docker (`almalinux:8.10` + EPEL8 + PowerTools).

**Spec:** `docs/superpowers/specs/2026-11-25-remote-display-performance-design.md` (§7.2 is this plan;
§3 anti-goals and §8 validation apply).

**Roadmap (later plans, written when this one lands):**
- Plan 2: VTE 0.84 on EL8 + xfce4-terminal from source (spec §7.3–7.4).
- Plan 3: remote-display engine work (§7.5), ordered by Plan 1 numbers.
- Plan 4: engineering-loadout integration (§7.7, separate go-ahead).

## Global Constraints

- Every compile and every measurement that decides anything runs in the bench container (`bench/container …`);
  the CachyOS host is for editing only.
- Python must run on EL8's `/usr/bin/python3` (3.6). No dataclasses, no `subprocess.run(capture_output=…)`,
  no `asyncio.run`, no `time.monotonic_ns`, no walrus, no `from __future__ import annotations`. Tests use
  `unittest` (no pytest). Run them with `bench/container python3 -m unittest discover -s bench/tests -t bench`.
- Timestamps everywhere are CLOCK_MONOTONIC. Python uses `time.monotonic()` (float seconds). `xlat` prints
  integer nanoseconds; Python converts them to seconds on read.
- Spaces only, never tab characters. Python, C, and shell use a 4-space indent. Do not use Makefiles; build
  with `bench/helpers/build.sh`.
- tmux is only ever invoked with a private socket `-L xtrp-<pid>`. Never run `kill-server` without `-L`.
  `bench/tests/test_policy.py` enforces this.
- The matrix runner is the only thing that starts X servers. It picks display numbers from :50 to :99 and
  never touches `$DISPLAY` from the host.
- Nothing from a real site is committed before it passes `xtrp.diag.scrub` (spec §3 anti-goal).
- Run records follow schema 1, defined in Task 7. `report` treats unknown metrics as informational.
- Baseline build = `/usr/bin/xfce4-terminal` from EPEL8 `xfce4-terminal-1.0.4-1.el8` + AppStream
  `vte291-0.52.4`.
- Regression rule: the candidate is worse than the baseline median by more than `max(5%, baseline noise band)`.
  The noise band is `(p90 − p10) / median` of the baseline.

## Review Focus

1. **`live` mode typing into the wrong window** on a user's real desktop. Expected: it refuses to inject unless
   the target window currently has input focus; it only ever sends `a` and `BackSpace`, never Return.
   Test in Task 9.
2. **Leftover X servers, terminals, or tmux** after an exception or Ctrl-C mid-matrix poison later runs (stale
   `/tmp/.X50-lock`). Expected: every resource stops on any exit path. Test in Task 7.
3. **Damage that never settles** (cursor blink, tmux status clock) hangs the runner. Expected: a hard cap; the
   record gets `drain_timeout: true`. Test in Task 7.
4. **VNC traffic unrelated to the terminal** (pointer, cursor shape) inflates bytes and makes baseline-vs-baseline
   noisy. Expected: the pointer is parked, the Cursor pseudo-encoding is not requested, and a self-compare flags
   no regressions. Checked in Task 10.
5. **Site identifiers surviving `scrub`** (FQDN in DISPLAY or the vendor string, `/vols/...` paths, IPs). Expected:
   none survive. Test in Task 9.

---

## File Structure

```
bench/
  Dockerfile                 EL8 bench image
  container                  docker build + run wrapper (sh)
  pins.json                  pinned URLs + sha256 for nvim, tmux, nerd font
  builds.json                build registry: name -> exec path + env
  helpers/
    build.sh                 compiles xlat + testwin into bench/helpers/bin/
    xlat.c                   X-side timing helper (modes: info, wait-window, focus, latency, damage, pick)
    testwin.c                deterministic X test client for helper/RFB/proxy tests
  conf/
    terminalrc.in            xfce4-terminal 1.0.4 rc template
    nvim/init.lua            fixed nvim config (+ bench helpers)
    tmux.conf                fixed tmux config
  xtrp/
    __init__.py
    __main__.py              argparse CLI: run | report | diag | live | workload
    model.py                 Build, RunKey, record I/O
    display.py               XServer, WindowManager
    xlat.py                  thin Python wrappers over the xlat binary
    terminal.py              Terminal launcher
    workloads.py             generators + workload table + in-terminal payload side
    rfb.py                   RFB client (stats + end-to-end key latency)
    x11proxy.py              X11StreamParser + X11Proxy
    metrics.py               proc CPU, summarize, DamageWatch
    runner.py                PRESETS, run_one, run_preset
    report.py                compare, render_markdown
    diag.py                  collect, scrub
    live.py                  live_latency, live_watch
  make-live-bundle           builds dist/xtrp-live.tar.gz for real targets
  tests/                     unittest modules (one per xtrp module + test_policy.py)
docs/LIVE.md                 how a user runs diag/live on a real VM
results/summary/             committed, scrubbed summaries
```

---

### Task 1: Bench container image

**Files:**
- Create: `bench/Dockerfile`, `bench/container`, `bench/pins.json`, `bench/selftest-image`

**Interfaces:**
- Produces: `bench/container <cmd...>`. It builds image `xtrp-bench` if needed, then runs
  `docker run --rm --init --network none -v <repo>:/work -w /work --user <uid>:<gid> xtrp-bench <cmd...>`.
  Use `--network host` only when `XTRP_NET=1`, for image builds or pin refreshes. Inside the image:
  `/usr/bin/xfce4-terminal` (baseline), `Xvfb`, `Xvnc`, `mutter`, `marco`, `xdotool`, `xprop`, `xdpyinfo`,
  `dbus-run-session`, `/opt/nvim/bin/nvim`, `/usr/local/bin/tmux`, and fonts "CaskaydiaCove Nerd Font Mono"
  + "DejaVu Sans Mono".

- [ ] **Step 1: Write `bench/selftest-image`** (sh). It runs inside the container and exits non-zero
  on the first failure:
  - `rpm -q xfce4-terminal` prints `xfce4-terminal-1.0.4-1.el8.x86_64`;
  - `rpm -q vte291` starts with `vte291-0.52.4`;
  - `command -v` succeeds for each tool listed under Produces;
  - `/opt/nvim/bin/nvim --version | head -1` reports v0.11 or newer;
  - `tmux -V` prints `tmux 3.5a`;
  - `fc-list` has both font families;
  - `python3 -c 'import sys; assert sys.version_info[:2] == (3, 6)'` passes.

- [ ] **Step 2: Run it to verify it fails** (no image yet)

Run: `XTRP_NET=1 bench/container bench/selftest-image`
Expected: the image build fails (no Dockerfile).

- [ ] **Step 3: Write `bench/Dockerfile` and `bench/pins.json`**

  Base is `FROM almalinux:8.10`. Enable `epel-release` and `powertools`. Install with dnf:

  | Group | Packages |
  |---|---|
  | Baseline terminal | `xfce4-terminal-1.0.4-1.el8`, `vte291` |
  | X servers and tools | `xorg-x11-server-Xvfb`, `tigervnc-server-minimal`, `xdotool`, `xorg-x11-utils`, `xorg-x11-xauth` |
  | Window managers | `mutter`, `marco` |
  | GL and D-Bus for mutter | `mesa-dri-drivers` (llvmpipe), `dbus-daemon`, `dbus-tools` |
  | Fonts | `dejavu-sans-mono-fonts`, `fontconfig` |
  | Python | `python36` |
  | Helper build | `gcc`, `libX11-devel`, `libXtst-devel`, `libXdamage-devel`, `libXfixes-devel`, `libXext-devel` |
  | tmux build | `libevent-devel`, `ncurses-devel` |
  | Misc | `procps-ng`, `unzip`, `xz`, `bzip2`, `diffutils` |

  Then add three pinned artifacts, each with its URL and sha256 recorded in `pins.json` and checked with
  `sha256sum -c` during the build:
  - nvim current stable from `github.com/neovim/neovim-releases`, extracted to `/opt/nvim`. This is the
    glibc-2.17 build. The official `neovim/neovim` tarball needs a newer glibc than EL8's 2.28.
    `selftest-image` proves it runs;
  - tmux 3.5a source, built with `./configure --prefix=/usr/local && make && make install`;
  - nerd-fonts `CascadiaCode.zip` (CaskaydiaCove), installed to `/usr/share/fonts/caskaydia`, then
    `fc-cache -f`.

  `bench/container` derives the repo root from `$0` and builds quietly (`docker build -q`). It sets
  `-e HOME=/tmp/xtrp-home`, and passes through an interactive TTY only when stdin and stdout are TTYs.

- [ ] **Step 4: Run selftest to verify it passes**

Run: `XTRP_NET=1 bench/container true && bench/container bench/selftest-image`
Expected: prints `selftest-image: OK`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add bench/Dockerfile bench/container bench/pins.json bench/selftest-image
git commit -m "bench: EL8 bench image with baseline terminal, X servers, WMs, nvim, tmux, fonts"
```

---

### Task 2: `xlat` helper + `testwin`

**Files:**
- Create: `bench/helpers/xlat.c`, `bench/helpers/testwin.c`, `bench/helpers/build.sh`, `bench/xtrp/__init__.py`,
  `bench/xtrp/xlat.py`, `bench/tests/test_xlat.py`
- Test helper: `bench/tests/xenv.py` provides:
  - `XvfbFixture(unittest.TestCase)`, whose `setUp`/`tearDown` start and stop Xvfb. Until Task 3 exists it
    does this directly; Task 3 swaps in `XServer`. It exposes `.display`, plus
    `.start_testwin(title, delay_ms, rect, damage_forever=False) -> int window` and
    `.stop_testwin(window) -> dict`, the JSON testwin prints on SIGTERM.
  - `pid_alive(pid) -> bool`.

**Interfaces:**
- Produces (CLI; every output line is one JSON object; all times are CLOCK_MONOTONIC ns):
  - `xlat info` → `{"vendor":str,"release":int,"extensions":[str],"wm_name":str|null,"frame_drawn":bool,
    "cm_owner":bool,"depth":int,"width":int,"height":int,"rtt_us_median":float}`.
    `rtt_us_median` is the median of 20 `XGetInputFocus` round trips. `cm_owner` means
    `_NET_WM_CM_S<screen>` has an owner. `frame_drawn` means `_NET_SUPPORTED` contains `_NET_WM_FRAME_DRAWN`.
  - `xlat wait-window --title T --timeout-ms N` polls every 5 ms for a viewable window whose `_NET_WM_NAME`
    or `WM_NAME` equals T. It prints `{"window":int,"t_ns":int}`, or exits 3 on timeout.
  - `xlat focus --window W` calls `XSetInputFocus` and `XSync`, then exits 0.
  - `xlat latency --window W --samples N --interval-ms M --timeout-ms T [--require-focus]`:
    - It alternates the keys `a` and `BackSpace`. Each sample is XTest press+release, then `XFlush`, then
      waiting for the first `DamageNotify` on W (`XDamageReportRawRectangles`). It prints
      `{"i":k,"inject_ns":int,"damage_ns":int|null}` per sample.
    - With `--require-focus`, if `XGetInputFocus` is not W (or an ancestor/descendant of it), it prints
      `{"error":"not-focused"}` and exits 2 *before* injecting anything.
  - `xlat damage --window W` prints `{"t_ns":int,"x":int,"y":int,"w":int,"h":int}` per raw damage rectangle
    until SIGTERM/SIGINT, then exits 0.
  - `xlat pick` grabs the pointer, waits for a click, and prints the client window (the one with `WM_STATE`)
    as `{"window":int}`.
  - `testwin --title T --delay-ms D --rect WxH [--damage-forever]`:
    - It maps a 400×300 window titled T.
    - On each KeyPress it waits D ms, then fills a WxH rect in alternating black and white.
    - With `--damage-forever` it fills a 10×10 rect every 50 ms regardless of input.
    - On SIGTERM it prints `{"keys":count}` and exits.
- Produces (Python, `bench/xtrp/xlat.py`):
  - `XLAT = <repo>/bench/helpers/bin/xlat`;
  - `run_json(args: list, display: str, timeout_s: float) -> list[dict]`;
  - `info(display) -> dict`;
  - `wait_window(display, title, timeout_ms=15000) -> (int window, float t_s)`;
  - `focus(display, window) -> None`;
  - `latency(display, window, samples, interval_ms=120, timeout_ms=2000, require_focus=False) -> list[float|None]`
    (milliseconds; raises `xlat.NotFocusedError` on exit 2; `class NotFocusedError(RuntimeError)`).

- [ ] **Step 1: Write failing tests** in `bench/tests/test_xlat.py`, using `XvfbFixture` (Xvfb `:50`–`:99`,
  1024x768x24):

```python
def test_latency_matches_testwin_delay(self):
    win = self.start_testwin(title="tw", delay_ms=30, rect="50x20")
    xlat.focus(self.display, win)
    ms = xlat.latency(self.display, win, samples=10)
    self.assertEqual(len(ms), 10)
    self.assertTrue(all(v is not None and 30.0 <= v <= 60.0 for v in ms), ms)

def test_require_focus_refuses_and_injects_nothing(self):
    win = self.start_testwin(title="tw2", delay_ms=0, rect="10x10")
    other = self.start_testwin(title="other", delay_ms=0, rect="10x10")
    xlat.focus(self.display, other)
    with self.assertRaises(xlat.NotFocusedError):
        xlat.latency(self.display, win, samples=3, require_focus=True)
    self.assertEqual(self.stop_testwin(win)["keys"], 0)

def test_info_reports_no_wm_on_bare_xvfb(self):
    i = xlat.info(self.display)
    self.assertIsNone(i["wm_name"]); self.assertFalse(i["cm_owner"])
    self.assertIn("DAMAGE", i["extensions"]); self.assertGreater(i["rtt_us_median"], 0)

def test_damage_reports_rect_area(self):  # testwin --damage-forever, 1 s -> >= 15 rects, each 10x10
    ...
```

- [ ] **Step 2: Run to verify they fail**

Run: `bench/container python3 -m unittest -v tests.test_xlat` (with `-t bench -s bench/tests` per Global Constraints)
Expected: FAIL/ERROR. The `xlat` binary is missing.

- [ ] **Step 3: Implement `xlat.c`, `testwin.c`, `build.sh`, `xlat.py`**

  `build.sh` compiles both programs with `-O2 -Wall -Werror`, linking `-lX11 -lXtst -lXdamage -lXfixes -lXext`,
  into `bench/helpers/bin/`. Add `bench/helpers/bin/` to `.gitignore`. `xlat.py` runs `build.sh` once if the
  binary is missing.

- [ ] **Step 4: Run tests to verify they pass** (same command). Expected: 4 tests OK.

- [ ] **Step 5: Commit**

```bash
git add bench/helpers bench/xtrp/__init__.py bench/xtrp/xlat.py bench/tests/test_xlat.py bench/tests/xenv.py .gitignore
git commit -m "bench: xlat X-side timing helper and testwin fixture"
```

---

### Task 3: X servers and window managers

**Files:**
- Create: `bench/xtrp/display.py`, `bench/tests/test_display.py`
- Modify: `bench/tests/xenv.py` (`XvfbFixture` delegates to `XServer("xvfb")`)

**Interfaces:**
- Consumes: `xlat.info`
- Produces:
  - `class XServer(kind: str, width: int = 1920, height: int = 1080, depth: int = 24)`
    - `kind` is `"xvfb"` or `"xvnc"`. Context manager with `.start()`/`.stop()`.
    - Attributes: `.display` (`":N"`), `.number`, `.pid`, `.rfb_port` (`5900+N` for xvnc, else `None`).
    - It picks the first N in 50..99 with no `/tmp/.XN-lock` and no `/tmp/.X11-unix/XN`. It is ready when
      `xlat info` succeeds (10 s cap).
    - Xvfb runs as `Xvfb :N -screen 0 WxHxD -nolisten tcp -noreset`.
    - Xvnc runs as `Xvnc :N -geometry WxH -depth D -SecurityTypes None -rfbport P -nolisten tcp -AlwaysShared`.
    - `.stop()` sends SIGTERM, waits 5 s, then SIGKILL, and removes the lock and socket if they are left over.
  - `class WindowManager(name: str, display: str)`
    - `name` is one of `"none"`, `"mutter"`, `"marco-comp"`, `"marco-nocomp"`. Context manager.
    - mutter runs as `dbus-run-session -- mutter --x11 --replace --sm-disable`.
    - marco runs as `dbus-run-session -- marco --replace --composite|--no-composite`.
    - Ready when `xlat info` shows `wm_name` set, plus, for mutter and marco-comp, `cm_owner` true
      (15 s cap). Otherwise it raises `WmStartError`, including the WM's stderr tail.
  - `WM_NAMES = ("none", "mutter", "marco-comp", "marco-nocomp")`

- [ ] **Step 1: Write failing tests**

```python
def test_each_wm_reports_expected_compositing(self):
    expect = {"none": (None, False), "mutter": (True, True),
              "marco-comp": (True, True), "marco-nocomp": (True, False)}
    for name, (has_wm, cm) in expect.items():
        with self.subTest(wm=name), XServer("xvfb") as xs, WindowManager(name, xs.display):
            i = xlat.info(xs.display)
            self.assertEqual(i["wm_name"] is not None, bool(has_wm)); self.assertEqual(i["cm_owner"], cm)

def test_xvnc_exposes_rfb_port_and_vnc_extension(self):
    with XServer("xvnc") as xs:
        self.assertEqual(xs.rfb_port, 5900 + xs.number)
        self.assertIn("VNC-EXTENSION", xlat.info(xs.display)["extensions"])

def test_stop_leaves_no_lock_or_process(self):
    xs = XServer("xvfb"); xs.start(); n, pid = xs.number, xs.pid; xs.stop()
    self.assertFalse(os.path.exists("/tmp/.X%d-lock" % n)); self.assertFalse(pid_alive(pid))
```

- [ ] **Step 2: Run to verify they fail.** Expected: ImportError `xtrp.display`.
- [ ] **Step 3: Implement `display.py`.** Use one helper, `_spawn(argv, env) -> Popen`, with
  `start_new_session=True`, so `stop()` can `os.killpg` the whole group (dbus-run-session included).
- [ ] **Step 4: Run to verify they pass.** Expected: OK. If mutter cannot composite on Xvfb+llvmpipe, record
  the stderr in the task report and stop. That is a spec-level problem (mutter is a first-class target),
  not something to skip.
- [ ] **Step 5: Commit** — `git commit -m "bench: XServer (Xvfb/Xvnc) and WindowManager (mutter/marco) lifecycle"`

---

### Task 4: Terminal launcher, configs, and build registry

**Files:**
- Create: `bench/xtrp/model.py` (the `Build` part), `bench/builds.json`, `bench/conf/terminalrc.in`,
  `bench/xtrp/terminal.py`, `bench/tests/test_terminal.py`

**Interfaces:**
- Produces:
  - `class Build(name: str, exec_path: str, env: dict)`.
  - `load_builds(path="bench/builds.json") -> dict`. Initial content:
    `{"baseline": {"exec": "/usr/bin/xfce4-terminal", "env": {}}}`.
  - `SIZES = {"small": "120x40", "large": "236x62"}`.
  - `FONTS = {"caskaydia": "CaskaydiaCove Nerd Font Mono 12", "dejavu": "DejaVu Sans Mono 12"}`.
  - `class Terminal(build: Build, display: str, size: str, font: str, command: list, workdir: str, env: dict = None)`
    - `.start(timeout_s=15)` sets `.window` (int), `.pid`, and `.startup_ms`, and returns `self`.
      `startup_ms` is the time from `Popen` to `wait_window`.
    - `.stop()` kills the process group; it is idempotent. Context manager.
    - It writes `<workdir>/home/.config/xfce4/terminal/terminalrc` from the template and runs with
      `HOME=<workdir>/home`, `XDG_CONFIG_HOME=<workdir>/home/.config`, `NO_AT_BRIDGE=1`, no
      `DBUS_SESSION_BUS_ADDRESS`, and `DISPLAY=display`.
    - argv: `[exec, "--disable-server", "--geometry", SIZES[size], "--title", title, "--hide-menubar",
      "--hide-toolbar", "-x"] + command`, where `title = "xtrp-<pid>-<counter>"`.
- `terminalrc.in` pins these keys (all from 1.0.4's rc blurbs):
  - `FontName=@FONT@`, `FontUseSystem=FALSE`, `FontAllowBold=TRUE`;
  - `MiscCursorBlinks=FALSE`, `MiscBell=FALSE`, `MiscConfirmClose=FALSE`, `MiscShowUnsafePasteDialog=FALSE`;
  - `MiscMenubarDefault=FALSE`, `MiscToolbarDefault=FALSE`, `MiscBordersDefault=TRUE`;
  - `ScrollingBar=TERMINAL_SCROLLBAR_NONE`, `ScrollingLines=1000`, `TitleMode=TERMINAL_TITLE_HIDE`;
  - `ColorForeground=#ffffff`, `ColorBackground=#000000`;
  - `ColorPalette=` the loadout seed palette (copy the 16 `rgb(...)` entries from the spec's source
    `envs/xfce4-terminal/xfce4-terminal.xml` in engineering-loadout).

- [ ] **Step 1: Write failing tests**

```python
def test_baseline_maps_titled_window_and_stops_cleanly(self):
    with XServer("xvfb") as xs, Terminal(load_builds()["baseline"], xs.display, "small", "dejavu",
                                         ["sleep", "60"], self.tmp) as t:
        self.assertGreater(t.window, 0); self.assertLess(t.startup_ms, 15000)
        pid = t.pid
    self.assertFalse(pid_alive(pid))

def test_rc_file_carries_font_and_blink_off(self):
    ...  # after start: read terminalrc, assert "FontName=CaskaydiaCove Nerd Font Mono 12" and "MiscCursorBlinks=FALSE"
```

- [ ] **Step 2: Run to verify they fail.** Expected: ImportError.
- [ ] **Step 3: Implement.** The window title is the stable handle. `TitleMode=TERMINAL_TITLE_HIDE` stops
  workloads from changing it.
- [ ] **Step 4: Run to verify they pass.**
- [ ] **Step 5: Commit** — `git commit -m "bench: terminal launcher with pinned 1.0.4 rc and build registry"`

---

### Task 5: Workloads (generators, configs, in-terminal payload side)

**Files:**
- Create: `bench/xtrp/workloads.py`, `bench/xtrp/__main__.py` (the `workload` subcommand only),
  `bench/conf/nvim/init.lua`, `bench/conf/tmux.conf`, `bench/tests/test_workloads.py`, `bench/tests/test_policy.py`

**Interfaces:**
- Produces:
  - Generators, deterministic for a given `seed`, each yielding `bytes` chunks of at most 64 KiB:
    - `gen_bulk_ascii(n_bytes, seed=1)`: printable ASCII lines, 40–200 columns.
    - `gen_sgr(n_bytes, seed=1)`: every run of 1–8 chars carries a 256-colour or truecolour SGR, plus
      bold/italic/underline.
    - `gen_unicode(n_bytes, seed=1)`: mixes CJK (wide), combining marks, emoji, and Nerd Font PUA
      (U+E0A0–U+E0D4, U+F000–U+F2E0).
    - `gen_box(n_bytes, seed=1)`: U+2500–U+259F tables and borders.
    - `gen_compile_log(n_lines, seed=1)`: gcc-like `path:line:col: warning: …` lines with occasional SGR.
    - `gen_source_file(n_lines=50000, seed=1) -> str`: a C-like file for nvim.
  - `WORKLOADS: dict[str, Workload]`, where `Workload(name, kind, command(ctx) -> list, timeout_s)`.
    - `kind` is `"latency"` or `"throughput"`.
    - `ctx` carries `status_path`, `workdir`, `sync` (bool), `cols`, and `rows`.
  - Workload names (exactly these 11):
    - latency: `shell-echo`, `nvim-type`, `tmux-type`;
    - throughput: `bulk-ascii`, `sgr-color`, `unicode`, `box-drawing`, `compile-log`, `fullscreen-redraw`,
      `nvim-scroll`, `tmux-bulk-split`.
  - Payload side: `python3 -m xtrp workload <name> --status <path> [--bytes N]` writes the payload to stdout
    (the pty). It appends to the status file:
    - `{"event":"start","t":float}`;
    - then `{"event":"end","t":float,"bytes":int,"term_cpu_s":float}`, where `term_cpu_s` is the CPU delta
      of the nearest ancestor process whose comm starts with `xfce4-termina` (from `/proc/<pid>/stat`).
    - Then it sleeps forever, so the window stays put until the runner stops it.
  - Byte and duration defaults:
    - `bulk-ascii`, `sgr-color`, `unicode`, `box-drawing`: 50 MiB (`--bytes` overrides; the smoke preset
      uses 5 MiB);
    - `compile-log`: 200k lines;
    - `fullscreen-redraw`: alternate screen, full repaint at 60 fps for 5 s;
    - `nvim-scroll`: `init.lua`'s `XtrpScroll(2000)`, which does `<C-e>` + `redraw` per step;
    - `tmux-bulk-split`: `tmux -L xtrp-<pid> -f bench/conf/tmux.conf`, two panes, bulk-ascii 20 MiB in the
      left pane, `cat` idle in the right;
    - latency workloads run an idle reader. `shell-echo` runs `bash --norc --noprofile -i` with `PS1='$ '`.
      `nvim-type` runs nvim in insert mode. `tmux-type` runs `cat` inside tmux.
  - `ctx.sync` → `XTRP_SYNC=1`. `init.lua` then sets `termsync`, and `tmux.conf` sources
    `set -as terminal-features ',xterm-256color:sync'` via `if-shell '[ "$XTRP_SYNC" = 1 ]'`.
  - `tmux.conf`: `status-interval 0`, `set-titles off`, `default-terminal screen-256color`.
  - `init.lua`: `notitle`, `number`, `cursorline`, `syntax on`, a fixed statusline, and no plugins.

- [ ] **Step 1: Write failing tests**

```python
def test_generators_are_deterministic_and_exact_size(self):
    for gen in (gen_bulk_ascii, gen_sgr, gen_unicode, gen_box):
        a = b"".join(gen(1 << 20, seed=7)); b = b"".join(gen(1 << 20, seed=7))
        self.assertEqual(a, b); self.assertEqual(len(a), 1 << 20)
        a.decode("utf-8")  # never splits a code point at the size boundary

def test_bulk_ascii_is_printable_ascii_lines(self):
    data = b"".join(gen_bulk_ascii(1 << 18))
    self.assertTrue(all(32 <= c < 127 or c == 10 for c in data))

def test_workload_table_is_exactly_the_eleven(self):
    self.assertEqual(sorted(WORKLOADS), sorted([...the 11 names...]))

def test_payload_writes_start_and_end_status(self):  # run `xtrp workload bulk-ascii --bytes 65536` with stdout to /dev/null
    ...  # status file has a start then an end event, end.t >= start.t, bytes == 65536
```

  `test_policy.py` scans every file under `bench/` for `tmux` invocations. It asserts each one passes `-L`, and
  that no `kill-server` appears without `-L xtrp-`.

- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement.** Keep the generators pure (`random.Random(seed)`). Truncate the final chunk on a
  UTF-8 boundary, padding with ASCII to reach the exact size.
- [ ] **Step 4: Run to verify they pass.**
- [ ] **Step 5: Commit** — `git commit -m "bench: deterministic workloads, nvim/tmux configs, tmux socket policy test"`

---

### Task 6: RFB client and X11 proxy

**Files:**
- Create: `bench/xtrp/rfb.py`, `bench/xtrp/x11proxy.py`, `bench/tests/test_rfb.py`, `bench/tests/test_x11proxy.py`

**Interfaces:**
- Produces (`rfb.py`):
  - `class RfbClient(host: str, port: int, encodings: list)`
    - `encodings` holds names from `{"tight", "zrle", "copyrect", "raw"}`. Never request Cursor or JPEG
      quality pseudo-encodings.
    - `.connect()`: RFB 3.8 handshake, security None, ClientInit shared=1, SetPixelFormat 32bpp/depth 24
      true-colour little-endian, SetEncodings.
    - `.start()` starts a background reader that keeps exactly one incremental FramebufferUpdateRequest
      outstanding.
    - `.reset_stats()`; `.stats() -> {"bytes":int, "updates":int, "rects":{enc:int}, "copyrect_area":int}`.
    - `.key_roundtrip_ms(keysym, timeout_s=2.0) -> float|None` sends KeyEvent down and up, then returns the
      time until the next complete update with ≥1 non-pseudo rect.
    - `.close()`.
  - `parse_rect_payload(enc: int, w: int, h: int, read: callable) -> int` returns the bytes consumed. The
    rules:

    | Encoding | Payload size |
    |---|---|
    | Raw | w·h·4 |
    | CopyRect | 4 |
    | ZRLE | 4-byte big-endian length + data |
    | LastRect (−224), DesktopSize (−223) | 0; LastRect ends the update early |

    Tight is decoded from its control byte:
    - fill: 3-byte TPIXEL.
    - basic compression with an optional filter byte:
      - palette: 1-byte count−1 + count·3 TPIXEL bytes; data bpp is 1 bit if count ≤ 2, else 8;
      - copy and gradient: 24 bits per pixel.
    - Raw data length is `ceil(w·bpp/8)·h`. Under 12 bytes it is read raw; otherwise it is a compact length
      (1–3 bytes, 7 bits each) + zlib data.
    - JPEG never appears, because no quality level is requested; if it does, raise `RfbProtocolError`.
- Produces (`x11proxy.py`):
  - `class X11StreamParser(hide_shm: bool = True)`
    - `.feed_c2s(data: bytes) -> bytes` and `.feed_s2c(data: bytes) -> bytes` return the bytes to forward.
    - `.stats -> {"c2s_bytes","s2c_bytes","requests":{name:int},"replies","events","errors","image_bytes"}`.
    - Client side: the setup is 12 bytes + padded auth name and data. Requests are
      `[major, minor, len16]` units of 4 bytes; `len16 == 0` means BIG-REQUESTS, with a 32-bit length next.
      Sequence numbers increment per request.
    - Extension majors are learned from QueryExtension (opcode 98) replies, which are matched by sequence.
      Names are `core:<Name>` for core opcodes and `<EXT>:<minor>` for extensions.
    - Server side: the setup reply is 8 bytes + 4·len. Errors and events are 32 bytes. Replies (type 1) and
      GenericEvent (35) are 32 + 4·len32@4.
    - `image_bytes` sums core PutImage(72), `MIT-SHM` minor 3, and `RENDER` AddGlyphs (minor 20) request
      sizes.
    - `hide_shm=True` rewrites byte 8 (`present`) to 0 in the reply to a QueryExtension whose name was
      `MIT-SHM`.
  - `class X11Proxy(upstream_display: str, rtt_ms: float = 0.0, bw_mbps: float = None, hide_shm: bool = True)`
    - `.start() -> str` returns the proxy's DISPLAY (`"localhost:M"`, listening on TCP 6000+M, with M picked
      free in 150..199).
    - `.stop()`; `.stats()` merges all connections.
    - One selector thread. Every forwarded chunk is held `rtt_ms/2` in each direction (a min-heap keyed by
      release time). `bw_mbps`, if set, is a token bucket per direction.

- [ ] **Step 1: Write failing unit tests** (no X needed)

```python
def test_zrle_copyrect_raw_accounting(self):   # fake RFB server thread sends one update: ZRLE(len=100) + CopyRect + Raw 2x2
    st = client.stats()
    self.assertEqual(st["rects"], {"zrle": 1, "copyrect": 1, "raw": 1})
    self.assertEqual(st["copyrect_area"], 64 * 32)

def test_tight_palette_small_raw_and_compact_length(self):
    # 2-colour palette rect 8x1 -> 1 byte raw (<12, no length); 16x16 copy-filter -> compact length 0x81 0x01 (129) + 129 bytes
    ...

def test_big_requests_length_and_opcode_names(self):
    p = X11StreamParser(); p.feed_c2s(SETUP_LE); p.feed_s2c(SETUP_REPLY_LE)
    p.feed_c2s(core_request(72, extra_words=0, big=True, big_len=5000))  # PutImage via BIG-REQUESTS
    self.assertEqual(p.stats["requests"]["core:PutImage"], 1); self.assertEqual(p.stats["image_bytes"], 5000 * 4)

def test_mit_shm_hidden(self):
    p = X11StreamParser(hide_shm=True)  # QueryExtension("MIT-SHM") seq 1 -> reply present=1 rewritten to 0
    out = p.feed_s2c(query_extension_reply(seq=1, present=1, major=130))
    self.assertEqual(out[8], 0)

def test_split_feeds_parse_identically(self):   # same stream fed 1 byte at a time -> identical stats
    ...
```

- [ ] **Step 2: Write failing integration tests** (container):
  - Proxy with `rtt_ms=20` in front of Xvfb: `xlat latency` against a `testwin` launched with
    `DISPLAY=<proxy>` must be ≥ 20 ms with `delay_ms=0`.
  - `xdpyinfo -display <proxy>` exits 0, and `stats()["replies"] > 0`.
  - The RFB client against Xvnc: `key_roundtrip_ms` on a focused `testwin` (`delay_ms=0`) returns a float
    under 500. `stats()["bytes"] > 0` after 5 key presses.
- [ ] **Step 3: Run all to verify they fail.**
- [ ] **Step 4: Implement both modules.** Keep the parsers pure; sockets live only in `RfbClient` and
  `X11Proxy`.
- [ ] **Step 5: Run to verify they pass.**
- [ ] **Step 6: Commit** — `git commit -m "bench: RFB client with encoding accounting; counting/delaying X11 proxy"`

---

### Task 7: Metrics, run records, and the matrix runner

**Files:**
- Create: `bench/xtrp/metrics.py`, `bench/xtrp/runner.py`, `bench/tests/test_metrics.py`, `bench/tests/test_runner.py`
- Modify: `bench/xtrp/model.py` (add `RunKey` and record I/O), `bench/xtrp/__main__.py` (add `run`)

**Interfaces:**
- Consumes: `XServer`, `WindowManager`, `Terminal`, `WORKLOADS`, `RfbClient`, `X11Proxy`, `xlat.*`
- Produces:
  - `proc_cpu_s(pid) -> float` (utime + stime of the whole process).
  - `summarize(values) -> {"n","median","p10","p90"}` (`None`s dropped; percentiles use linear interpolation
    between closest ranks, i.e. numpy's default).
  - `class DamageWatch(display, window)`: `.start()`; `.wait_quiet(quiet_ms=300, cap_s=10.0) -> bool`
    (False means the cap was hit); `.stop() -> {"events":int,"area_px":int}`.
  - `RunKey(build, display_kind, wm, rtt_ms, vnc_encoding, size, font, variant, workload)`:
    - `display_kind` is one of `"xvfb"`, `"xvnc"`, `"xvnc+x11remote"`.
    - `rtt_ms` is `None` unless `display_kind` is x11remote.
    - `vnc_encoding` is `"tight"` or `"zrle"` on xvnc kinds, else `None`.
    - `variant` is `"default"` or `"sync"`; `"sync"` sets `ctx.sync=True`. Plan 1 presets use only
      `"default"`; Plan 3 adds `sync`, `at-spi`, and the font-rendering variants.
  - Run record (schema 1) = `{"schema":1, "key":{RunKey fields}, "iteration":int, "host":{"xlat_info":…},
    "metrics":{…}, "flags":{"drain_timeout":bool,"errors":[str]}}`. Metrics present depend on the workload:
    - all workloads: `startup_ms`, `term_cpu_s`, `xserver_cpu_s`, `damage_events`, `damage_area_px`;
    - latency: `latency_ms` (list, 40 samples, interval 120 ms);
    - latency on xvnc: also `e2e_latency_ms` (list, 20 samples);
    - throughput: `elapsed_s` (end − start from the status file), `drain_s` (end → quiet), `throughput_mb_s`;
    - xvnc: also `vnc_bytes`, `vnc_updates`, `vnc_rects`, `vnc_copyrect_area`. Run Tight; a `zrle` variant
      is selected by preset.
    - x11remote: also `x11_c2s_bytes`, `x11_s2c_bytes`, `x11_replies`, `x11_requests`, `x11_image_bytes`,
      and `startup_x11_replies`, a proxy stats snapshot taken when `wait_window` returns.
  - `write_record(out_dir, rec) -> str` writes `<out_dir>/<sha1(key)>-<iteration>.json`.
    `load_records(dir) -> list`.
  - `PRESETS` (each lists `displays`, `wms`, `sizes`, `fonts`, `workloads`, `iterations`, `rtts`, `vnc_encodings`):
    - `smoke`: xvfb / none / small / dejavu / [shell-echo, bulk-ascii at 5 MiB] / 1 iteration.
    - `quick`: xvnc (tight) / mutter / large / caskaydia / all 11 / 3 iterations.
    - `full`: displays [xvfb, xvnc, xvnc+x11remote with rtts [0.25]] × wms (all 4) × large × caskaydia × all 11
      × 7 iterations. xvnc kinds use vnc_encodings [tight, zrle]. Plus a sensitivity block: xvnc (tight) /
      mutter / sizes × fonts × all 11 × 5 iterations.
    - `rtt-sweep`: xvnc+x11remote (tight) with rtts [0, 0.25, 2, 20] / mutter / large / caskaydia /
      [shell-echo, nvim-type, nvim-scroll, bulk-ascii] × 5 iterations.
  - `run_preset(preset, builds: list, out_dir, iterations=None) -> int` returns the number of records
    written. One X server + WM per (display, wm) group is reused across workloads and iterations. A fresh
    terminal is started per run. The pointer is parked at (0, 0) before measuring. Any exception in one run
    is recorded in `flags.errors`, and the matrix continues.
  - CLI: `python3 -m xtrp run --preset P --build baseline [--build …] --out results/raw/<stamp>`.

- [ ] **Step 1: Write failing tests**

```python
def test_summarize(self):
    self.assertEqual(summarize([3, 1, 2, None]), {"n": 3, "median": 2, "p10": 1.2, "p90": 2.8})

def test_drain_timeout_is_flagged_not_hung(self):  # DamageWatch on testwin --damage-forever, cap 1 s
    t0 = time.monotonic(); self.assertFalse(dw.wait_quiet(quiet_ms=300, cap_s=1.0))
    self.assertLess(time.monotonic() - t0, 2.0)

def test_smoke_preset_writes_valid_records(self):
    n = run_preset("smoke", ["baseline"], self.out)
    recs = load_records(self.out); self.assertEqual(n, 2); self.assertEqual(len(recs), 2)
    echo = [r for r in recs if r["key"]["workload"] == "shell-echo"][0]
    self.assertEqual(len(echo["metrics"]["latency_ms"]), 40)
    self.assertTrue(all(0 < v < 1000 for v in echo["metrics"]["latency_ms"]))
    bulk = [r for r in recs if r["key"]["workload"] == "bulk-ascii"][0]
    self.assertGreater(bulk["metrics"]["throughput_mb_s"], 0); self.assertFalse(bulk["flags"]["errors"])

def test_sigint_mid_matrix_leaves_nothing_running(self):
    # start `python3 -m xtrp run --preset smoke` in its own session, wait for "run 1/" on stderr, send SIGINT;
    # afterwards: no Xvfb/xfce4-terminal/tmux process in that session, no /tmp/.X5?-lock left behind
    ...
```

- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement `metrics.py`, `runner.py`, and the record I/O.** Cleanup is a `contextlib.ExitStack`
  per group and per run. A SIGINT/SIGTERM handler raises `KeyboardInterrupt` so every `__exit__` runs.
- [ ] **Step 4: Run to verify they pass.**
- [ ] **Step 5: Commit** — `git commit -m "bench: metrics, schema-1 run records, preset matrix runner"`

---

### Task 8: Report

**Files:**
- Create: `bench/xtrp/report.py`, `bench/tests/test_report.py`
- Modify: `bench/xtrp/__main__.py` (add `report`)

**Interfaces:**
- Consumes: `load_records`, `summarize`
- Produces:
  - `METRIC_DIRECTION`: `+1` (higher is better) for `throughput_mb_s`; `-1` for every other numeric metric.
    List metrics are summarized first.
  - `compare(base, cand, threshold_pct=5.0) -> list[Row]`. Rows are grouped by the RunKey minus `build`, plus
    the metric name.
    - Each row is `{"key","metric","base":summary,"cand":summary,"delta_pct","noise_pct","regression"}`.
    - `delta_pct` is positive when the candidate is better.
    - `noise_pct = 100·(p90−p10)/median` of the baseline.
    - `regression = delta_pct < −max(threshold_pct, noise_pct)`.
    - Keys present on only one side produce a row with `regression: False` and `note: "missing in base|cand"`.
  - `render_markdown(rows) -> str`: one table per `(display_kind, wm, rtt_ms)`, with columns workload, metric,
    base median, cand median, Δ%, noise%, and flag. Regressions are listed first in a summary block.
  - CLI: `python3 -m xtrp report BASE_DIR CAND_DIR [--threshold 5] [--out file.md]`. It exits 1 if any row
    regressed.

- [ ] **Step 1: Write failing tests** with synthetic records:
  - latency 10 → 12 ms is a regression at 0% noise;
  - latency 10 → 10.4 ms is not;
  - throughput 100 → 90 is a regression;
  - noise 30% suppresses a −20% delta;
  - a missing key gets a note and no flag;
  - the markdown contains the regression summary first.
- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run to verify they pass.**
- [ ] **Step 5: Commit** — `git commit -m "bench: baseline-vs-candidate report with noise-aware regression flag"`

---

### Task 9: `diag`, `live`, and the live bundle

**Files:**
- Create: `bench/xtrp/diag.py`, `bench/xtrp/live.py`, `bench/make-live-bundle`, `docs/LIVE.md`, `bench/tests/test_diag.py`,
  `bench/tests/test_live.py`
- Modify: `bench/xtrp/__main__.py` (add `diag`, `live`)

**Interfaces:**
- Consumes: `xlat.info`, `xlat.latency`, `DamageWatch`, `summarize`
- Produces:
  - `collect() -> dict` with these sections:
    - `xlat_info`;
    - `display_transport`: `"unix"` or `"tcp"`, derived from `$DISPLAY` (host part present and not `unix`);
      the host itself is never stored;
    - `fonts`: `fc-match` for both bench font names and for `monospace`;
    - `font_rendering`: `gsettings get` for `org.gnome.desktop.interface font-antialiasing/font-hinting/font-rgba-order`
      and `org.mate.font-rendering antialiasing/hinting/rgba-order` (missing schemas recorded as null);
    - `xft`: Xft settings from `xrdb -query`;
    - `packages`: `rpm -q` of `vte291`, `gtk3`, `xfce4-terminal`, `mutter`, `marco`, `tigervnc-server-minimal`,
      `gnome-shell`;
    - `session`: `XDG_SESSION_TYPE`, `XDG_CURRENT_DESKTOP`, `DESKTOP_SESSION`;
    - `cpu`: `nproc` and the `/proc/cpuinfo` model name.
  - `scrub(obj, extra_terms=()) -> obj` deep-copies and replaces:
    - the local hostname, short and FQDN, and any token matching `[A-Za-z0-9-]+(\.[A-Za-z0-9-]+){2,}` →
      `<host>`;
    - `getpass.getuser()` and `$USER` → `<user>`;
    - IPv4 and IPv6 literals → `<ip>`;
    - absolute paths under `/home/`, `/vols/`, `/proj/`, `/net/`, `/nfs/` → `<path>`;
    - every `extra_terms` entry → `<redacted>`.
    `collect()` output always passes through `scrub` before printing.
  - `live_latency(window=None, pick=False, samples=40) -> dict`. It requires focus and refuses otherwise. It
    returns `{"latency_ms": summary, "raw": [...]}`.
  - `live_watch(window, seconds) -> {"damage_events","damage_area_px","xserver_cpu_s"|null}`.
    `xserver_cpu_s` is non-null only when the X server's pid is visible locally (`pgrep -x` of `Xvnc`, `Xorg`,
    `nxagent`, or `etx*`). Damage is recorded while the user runs a workload in that terminal.
  - CLI:
    - `python3 -m xtrp diag [--out f]`;
    - `python3 -m xtrp live latency [--window ID | --pick] [--samples N]`;
    - `python3 -m xtrp live watch --window ID --seconds S`.
    - `live` prints the instruction "focus the terminal, run `cat`, then press Enter here" and waits on stdin
      before injecting anything.
  - `bench/make-live-bundle` writes `dist/xtrp-live.tar.gz` containing `xtrp/`, a prebuilt `xlat` (built in the
    container), `conf/`, and a `run` sh wrapper (`/usr/bin/python3` or `/usr/libexec/platform-python`).
  - `docs/LIVE.md` gives the exact commands for T1 (on A) and T2 (terminal on B with `DISPLAY=A:n`, xtrp on A),
    and says what to paste back.

- [ ] **Step 1: Write failing tests**

```python
def test_scrub_removes_planted_site_identifiers(self):
    planted = {"vendor": "Xvnc on build7.eng.example.corp", "display": "build7.eng.example.corp:3",
               "path": "/vols/tools/x/bin/bash", "home": "/home/alice/x", "ip": "10.1.2.3", "v6": "fe80::1",
               "note": "job PROJ:261:AE:debug"}
    out = json.dumps(scrub(planted, extra_terms=["PROJ:261:AE:debug"]))
    for s in ("example.corp", "build7", "/vols/", "alice", "10.1.2.3", "fe80::1", "PROJ:261"):
        self.assertNotIn(s, out)

def test_collect_is_scrubbed_and_has_sections(self):  # on Xvfb
    d = collect(); self.assertIn("xlat_info", d); self.assertNotIn(socket.gethostname(), json.dumps(d))

def test_live_refuses_unfocused_window(self):  # testwin A focused, target B -> NotFocusedError, B saw 0 keys
    ...
```

- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement.** Also add `bench/tests/test_bundle.py`. It builds the bundle, extracts it into a
  fresh directory, and runs `./run diag` on Xvfb. The JSON must parse.
- [ ] **Step 4: Run to verify they pass.**
- [ ] **Step 5: Commit** — `git commit -m "bench: scrubbed diag, focus-guarded live mode, live bundle + LIVE.md"`

---

### Task 10: Baseline numbers and the first real-target checkpoint

**Files:**
- Create: `results/summary/2026-11-25-baseline.md` (date = run date), `results/summary/README.md`
- Modify: `README.md` (status line + how to run the harness)

- [ ] **Step 1: Run the noise check.** Run `quick` twice for the baseline:

Run: `bench/container sh -c 'python3 -m xtrp run --preset quick --build baseline --out results/raw/q1 && python3 -m xtrp run --preset quick --build baseline --out results/raw/q2 && python3 -m xtrp report results/raw/q1 results/raw/q2'`
Expected: exit 0, no regressions flagged. If any are flagged, fix the noise source first; Review Focus #4
is the likely cause. Do not raise the threshold.

- [ ] **Step 2: Run `full` and `rtt-sweep` for the baseline** (long; run it in the background):

Run: `bench/container python3 -m xtrp run --preset full --build baseline --out results/raw/base-full`, then the
same with `--preset rtt-sweep --out results/raw/base-rtt`.
Expected: records = matrix size. Every record has an empty `flags.errors`, or the errors are explained in the
summary.

- [ ] **Step 3: Write `results/summary/<date>-baseline.md`.** It covers:
  - the image pins;
  - per-WM and per-display medians for every workload;
  - the five biggest costs observed, which are Plan 3's ordering input;
  - anything surprising, for example the effect of mutter vs marco compositing on latency, or the RFB
    CopyRect count (expected 0 for VTE 0.52).
  Run its content through `scrub` before committing.

- [ ] **Step 4: Build the live bundle and request the first real-target checkpoint.**

Run: `bench/container bench/make-live-bundle`
Expected: `dist/xtrp-live.tar.gz` exists, and `test_bundle` passes. Then hand the user the bundle path and
`docs/LIVE.md`. Ask for `diag` + `live latency` + `live watch` on:
- T1: a GNOME Classic session and a MATE session, each under TigerVNC, NoMachine, and ETX;
- T2: one farm-node run.

- [ ] **Step 5: Run the whole test suite once more, then commit and push.**

Run: `bench/container python3 -m unittest discover -s bench/tests -t bench`
Expected: all OK.

```bash
git add results/summary README.md
git commit -m "results: EPEL 1.0.4 + VTE 0.52.4 baseline across Xvfb/Xvnc/x11-remote and mutter/marco"
git push
```
