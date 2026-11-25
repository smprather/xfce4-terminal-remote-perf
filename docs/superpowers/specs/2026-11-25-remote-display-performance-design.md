# xfce4-terminal remote-display performance — design

Date: 2026-11-25
Status: approved 2026-11-25
Working tree: this repository (github.com/smprather/xfce4-terminal-remote-perf; started from the
EPEL8 1.0.4 source drop, see `README.loadout`)
Delivery vehicle (later): the engineering-loadout repo (github.com/smprather/engineering-loadout;
`build/build-xfce4-terminal.sh`, payload `el8.x86_64.glibc2p28`)

## 1. Intent

Engineers use xfce4-terminal on RHEL 8.10 VMs that have no GPU. They reach those VMs
through remote-desktop servers: OpenText Exceed TurboX (ETX), NoMachine, and TigerVNC.
The terminal feels slow there. The goal is to make it measurably faster on two axes:

- **Latency**: the time from a keypress to the result being visible. This covers echo at a
  shell prompt, typing in nvim, and switching panes in tmux.
- **Bandwidth/throughput**: how much work and how many bytes it takes to scroll and
  redraw. This covers bulk output, nvim scrolling, full-screen redraws, and tmux pane
  traffic.

Speed is the whole point. The app stays xfce4-terminal 1.0.4, so users keep the tabs,
preferences, and look they know. Everything underneath it is open to change.

## 2. Display topologies (both are first-class)

- **T1, local to the RDP host.** System A is a RHEL 8.10 VM. It runs the remote-desktop server,
  the X server, the desktop, and xfce4-terminal. The terminal talks to the X server over a Unix
  socket (MIT-SHM is available). The server encodes framebuffer changes and sends them to the
  user's client.
- **T2, X client on another machine.** xfce4-terminal runs on system B, a compute-farm node.
  `DISPLAY` is set directly to `A:n`, which means plain X11 over TCP with no ssh in the path.
  Measured round-trip time from B to A is about 0.2–0.3 ms. Between
  B and A, raw X11 protocol travels with no MIT-SHM. Between A and the client, the remote-desktop
  encoder carries it as in T1.

