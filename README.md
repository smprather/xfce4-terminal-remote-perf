# xfce4-terminal-remote-perf

Making xfce4-terminal fast on GPU-less RHEL 8.10 VMs viewed through remote-desktop
servers (Exceed TurboX, NoMachine, TigerVNC), including X clients on other machines
that draw over the network to that VM's X server.

Speed means both **latency** (keypress to visible result) and **bandwidth/throughput**
(scrolling, full-screen redraws, bulk output) for everyday use: shells, nvim, tmux.
CPU-only, 2D techniques; no GPU.

## Status

Design stage. See
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

## Layout

| Path | What |
|---|---|
| `xfce4-terminal-1.0.4/` | Upstream xfce4-terminal 1.0.4 (pristine import, then our patches) |
| `xfce4-terminal.spec`, `SHA256SUMS`, `README.loadout` | EPEL8 packaging metadata and pins for the source drop |
| `docs/` | Design and plans |

## Licensing

Upstream trees keep their own licences: xfce4-terminal is GPL-2.0-or-later, and VTE is
LGPL-3.0-or-later with some GPL-3.0-or-later parts. Our own code (harness and scripts) is
GPL-2.0-or-later; see `LICENSE`.
