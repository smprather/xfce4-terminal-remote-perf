# xfce4-terminal-remote-perf

Making xfce4-terminal fast on GPU-less RHEL 8.10 VMs viewed through remote-desktop
servers (Exceed TurboX, NoMachine, TigerVNC), including X clients on other machines
that draw over the network to that VM's X server.

Speed means both **latency** (keypress to visible result) and **bandwidth/throughput**
(scrolling, full-screen redraws, bulk output) for everyday use: shells, nvim, tmux.
CPU-only, 2D techniques; no GPU.

## Status

Plan 1 (measurement harness and baselines) is implemented; see
[`docs/superpowers/plans/2026-11-25-plan-1-measurement-harness.md`](docs/superpowers/plans/2026-11-25-plan-1-measurement-harness.md).
Baseline numbers are in [`results/summary/2026-11-27-baseline.md`](results/summary/2026-11-27-baseline.md):
on EL8, VTE 0.52's ~25.6 ms key-to-paint time dominates typing latency on every display, and bulk
output runs at 11-36 MB/s with no scroll-by-copy. The design is
[`docs/superpowers/specs/2026-11-25-remote-display-performance-design.md`](docs/superpowers/specs/2026-11-25-remote-display-performance-design.md).

Plan in brief:

1. A measurement harness (latency, throughput, VNC bytes, X11 protocol bytes, damage, CPU)
   that runs in an AlmaLinux 8.10 container and, in a reduced mode, on real target VMs.
2. Replace EL8's VTE 0.52.4 with current upstream VTE back-ported to EL8's GTK 3.22 / GLib 2.56.
3. Remote-display engine work in VTE: synchronized output (mode 2026), scroll by copying
   pixels, a keypress-to-pixels fast path, redraw pacing, X-protocol efficiency, and runtime
   detection of the WM, compositor, and display type, with automatic adaptation.
4. xfce4-terminal 1.0.4 built from source against it. The app's behaviour and preferences
   are unchanged.

## Running the harness (`xtrp`)

Three platforms:

- `el8`: the primary platform. Every number that decides anything comes from here.
- `el9`: forward compatibility.
- `host`: the CachyOS dev box. Its numbers are informational.

```sh
bench/container bench/selftest-image          # el8 bench image (AlmaLinux 8.10); --el 9 for EL9
bench/selftest-host                           # host prerequisites; prints the pacman line if any are missing
bench/test-all                                # unit + integration tests on el8, el9 and the host

# measure: presets smoke | quick | full | rtt-sweep; builds come from bench/builds.json
bench/container python3 -m xtrp run --preset quick --build baseline --build candidate --out results/raw/ab
bench/container python3 -m xtrp report results/raw/ab results/raw/ab \
    --base-build baseline --cand-build candidate                       # exit 1 on a regression
PYTHONPATH=bench python3 -m xtrp run --preset smoke --build baseline --out results/raw/host-smoke   # on the host
```

Always run the baseline and the candidate interleaved in one invocation, as above. Separate
invocations differ by 10-17% in startup time alone (session drift on a shared machine), so
comparing them would flag noise. `baseline-twin` (the same binary under another name) measures
the remaining noise.

The rules that keep the harness safe on the host:

- Every child gets an environment built from scratch: no Wayland, no session D-Bus, and a private
  `HOME` and `XDG_RUNTIME_DIR`.
- Terminals run under their own `dbus-run-session`.
- tmux only ever runs on private `-L xtrp-*` sockets with a per-run `TMUX_TMPDIR`.
- Processes are stopped by the pid or process group the harness started, never by name.

To measure a real VM, see [`docs/LIVE.md`](docs/LIVE.md). Build its bundle with
`bench/container bench/make-live-bundle`.

## Layout

| Path | What |
|---|---|
| `xfce4-terminal-1.0.4/` | Upstream xfce4-terminal 1.0.4 (pristine import, then our patches) |
| `xfce4-terminal.spec`, `SHA256SUMS`, `README.loadout` | EPEL8 packaging metadata and pins for the source drop |
| `bench/` | The `xtrp` harness: images, C helpers (`xlat`, `testwin`), Python package, tests |
| `results/summary/` | Scrubbed baseline and comparison summaries (raw runs stay in `results/raw/`, untracked) |
| `docs/` | Design, plans, and `LIVE.md` (running xtrp on a real VM) |

## Licensing

Upstream trees keep their own licences: xfce4-terminal is GPL-2.0-or-later, and VTE is
LGPL-3.0-or-later with some GPL-3.0-or-later parts. Our own code (harness and scripts) is
GPL-2.0-or-later; see `LICENSE`.