Desktops on A: **GNOME Classic** (EL8's GNOME 3.32 with the mutter compositing WM) and **MATE**
(EPEL8's MATE 1.26 with the marco WM, compositing optional). Both are first-class. Xfce sessions
exist but are not a target.

T2 still has headway. At 0.25 ms per round trip, an individual X round trip is cheap. The cost
concentrates in three places:
- A's software X server, which has to render every drawing request on a GPU-less VM;
- the remote-desktop encoder on A;
- any per-frame wait. For example, GTK waiting for a compositor ack.

So for T2 the levers are drawing less (fewer bytes and requests, which means less X-server CPU on
A) and never stalling a frame on a round trip. The wire bytes themselves matter less on this LAN.
§7.5 helps T2 at least as much as T1, and §7.5e targets T2 specifically.

## 3. Goals, non-goals, anti-goals

Goals
- A repeatable measurement harness that runs inside the EL8 build container (and, in a reduced
  "live display" mode, on a real target VM without root), and produces baseline-vs-candidate tables.
- Replace EL8's libvte 0.52.4 (2018) with current upstream VTE (0.84.x) back-ported to EL8's
  GTK 3.22.30 / GLib 2.56, used by xfce4-terminal only.
- Add the remote-display features neither old nor current VTE has (§7.5).
- Detect the display environment at runtime and adapt on the fly (§7.5i). This covers the WM and
  compositor, the X server type, local vs remote X, and the measured round-trip time. No per-user
  tuning is required. Environment variables override the detection.
- Build xfce4-terminal 1.0.4 from source against it; keep its behaviour and preferences format.

Non-goals
- GPU/GL anything; GTK4; Wayland-native operation.
- Upgrading xfce4-terminal to 1.1/1.2 (blocked on libxfce4ui 4.18; see engineering-loadout HANDOFF 2026-10-12).
- Moving mate-terminal off VTE 0.52.4 (possible later; out of scope now).
- New terminal features unrelated to speed.

Anti-goals (a failure even if it "works")
- Any workload/metric in the harness regressing by more than 5% vs baseline (beyond run-to-run noise) without
  that trade-off being surfaced and accepted.
- Failing to start or render correctly on a stock RHEL/Alma 8.10 host (glibc 2.28, EL8 libstdc++,
  EL8 GTK 3.22) with only the loadout payload — the build-box-masking class.
- Visible look changes users did not approve (font smoothing, colours, cursor style/blink defaults).
- Screen corruption or hangs in nvim/tmux (e.g. a synchronized-update that never ends).
- Touching mate-terminal's behaviour (it keeps the shared `libvte-2.91.so.0` payload stem).
- Killing or reusing anyone's default tmux server in any test. Use private sockets only
  (`tmux -L <name>`); never `kill-server` on the default socket.
- Committing anything from a real site to this public repo before it is scrubbed. Scrub
  hostnames, usernames, IPs, paths, and job and project identifiers.

## 4. Constraints

- Everything that compiles or packages runs in the EL8 container (`engineering-loadout/build/build-shell`,
  image `loadout-build` = almalinux:8.10; gcc-toolset-14 installed, enabled via `loadout_enable_gcc_toolset`).
  Day-to-day editing and quick local experiments may happen on the CachyOS host, but no number that
  decides anything comes from the host.
- One el8 build serves both A (RHEL 8.10) and B (farm nodes).
- glibc 2.28 floor. C++ built with gcc-toolset-14 (its libstdc++_nonshared covers the newer bits; the result
  must load against EL8's system libstdc++ — verify GLIBCXX/CXXABI version needs with `objdump -T`).
- No tab characters in anything we write (spaces only; Makefile recipes excepted). Respect each file's
  existing indent width.
- New dependencies are allowed (EL can package them); prefer static/bundled for small ones.
- Target X servers we cannot run here: ETX and NoMachine. TigerVNC's `Xvnc` (EL8 `tigervnc-server-minimal`)
  and `Xvfb` run in the container.

## 5. Findings that shaped this design

From VTE 0.52.4 source (what ships today):
- Scrolling repaints. `vte.cc` `scroll_region()` just invalidates; the source comments that VTE "stopped
  moving window contents around on scrolling" long ago. Over VNC/NX/ETX every scroll is re-encoded pixels
  rather than a cheap copy.
- Update pacing is fixed timeouts (`vtedefines.hh`: DISPLAY 10 ms, UPDATE 15 ms, UPDATE_REPEAT 30 ms,
  MAX_PROCESS 100 ms, input chunk 8 KiB).

From VTE 0.84.1 source (current upstream):
- Still builds for GTK3, but needs GTK ≥ 3.24.0, GLib/GIO ≥ 2.72, g++ ≥ 12 (`gnu++23`), meson ≥ 1.3.2,
  liblz4 ≥ 1.9 (EL8 has 1.8.3), simdutf ≥ 6.2, fmt ≥ 11, fast_float (the last three as meson wraps in
  `subprojects/`).
- GTK 3.24-only API (event controllers/gestures) is confined to `src/widget.cc` (2,680 lines; 48 GTK3 blocks).
- GLib > 2.56 use is small: `GUri` (2.66) in 7 files incl. `vteproperties.cc`, `vteseq.cc`, the public
  `vteterminal.h` (termprop URI API that xfce4-terminal 1.0.4 does not call); `g_memdup2` (2.68) in one place.
  More will surface at compile time; that is expected.
- Redraw is driven by a frame-clock scheduler (`scheduler.cc`, `gtk_widget_add_tick_callback`).
- Synchronized output (DEC private mode 2026) is a stub: `vteseq.cc` "TODO: implement this!" (GNOME/vte#15).
- Scrolling still repaints (no copy path).
- GTK3 accessibility (`vteaccess.cc`) is built by default (`-Da11y`); it tracks text changes and is a
  known CPU cost when an AT-SPI bus is active.

From xfce4-terminal 1.0.4:
- ~18k lines of UI; 74 distinct VTE functions / 128 call sites. Per-update hooks: `contents-changed`
  (tab activity indicator), `window-title-changed`, `selection-changed`. Cursor blink defaults off
  (`misc-cursor-blinks` FALSE); the loadout seed sets `TextBlinkMode=NEVER`.
- xfce4-terminal 1.0.4 is known to build against modern VTE (Debian 12 ships it with VTE 0.70).

## 6. Approaches considered

- **A. Current VTE, back-ported to EL8 GTK 3.22 / GLib 2.56 — CHOSEN by the user.** All upstream engine
  work since 2018 (parser rewrite, frame-clock scheduling, SIMD UTF-8, lz4 scrollback); one toolkit in the
  process; cost is a back-port patch set to carry across VTE upgrades.
- B. Current VTE unmodified on a private GTK 3.24 + newer GLib stack. Easier VTE upgrades and closes the
  "GUI toolkits are inherited" gap, but a much larger build/payload and a second GTK on every host.
- C. Patch EL8's VTE 0.52.4 only. Smallest deploy change, but nothing cherry-picks across the C→C++ rewrite;
  low ceiling. Kept as the **baseline** for measurement.
- Dropped: a new engine or language. xfce4-terminal is welded to the VTE API, and every remote-display
  win below fits inside VTE.

## 7. Design

### 7.1 Workspace layout (this repository)

```
docs/superpowers/specs/        this file
bench/                         measurement harness (§7.2)
vte/                           VTE 0.84.x source: pristine import commit, then our patches as commits
xfce4-terminal-1.0.4/          existing app tree (patched in place, minimal)
build/                         scripts that build everything inside the loadout-build container
results/                       harness output (JSON per run + generated comparison tables); gitignored except summaries
```

This is a public GitHub repo. Pristine-import commits go first, so every change is a reviewable
diff. Upstream tarballs and the SRPM are not committed; they are pinned by URL and sha256
(`SHA256SUMS`). Upstream trees keep their own licences: xfce4-terminal is GPL-2.0-or-later, and
VTE is LGPL-3.0-or-later with some GPL-3.0-or-later parts. Our own code (harness and scripts) is
GPL-2.0-or-later. Wrap tarballs for `subprojects/` (simdutf, fmt, fast_float) and lz4 are pre-fetched into a checked-in
cache dir with sha256 pins so container builds run offline and reproducibly.

### 7.2 Measurement harness (built first; nothing in §7.3+ lands without numbers)

Runs inside the EL8 container against two builds: **baseline** = EPEL 1.0.4 binary + EL8 VTE 0.52.4
(exactly what ships), **candidate** = our build. Each workload runs N times (default 7). The report shows
median, p90, and spread. Regressions beyond 5% and outside the noise band are flagged.

Display setups:
- `xvfb`: Xvfb, measures the terminal alone.
- `xvnc`: EL8 TigerVNC `Xvnc` plus a headless RFB client in the harness (§ below), for T1 over VNC.
- `x11-remote`: the terminal reaches the X server through a counting, delaying TCP proxy. RTT and bandwidth
  are configurable; presets are 0, 0.25 ms (the measured farm-to-A LAN), 2 ms, and 20 ms (sensitivity
  only). This emulates T2. It can stack on `xvnc`.
- `live`: whatever `$DISPLAY` is, on a real target, no root. This runs latency, damage, CPU, and startup,
  for ETX/NoMachine/TigerVNC validation by the user. It runs on A for T1, and from a farm node with
  `DISPLAY=A:n` for T2.
- `diag`: collects environment facts from a real session. These are the X server vendor and release,
  the extensions (VNC, NX, ETX markers, RENDER, DAMAGE, SHM, XInput2), the WM name and version,
  the compositor selection owner, `_NET_SUPPORTED` (notably `_NET_WM_FRAME_DRAWN`), screen depth and
  size, fonts, GTK/Xft settings, and an RTT probe. Output is scrubbed JSON that the user can paste
  back. The scrub covers hostnames, usernames, IPs, and paths.

Window managers in the container (each display setup runs under each one):
- **mutter**, EL8's GNOME Classic WM, compositing. Run it standalone as `mutter --x11 --replace` or
  inside a minimal gnome-classic session, whichever is reproducible.
- **marco**, EPEL8 MATE, with compositing on and off.
- **no WM**, as the reference.

Metrics:
- **Keypress→pixels latency.** A small C helper (Xlib + XTest + XDamage) injects a key and timestamps the
  first damage on the terminal window, then confirms the pixels changed with XGetImage on the damaged
  rectangle. Under `xvnc`, the RFB client also measures true end-to-end time: it sends a KeyEvent and
  waits for the FramebufferUpdate that covers the changed area.
- **Throughput.** The workload runs inside the terminal (`-x`), and the harness times it until it finishes
  writing to the pty. Back-pressure keeps this within one pty buffer of the terminal's drain time. A final
  on-screen marker confirms the render.
- **Bytes on the wire.**
  - VNC: bytes, number of updates, and rectangles by encoding (CopyRect counted separately). Run with Tight
    (TigerVNC's default) and ZRLE.
  - T2: X11 request and reply bytes, request counts by opcode, blocking round trips (requests that need a
    reply), and image uploads (PutImage, ShmPutImage, Render AddGlyphs).
- **Damage area.** Damaged pixels per second and damage events, from XDamage. This stands in for ETX and
  NoMachine framebuffer encoders.
- **CPU.** utime+stime from `/proc` for the terminal and for the X server, per workload.
- **Startup.** Time to first mapped frame, and round trips during startup. Opening a terminal from a farm
  node over T2 is itself a latency users feel.

Workloads (deterministic inputs generated by the harness):
- Shell echo: single keys at a bash prompt; key bursts (typing at 15 cps).
- nvim (loadout's EL8 nvim build, minimal fixed config plus a variant with the user's typical options):
  typing in insert mode; `<C-e>`/`<C-d>` scrolling through a 50k-line file; vertical and horizontal splits;
  `:redraw!`. Driven over `--listen` RPC for throughput, and over XTest keys for latency.
- tmux (loadout's EL8 tmux, **private socket `tmux -L bench-<pid>` only**): two panes with bulk output in one
  while typing in the other; copy-mode scrolling; pane switching. Run with and without synchronized output
  enabled (`terminal-features ... :sync`).
- Bulk output: 50 MB dense ASCII; SGR-colour-heavy; Unicode (CJK, combining marks, Nerd Font PUA glyphs);
  box drawing (tmux borders, `tree`); compiler-log-like line stream.
- Full-screen redraw: alternate-screen app repainting 60×/s (htop-like).

Fixed conditions: two window sizes, 120×40 and 1920×1080 maximised. Fonts: CaskaydiaCove Nerd Font Mono 12
(the loadout seed) and DejaVu Sans Mono 12 (EL8 default). Cursor blink off. AT-SPI bus absent, with an extra
pass with one present (§7.5g).

Implementation: Python 3.6 or newer, standard library only, so it runs with EL8's `/usr/bin/python3` on
targets. The RFB client, the X11 proxy, and orchestration go here. The latency helper is C (libX11, libXtst,
libXdamage, libXext), built in the container. Output is JSON plus a generated markdown/TSV table.

### 7.3 VTE 0.84.x on EL8

- Import the latest 0.84.x stable release (check for a newer stable branch at start; pin whichever is used).
- Build with meson (pip-installed into a build venv in the container) and gcc-toolset-14.
  Options: `-Dgtk3=true -Dgtk4=false -Dgir=false -Dvapi=false -Ddocs=false -D_systemd=false`.
  gnutls and ICU stay on only if EL8's versions satisfy them; otherwise drop them and note the lost
  feature. Ship a11y as upstream does unless §7.5g says otherwise.
- Dependencies:
  - lz4 ≥ 1.9 built static (PIC) from a pinned upstream tarball.
  - simdutf, fmt, fast_float from the bundled wraps, static, offline cache.
  - fribidi 1.0.4, pcre2 10.32, pango 1.42, and cairo 1.15.12 from EL8, which satisfy VTE's floors.
- **GTK 3.24 → 3.22 back-port (`src/widget.cc`).** Replace the GTK 3.24 event controllers and gestures with
  GTK 3.22 signal handlers (`key-press-event`, `button-press-event`, `motion-notify-event`, `scroll-event`,
  and so on). Keep VTE's internal event abstraction untouched so the patch stays in one file. Lower the meson
  floor to 3.22 behind our patch.
- **GLib 2.72 → 2.56 back-port.** Add a small compat header with `g_memdup2` and similar shims. Compile the
  GUri-based termprop URI paths out under a `VTE_COMPAT_GLIB_256` guard; their public API stays as stubs that
  return NULL. Fix the remaining compile errors the same way. **Stop and report** if the compat layer grows
  past roughly 600 lines or needs a GLib behaviour change. That is the signal to reconsider bundling a newer
  GLib, and it is a decision for the user, not the builder.
- Install as a **private** `libvte-2.91.so.0` that only xfce4-terminal resolves (for example
  `lib64/xfce4-terminal/`, reached by the binary's RUNPATH). The shared payload stem that mate-terminal uses
  is left alone.
- Correctness: VTE's own `meson test` suite in the container; the interactive checklist in §8.

### 7.4 xfce4-terminal 1.0.4 from source

- Build with autotools in the container against the new VTE, EL8 GTK 3.22, and the bundled
  libxfce4ui/libxfce4util/xfconf (`-devel` packages from EPEL8 at build time). Fix deprecation fallout
  only as needed.
- Profile under the harness for app-level costs: the `contents-changed` tab-activity handler, title updates,
  and anything else that shows up per frame. Back-port the 1.2.0 tab-title CPU fix if it applies.
  Keep app patches small and separate.

### 7.5 Remote-display engine changes (VTE patches; each one measured on/off)

Rough priority order. The builder may reorder based on what the baseline numbers show is biggest.

a. **Synchronized output (DEC mode 2026).**
   - BSU/ESU suspend invalidation while still parsing.
   - A safety timeout (default 200 ms, configurable) forces a flush.
   - Answer DECRQM ?2026 so nvim and tmux can detect it.
   - Clear the state on reset and on alternate-screen switches.
   - Add loadout tmux config (`terminal-features` `sync`) only after measurement shows a win.

b. **Scroll by copying pixels.**
   - Spike first. Prove that on GTK 3.22 X11, `gdk_window_move_region` (or an equivalent on a native child
     window that VTE owns) produces a server-side `CopyArea`, that Xvnc emits CopyRect for it, and how it
     looks on the T2 proxy.
   - If yes, use it for whole-width scrolls of the viewport and of DECSTBM regions. Repaint only the
     exposed lines.
   - Disable it when copying is unsafe: background image, transparency, a selection or highlight crossing
     the region, a partial-width scroll region, or pending invalidations inside the region.
   - If the spike fails, write up why and drop the item.

c. **Keypress→pixels fast path.**
   - When input arrives within a short window after a user keypress, process it and draw on the next
     opportunity rather than waiting a full scheduler tick. Bulk output keeps the batched path.
   - Investigate GDK frame-clock throttling on X11 when the WM supports `_NET_WM_FRAME_DRAWN`.
     - GTK can wait for the compositor's ack before the next frame. mutter does this, and so does
       marco with compositing on.
     - That wait costs the compositor's frame latency plus, over T2, a round trip, every frame.
     - Measure it under each WM.
     - If the stall sits in VTE's reach, fix it in VTE.
     - If it lives inside GDK, bring the evidence back before patching. The fallback is a private
       rebuild of EL8's GTK 3.22.30 SRPM with a minimal patch, used by xfce4-terminal only.

d. **Redraw pacing for bulk output.** Under sustained output, cap the frame rate (configurable, for example
   `VTE_MAX_FPS`, with a remote-friendly default chosen from measurements). Every frame costs encoder CPU
   and bandwidth, and nobody reads 60 frames a second of `cat`. Latency-path frames from (c) are exempt.

e. **X-protocol efficiency (T2).**
   - Using the proxy's opcode counts, eliminate round trips and image uploads from the steady-state draw
     path. Candidates:
     - box-drawing and block glyphs uploaded as images;
     - cursor and underline drawing that falls back to images;
     - any XGetImage or XSync.
   - Confirm glyphs go through server-side XRender glyph caches. Also cut startup round trips where VTE
     owns them.

f. **Damage minimisation.** Cut full-widget invalidations (focus changes, selection, hover, hyperlink and
   URL highlight) down to the cells actually affected, and make the cursor cheap to draw.

g. **Accessibility cost.** Measure with an AT-SPI bus present. If the a11y tracking costs meaningfully, bring
   the numbers back as a decision: a runtime opt-out in the wrapper (`NO_AT_BRIDGE=1`) or a build without
   a11y. Do not change it silently.

h. **Font rendering vs compressibility (study only).** Measure VNC bytes and damage cost for subpixel,
   grayscale, and no antialiasing, plus hinting levels. Report the results. Defaults change only with user
   approval (anti-goal: look changes).

i. **Runtime detection and adaptation.**
   - At realize time, VTE inspects the display it is on:
     - the X server vendor string and extensions (Xvnc's VNC extension, nxagent, ETX markers);
     - transport: Unix socket vs TCP, and whether MIT-SHM works;
     - round-trip time, from a few `GetInputFocus` round trips;
     - the WM and compositor: the `_NET_SUPPORTING_WM_CHECK` name, the `_NET_WM_CM_Sn` owner, and
       `_NET_WM_FRAME_DRAWN` support.
   - From these it picks a profile: `local`, `remote-desktop` (T1 behind an encoder), or `x11-remote`
     (T2). The profile sets the knobs from (a)–(d), such as frame cap, fast-path window, scroll-copy on or
     off, and sync timeout.
   - It re-evaluates when the compositor selection owner changes (marco compositing can be toggled live),
     and when the widget moves to another display or screen.
   - The detected profile and the reasons are logged under a debug flag, so `diag` and bug reports
     can show them.
   - Profile defaults come from harness measurements, not guesses.

Configuration knobs added in (a)–(d) and (i) are environment variables read by our VTE (prefix `VTE_`).
`VTE_PROFILE=auto|local|remote-desktop|x11-remote` overrides detection, and each knob overrides its
profile value. So the loadout wrapper or a user can pin behaviour without xfce4-terminal UI changes.

### 7.6 Deployment notes for T2 (documented and measured, not code)

These are measured with the `x11-remote` proxy where cheap and written up as guidance:
- Running the terminal on A with a remote shell into B moves the X traffic local to A and sends only pty
  bytes. MIT-SHM becomes available, and A's X server renders only the terminal's own frames.
- An X-protocol accelerator between B and A, such as `nxproxy` from nx-libs (EPEL8), is probably not
  worth it at 0.25 ms RTT. It is measured once to confirm.

### 7.7 Packaging and delivery

- Phase 1–4 deliverables live in this working tree: harness, patched sources, container build scripts,
  results.
- **Integration into engineering-loadout** comes last and needs its own go-ahead because it touches that
  repo. It means a source-build path for xfce4-terminal plus the private VTE, the payload layout and
  RUNPATH, wrapper env defaults for the §7.5 knobs, `packages.json`, tests, and PROVENANCE. The current
  `build-xfce4-terminal.sh` repack stays until then.

## 8. Validation

- Harness tables: baseline vs candidate, per topology and workload. Every §7.5 item is shown on and off.
- VTE `meson test` in the container.
- Clean-room runtime check:
  - A stock `almalinux:8.10` container with only the built artefacts plus loadout's EL8 runtime GTK
    stack. It starts, renders, and passes the harness smoke workload.
  - `objdump -T` shows no GLIBC > 2.28 and no GLIBCXX beyond EL8's.
- Interactive checklist, run under Xvnc and screenshotted:
  - nvim: splits, completion popups, true-colour themes.
  - tmux: panes, copy-mode, status line.
  - `less`, `htop`, `mc`.
  - Text: Unicode/CJK/emoji/Nerd glyphs, box drawing, bold/italic/underline styles.
  - Interaction: mouse reporting, selection and copy-on-select, right-click paste-selection, URL
    highlighting, search (PCRE2), resize/reflow, scrollback 1000 lines and unlimited.
  - Tabs, preferences dialog, unsafe-paste dialog.
- Real targets: the user runs `diag` and the harness's `live` mode in these setups, baseline vs candidate:
  - T1: a RHEL 8.10 VM under ETX, NoMachine, and TigerVNC, with GNOME Classic and MATE sessions;
  - T2: a farm node with `DISPLAY=A:n`.
  The builder asks for these runs at defined checkpoints: after the baseline, after the VTE swap, and
  after §7.5. Each request comes with exact commands.

## 9. Decisions

Decided by the user
- Optimise both latency and bandwidth; CPU-only rendering; target RHEL 8.10 under ETX/NoMachine/TigerVNC.
- Everything below xfce4-terminal 1.0.4 is open; new deps OK; EL can package them.
- Approach A: current VTE back-ported to EL8 GTK 3.22.
- T2 (X client on B, display on A) is in scope.
- Desktops on A are GNOME Classic and MATE, at EL8/EPEL8 versions. Adapt to them at runtime.
- T2 uses direct `DISPLAY=A:n` (no ssh). Farm-to-A RTT is about 0.25 ms.
- The user gathers real-target diagnostics on request.
- The project lives in a public GitHub repo.

My calls (correct any of these)
- xfce4-terminal gets a private libvte; mate-terminal stays on 0.52.4.
- Harness first; EPEL binary + VTE 0.52.4 is the baseline; 5% regression threshold.
- No look-affecting default changes without approval (§7.5g–h are measure-and-report).
- GLib gap handled by shims; bundling a newer GLib is a stop-and-ask, not a builder choice.
- Patching GTK is a stop-and-ask too (§7.5c).
- Repo name `xfce4-terminal-remote-perf`. Our code is GPL-2.0-or-later. Tarballs and SRPM are pinned by
  sha256, not committed. Real-site data is scrubbed before commit.
- One el8 build serves A and the farm nodes.
- engineering-loadout integration is a separate, later go-ahead.

Left to the builder
- Exact VTE point release; RFB client and proxy internals; workload parameters; ordering within §7.5;
  knob names and defaults (derived from measurements).

## 10. Risks

- `widget.cc` back-port subtly changes input behaviour (IME, dead keys, scroll smoothing). Mitigation:
  the input part of the checklist, plus key-injection tests in the harness.
- Scroll-by-copy is not achievable through GTK 3.22's drawing model. Mitigation: spike first; drop cleanly.
- ETX/NoMachine behave unlike Xvnc. Mitigation: damage-area and X-protocol proxies, plus the user's
  `diag`/`live` runs at each checkpoint.
- Runtime detection misclassifies a setup (for example an unknown ETX vendor string). Mitigation: the
  detection degrades to `local` behaviour, which is never worse than today. `VTE_PROFILE` overrides it,
  and the reasons are logged for `diag`.
- Synchronized-update deadlock-style hangs. Mitigation: hard timeout, reset paths, a fuzz workload that
  sends BSU without ESU.
