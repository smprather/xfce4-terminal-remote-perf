# Baseline medians, EL8 (2026-11-27)

Every el8 configuration of the `full` and `rtt-sweep` presets, build `baseline` (EPEL8 xfce4-terminal
1.0.4 + VTE 0.52.4). Each run is reduced to its own median first. A cell is the median over runs: 7
iterations, or 5 for the size/font block and the RTT sweep. Latency columns are per-keystroke medians.
`latency_multi_paint` counts keys followed by a separate later paint. Counters are raw totals, not per
key: divide typing-workload counters by 40 (Xvfb) or 60 (VNC: 40 X-side + 20 end-to-end keys).
`tmux-type-load` counters include the bulk output running in the other pane. "large" is the window
maximised on the 1920x1080 screen; the actual cells and pixels per configuration are in the GEOMETRY
table of the commentary: [2026-11-27-baseline.md](2026-11-27-baseline.md).

## full preset


### display_kind=xvnc / vnc_encoding=tight / wm=none / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tmux-type-load | 69.5 | - | - | - | - | - | 58.9 | 0.57 | 0.783 | 49 | 100M | 8.4M | 49 | 0 | - |
| nvim-scroll | - | - | - | - | 0.181 | 0.0348 | 58.8 | 0.0633 | 0.0415 | 6 | 11.9M | 351k | 6 | 0 | - |
| nvim-type | 26.7 | 36.2 | 0 | - | - | - | 58.9 | 0.0423 | 0.112 | 60 | 116M | 5.74e+03 | 60 | 0 | - |
| sgr-color | - | - | - | 21.3 | 2.36 | 0.102 | 59 | 1.98 | 0.563 | 20 | 41.5M | 16.7M | 20 | 0 | - |
| compile-log | - | - | - | 18.3 | 1 | 0.0515 | 54 | 0.824 | 0.175 | 10 | 20.7M | 2.2M | 10 | 0 | - |
| shell-echo | 25.6 | 34.5 | 0 | - | - | - | 53.7 | 0.0186 | 0.0496 | 60 | 2.42M | 3.42e+03 | 60 | 0 | - |
| tmux-bulk-split | - | - | - | 35.6 | 0.558 | 0.0315 | 54.3 | 0.306 | 0.206 | 11 | 12.2M | 2.69M | 11 | 0 | - |
| tmux-type | 25.6 | 34.5 | 0 | - | - | - | 59 | 0.0189 | 0.0503 | 60 | 2.07M | 7.12e+03 | 60 | 0 | - |
| fullscreen-redraw | - | - | - | 0.722 | 5 | 0.004 | 54.1 | 0.319 | 2.05 | 159 | 330M | 3.05M | 159 | 0 | 300 |
| tmux-pane-switch | 27 | 36.3 | 0 | - | - | - | 58.9 | 0.0445 | 0.0886 | 60 | 64.7M | 10.6k | 60 | 0 | - |
| unicode | - | - | - | 11.6 | 4.47 | 0.056 | 58.9 | 3.87 | 0.781 | 36 | 74.6M | 8.54M | 36 | 0 | - |
| bulk-ascii | - | - | - | 14.7 | 3.53 | 0.044 | 58.7 | 2.71 | 0.791 | 29 | 60.1M | 10.4M | 29 | 0 | - |
| box-drawing | - | - | - | 35.4 | 1.4 | 0.0786 | 54.1 | 1.31 | 0.0785 | 13 | 27M | 146k | 13 | 0 | - |

### display_kind=xvfb / wm=none / size=large / font=caskaydia

| workload | latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sgr-color | - | - | 21.4 | 2.35 | 0.0935 | 53.7 | 1.96 | 0.0855 | 20 | 41.5M | - |
| unicode | - | - | 11.6 | 4.47 | 0.0464 | 58.7 | 3.85 | 0.196 | 36 | 74.6M | - |
| box-drawing | - | - | 34.9 | 1.45 | 0.0559 | 58.8 | 1.32 | 0.0329 | 14 | 29M | - |
| nvim-type | 26.7 | 0 | - | - | - | 53.8 | 0.0265 | 0.0444 | 40 | 77M | - |
| bulk-ascii | - | - | 14.9 | 3.41 | 0.107 | 53.9 | 2.69 | 0.0926 | 28 | 58.1M | - |
| shell-echo | 25.6 | 0 | - | - | - | 58.6 | 0.0117 | 0.0052 | 40 | 1.61M | - |
| tmux-type-load | 71 | - | - | - | - | 54.1 | 0.572 | 0.124 | 49 | 100M | - |
| tmux-bulk-split | - | - | 36.1 | 0.555 | 0.0389 | 54.2 | 0.304 | 0.0218 | 11 | 12.2M | - |
| compile-log | - | - | 18.3 | 1 | 0.0493 | 53.8 | 0.821 | 0.0275 | 10 | 20.7M | - |
| tmux-pane-switch | 27 | 0 | - | - | - | 53.8 | 0.0288 | 0.0251 | 40 | 43.5M | - |
| tmux-type | 25.6 | 0 | - | - | - | 53.9 | 0.0118 | 0.00561 | 40 | 2.06M | - |
| nvim-scroll | - | - | - | 0.182 | 0.0342 | 53.9 | 0.0629 | 0.0111 | 6 | 11.9M | - |
| fullscreen-redraw | - | - | 0.722 | 5 | 0.0038 | 58.8 | 0.308 | 0.489 | 159 | 330M | 300 |

### display_kind=xvfb / wm=marco-comp / size=large / font=caskaydia

| workload | latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|
| tmux-type | 25.6 | 0 | - | - | - | 58 | 0.0106 | 0.0114 | 40 | 2.03M | - |
| compile-log | - | - | 18.3 | 0.997 | 0.0542 | 58.3 | 0.815 | 0.0385 | 10 | 20.2M | - |
| tmux-type-load | 70.9 | - | - | - | - | 57.7 | 0.536 | 0.18 | 49 | 98.5M | - |
| sgr-color | - | - | 21.4 | 2.35 | 0.102 | 57 | 1.97 | 0.107 | 20 | 40.4M | - |
| nvim-scroll | - | - | - | 0.181 | 0.035 | 57.5 | 0.0631 | 0.018 | 6 | 11.7M | - |
| nvim-type | 26.8 | 0 | - | - | - | 57.5 | 0.026 | 0.0807 | 40 | 75.6M | - |
| tmux-bulk-split | - | - | 36 | 0.551 | 0.0323 | 58 | 0.307 | 0.0304 | 11 | 11.9M | - |
| bulk-ascii | - | - | 14.9 | 3.4 | 0.112 | 57 | 2.69 | 0.126 | 28 | 56.6M | - |
| tmux-pane-switch | 27.1 | 0 | - | - | - | 57.6 | 0.0281 | 0.0474 | 40 | 43.4M | - |
| shell-echo | 25.6 | 0 | - | - | - | 57.9 | 0.0105 | 0.01 | 40 | 1.61M | - |
| unicode | - | - | 11.6 | 4.48 | 0.0601 | 57.8 | 3.87 | 0.235 | 36 | 72.8M | - |
| fullscreen-redraw | - | - | 0.709 | 5 | 0.0037 | 58.1 | 0.314 | 0.666 | 159 | 321M | 300 |
| box-drawing | - | - | 35.6 | 1.39 | 0.0807 | 57.7 | 1.31 | 0.0446 | 13 | 26.3M | - |

### display_kind=xvnc / vnc_encoding=zrle / wm=marco-nocomp / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fullscreen-redraw | - | - | - | 0.71 | 5 | 0 | 57.1 | 0.314 | 2.44 | 159 | 321M | 2.51M | 159 | 0 | 300 |
| tmux-type-load | 59.1 | - | - | - | - | - | 58.1 | 0.558 | 1.31 | 51 | 103M | 10.1M | 50 | 0 | - |
| sgr-color | - | - | - | 21.2 | 2.36 | 0.108 | 57.8 | 2 | 1.12 | 20 | 40.4M | 15M | 20 | 0 | - |
| box-drawing | - | - | - | 35.6 | 1.39 | 0.0861 | 57.4 | 1.32 | 0.0891 | 13 | 26.3M | 88.6k | 13 | 0 | - |
| tmux-pane-switch | 27 | 36.2 | 0 | - | - | - | 57.6 | 0.043 | 0.0913 | 60 | 64.7M | 8.23e+03 | 60 | 0 | - |
| unicode | - | - | - | 11.5 | 4.47 | 0.0695 | 58.7 | 3.89 | 1.31 | 36 | 72.8M | 9.49M | 36 | 0 | - |
| nvim-scroll | - | - | - | - | 0.181 | 0.0352 | 57.2 | 0.0612 | 0.0623 | 6 | 11.7M | 348k | 6 | 0 | - |
| shell-echo | 25.6 | 34.4 | 0 | - | - | - | 58.7 | 0.0166 | 0.0508 | 60 | 2.42M | 3.22e+03 | 60 | 0 | - |
| compile-log | - | - | - | 18.2 | 1 | 0.0555 | 57.5 | 0.826 | 0.294 | 10 | 20.2M | 2.05M | 10 | 0 | - |
| tmux-bulk-split | - | - | - | 33.2 | 0.577 | 0.0543 | 56.8 | 0.326 | 0.376 | 12 | 12.8M | 3.2M | 12 | 0 | - |
| bulk-ascii | - | - | - | 14.6 | 3.53 | 0.0589 | 57.8 | 2.72 | 1.39 | 29 | 58.6M | 12.5M | 29 | 0 | - |
| nvim-type | 26.7 | 36.2 | 0 | - | - | - | 57.2 | 0.0389 | 0.115 | 60 | 113M | 5.61e+03 | 60 | 0 | - |
| tmux-type | 25.7 | 34.4 | 0 | - | - | - | 57.8 | 0.0166 | 0.0501 | 60 | 2.04M | 3.77e+03 | 60 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=none / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tmux-bulk-split | - | - | - | 34.3 | 0.562 | 0.0467 | 89.4 | 0.302 | 0.222 | 12 | 13.2M | 2.93M | 12 | 0 | 94.3k | 504 | 9.14e+03 | 14 | - |
| bulk-ascii | - | - | - | 14.7 | 3.53 | 0.0493 | 85.7 | 2.71 | 0.784 | 29 | 60.1M | 10.4M | 29 | 0 | 313k | 1.05e+03 | 12k | 31 | - |
| box-drawing | - | - | - | 35 | 1.46 | 0.0582 | 85.7 | 1.32 | 0.0818 | 14 | 29M | 150k | 14 | 0 | 1.84M | 568 | 64 | 16 | - |
| nvim-scroll | - | - | - | - | 0.186 | 0.0308 | 85.7 | 0.0633 | 0.0432 | 6 | 11.9M | 388k | 6 | 0 | 43.9k | 312 | 1.28e+03 | 8 | - |
| unicode | - | - | - | 11.5 | 4.48 | 0.0702 | 86.3 | 3.9 | 0.787 | 36 | 74.6M | 8.52M | 36 | 0 | 9.46M | 1.27e+03 | 137k | 38 | - |
| shell-echo | 27.1 | 35.9 | 0 | - | - | - | 84.7 | 0.0194 | 0.0485 | 60 | 2.42M | 3.42e+03 | 60 | 0 | 24.9k | 43.2k | 124 | 129 | - |
| tmux-type-load | 69.5 | - | - | - | - | - | 85.7 | 0.571 | 0.785 | 49 | 100M | 8.43M | 49 | 0 | 682k | 25.8k | 0 | 95 | - |
| sgr-color | - | - | - | 21.2 | 2.36 | 0.106 | 89.4 | 1.98 | 0.579 | 20 | 41.5M | 16.6M | 20 | 0 | 2.16M | 760 | 51.8k | 22 | - |
| compile-log | - | - | - | 18.3 | 1 | 0.0463 | 85.5 | 0.822 | 0.173 | 10 | 20.7M | 2.19M | 10 | 0 | 98.5k | 440 | 11.7k | 12 | - |
| fullscreen-redraw | - | - | - | 0.721 | 5 | 0.00774 | 84.8 | 0.312 | 2.06 | 159 | 330M | 3.08M | 159 | 0 | 2.73M | 5.27e+03 | 12k | 163 | 300 |
| tmux-pane-switch | 28 | 37.2 | 0 | - | - | - | 85.1 | 0.045 | 0.0901 | 60 | 64.7M | 10.8k | 60 | 0 | 543k | 44.3k | 728 | 129 | - |
| nvim-type | 27.9 | 37.4 | 0 | - | - | - | 89.4 | 0.0426 | 0.114 | 60 | 116M | 5.74e+03 | 60 | 0 | 38.1k | 44.3k | 136 | 129 | - |
| tmux-type | 27 | 35.8 | 0 | - | - | - | 89.5 | 0.02 | 0.0508 | 60 | 2.07M | 7.12e+03 | 60 | 0 | 20.8k | 44.3k | 728 | 129 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=mutter / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| box-drawing | - | - | - | 35.6 | 1.4 | 0.068 | 217 | 1.31 | 0.107 | 13 | 26M | 140k | 13 | 0 | - |
| compile-log | - | - | - | 18.2 | 0.996 | 0.0547 | 215 | 0.825 | 0.193 | 10 | 20M | 2.12M | 10 | 0 | - |
| tmux-type-load | 64.5 | - | - | - | - | - | 219 | 0.534 | 0.886 | 49 | 96.7M | 8.19M | 49 | 0 | - |
| tmux-pane-switch | 27 | 39.7 | 0 | - | - | - | 210 | 0.0448 | 0.187 | 60 | 62.5M | 7.94e+03 | 60 | 0 | - |
| tmux-type | 25.6 | 35.2 | 0 | - | - | - | 208 | 0.0189 | 0.0636 | 60 | 2M | 4.3e+03 | 60 | 0 | - |
| nvim-type | 26.8 | 39.9 | 0 | - | - | - | 209 | 0.0426 | 0.171 | 60 | 111M | 5.99e+03 | 60 | 0 | - |
| shell-echo | 25.6 | 35.3 | 0 | - | - | - | 222 | 0.0177 | 0.0583 | 60 | 2.42M | 3.43e+03 | 60 | 0 | - |
| bulk-ascii | - | - | - | 14.6 | 3.53 | 0.0589 | 219 | 2.72 | 0.842 | 29 | 58.1M | 10.1M | 29 | 0 | - |
| sgr-color | - | - | - | 21.2 | 2.36 | 0.103 | 225 | 2 | 0.624 | 20 | 40.1M | 16.1M | 20 | 0 | - |
| unicode | - | - | - | 11.5 | 4.47 | 0.0825 | 228 | 3.9 | 0.855 | 36 | 72.1M | 8.16M | 36 | 0 | - |
| nvim-scroll | - | - | - | - | 0.195 | 0.0209 | 227 | 0.0612 | 0.0582 | 6 | 11.4M | 378k | 6 | 0 | - |
| tmux-bulk-split | - | - | - | 33.9 | 0.578 | 0.0415 | 210 | 0.31 | 0.224 | 12 | 12.7M | 2.83M | 12 | 0 | - |
| fullscreen-redraw | - | - | - | 0.697 | 5 | 0.000172 | 219 | 0.327 | 2.48 | 158 | 316M | 2.94M | 158 | 0 | 300 |

### display_kind=xvfb / wm=marco-nocomp / size=large / font=caskaydia

| workload | latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|
| compile-log | - | - | 18.3 | 1 | 0.0488 | 57.7 | 0.823 | 0.0281 | 10 | 20.2M | - |
| tmux-type-load | 70.8 | - | - | - | - | 57.3 | 0.543 | 0.123 | 49 | 98.5M | - |
| tmux-type | 25.6 | 0 | - | - | - | 57.6 | 0.0107 | 0.00596 | 40 | 2.03M | - |
| box-drawing | - | - | 35.3 | 1.4 | 0.0745 | 57.5 | 1.32 | 0.0315 | 13 | 26.3M | - |
| unicode | - | - | 11.6 | 4.47 | 0.0625 | 57.4 | 3.86 | 0.195 | 36 | 72.8M | - |
| tmux-pane-switch | 27 | 0 | - | - | - | 56.9 | 0.0274 | 0.0254 | 40 | 43.4M | - |
| sgr-color | - | - | 21.4 | 2.35 | 0.095 | 58.3 | 1.97 | 0.0882 | 20 | 40.4M | - |
| tmux-bulk-split | - | - | 35.8 | 0.557 | 0.0325 | 57.7 | 0.305 | 0.0203 | 11 | 11.9M | - |
| nvim-scroll | - | - | - | 0.186 | 0.0294 | 57.8 | 0.0608 | 0.0106 | 6 | 11.7M | - |
| bulk-ascii | - | - | 14.8 | 3.41 | 0.105 | 56.7 | 2.69 | 0.095 | 29 | 58.6M | - |
| shell-echo | 25.6 | 0 | - | - | - | 57.9 | 0.0101 | 0.00546 | 40 | 1.61M | - |
| fullscreen-redraw | - | - | 0.709 | 5 | 0.0036 | 57.5 | 0.302 | 0.478 | 159 | 321M | 300 |
| nvim-type | 26.7 | 0 | - | - | - | 58.2 | 0.0246 | 0.0445 | 40 | 75.6M | - |

### display_kind=xvnc / vnc_encoding=tight / wm=mutter / size=small / font=dejavu

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| box-drawing | - | - | - | 35.8 | 1.4 | 0.0662 | 157 | 1.3 | 0.0556 | 13 | 11.9M | 145k | 13 | 0 | - |
| shell-echo | 25.6 | 35 | 0 | - | - | - | 146 | 0.0177 | 0.0429 | 60 | 1.51M | 10.2k | 60 | 0 | - |
| unicode | - | - | - | 11.6 | 4.47 | 0.0568 | 150 | 3.77 | 0.551 | 36 | 33M | 7.89M | 36 | 0 | - |
| tmux-pane-switch | 26.4 | 36.6 | 0 | - | - | - | 153 | 0.0326 | 0.0816 | 60 | 29.4M | 44.5k | 60 | 0 | - |
| bulk-ascii | - | - | - | 14.4 | 3.54 | 0.0886 | 153 | 2.74 | 0.376 | 29 | 26.6M | 6.61M | 29 | 0 | - |
| tmux-bulk-split | - | - | - | 36.4 | 0.549 | 0.028 | 143 | 0.239 | 0.108 | 13 | 6.29M | 1.83M | 13 | 0 | - |
| fullscreen-redraw | - | - | - | 0.293 | 5 | 0 | 145 | 0.156 | 1.07 | 160 | 147M | 1.91M | 161 | 0 | 300 |
| sgr-color | - | - | - | 21.3 | 2.35 | 0.108 | 124 | 1.97 | 0.315 | 20 | 18.3M | 8.05M | 20 | 0 | - |
| nvim-type | 26.3 | 37.2 | 0 | - | - | - | 151 | 0.029 | 0.101 | 60 | 49.6M | 17.5k | 60 | 0 | - |
| tmux-type | 25.6 | 34.8 | 0 | - | - | - | 146 | 0.0175 | 0.0459 | 60 | 944k | 17.3k | 60 | 0 | - |
| tmux-type-load | 70.8 | - | - | - | - | - | 153 | 0.506 | 0.405 | 49 | 44.9M | 5.24M | 49 | 0 | - |
| nvim-scroll | - | - | - | - | 0.187 | 0.0206 | 127 | 0.0522 | 0.0313 | 6 | 5.24M | 271k | 6 | 0 | - |
| compile-log | - | - | - | 19 | 0.894 | 0.112 | 152 | 0.813 | 0.116 | 9 | 8.24M | 1.51M | 9 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=marco-comp / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | - | 0.183 | 0.0339 | 92.6 | 0.0617 | 0.0487 | 6 | 11.7M | 392k | 6 | 0 | 43.1k | 0 | 1.12e+03 | 0 | - |
| shell-echo | 26.1 | 50.5 | 0 | - | - | - | 92.2 | 0.0157 | 0.0192 | 60 | 2.42M | 3.4e+03 | 60 | 0 | 22.1k | 37.5k | 124 | 9 | - |
| nvim-type | 27.4 | 53.6 | 0 | - | - | - | 92.5 | 0.0409 | 0.16 | 60 | 113M | 5.83e+03 | 60 | 0 | 35.2k | 38.5k | 136 | 9 | - |
| tmux-bulk-split | - | - | - | 34.3 | 0.566 | 0.0436 | 92.7 | 0.318 | 0.215 | 11 | 12M | 2.67M | 11 | 0 | 87.1k | 0 | 9.31e+03 | 0 | - |
| unicode | - | - | - | 11.5 | 4.47 | 0.0884 | 92.6 | 3.91 | 0.835 | 36 | 72.8M | 8.36M | 36 | 0 | 9.37M | 96 | 137k | 3 | - |
| tmux-type | 26.1 | 50.6 | 0 | - | - | - | 92.6 | 0.0159 | 0.021 | 60 | 2.04M | 4.22e+03 | 60 | 0 | 17.9k | 38.5k | 728 | 9 | - |
| fullscreen-redraw | - | - | - | 0.71 | 5 | 0 | 92.1 | 0.315 | 2.15 | 158 | 319M | 2.99M | 158 | 0 | 2.66M | 64 | 11.3k | 2 | 300 |
| tmux-pane-switch | 27.6 | 53.1 | 0 | - | - | - | 92.1 | 0.0428 | 0.0995 | 60 | 64.7M | 7.98e+03 | 60 | 0 | 540k | 38.5k | 728 | 9 | - |
| compile-log | - | - | - | 18.1 | 1 | 0.0592 | 91.6 | 0.829 | 0.178 | 10 | 20.2M | 2.14M | 10 | 0 | 96.8k | 0 | 11.7k | 0 | - |
| bulk-ascii | - | - | - | 14.6 | 3.53 | 0.0535 | 94.2 | 2.72 | 0.811 | 29 | 58.6M | 10.3M | 29 | 0 | 307k | 0 | 12k | 0 | - |
| tmux-type-load | 71.1 | - | - | - | - | - | 92.5 | 0.54 | 0.802 | 49 | 98.5M | 7.87M | 48 | 0 | 668k | 21.7k | 0 | 6 | - |
| sgr-color | - | - | - | 21.3 | 2.35 | 0.106 | 93 | 1.97 | 0.591 | 20 | 40.4M | 16.2M | 20 | 0 | 2.12M | 32 | 51.8k | 1 | - |
| box-drawing | - | - | - | 35.5 | 1.4 | 0.067 | 91.5 | 1.32 | 0.0849 | 13 | 26.3M | 140k | 13 | 0 | 1.71M | 0 | 64 | 0 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=mutter / size=small / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-type | 26.2 | 36.9 | 0 | - | - | - | 115 | 0.0279 | 0.0956 | 60 | 44.7M | 16.4k | 60 | 0 | - |
| tmux-type-load | 70.7 | - | - | - | - | - | 140 | 0.519 | 0.408 | 49 | 40.4M | 5.33M | 49 | 0 | - |
| bulk-ascii | - | - | - | 14.6 | 3.54 | 0.0553 | 137 | 2.73 | 0.38 | 29 | 23.9M | 6.69M | 30 | 0 | - |
| tmux-type | 25.6 | 34.7 | 0 | - | - | - | 113 | 0.0174 | 0.0446 | 60 | 851k | 17.1k | 60 | 0 | - |
| fullscreen-redraw | - | - | - | 0.293 | 5 | 0 | 149 | 0.156 | 1.01 | 160 | 132M | 1.87M | 161 | 0 | 300 |
| shell-echo | 25.6 | 34.8 | 0 | - | - | - | 219 | 0.0176 | 0.041 | 60 | 1.36M | 9.32e+03 | 60 | 0 | - |
| compile-log | - | - | - | 18.4 | 1 | 0.0372 | 136 | 0.821 | 0.126 | 10 | 8.24M | 1.68M | 10 | 0 | - |
| unicode | - | - | - | 11.6 | 4.47 | 0.0637 | 140 | 3.81 | 0.535 | 36 | 29.7M | 7.57M | 36 | 0 | - |
| sgr-color | - | - | - | 21.3 | 2.35 | 0.111 | 118 | 1.97 | 0.323 | 20 | 16.5M | 8.4M | 20 | 0 | - |
| tmux-pane-switch | 26.4 | 36.5 | 0 | - | - | - | 145 | 0.033 | 0.076 | 60 | 26.4M | 24.5k | 60 | 0 | - |
| box-drawing | - | - | - | 35.8 | 1.39 | 0.0705 | 144 | 1.3 | 0.0507 | 13 | 10.7M | 135k | 13 | 0 | - |
| tmux-bulk-split | - | - | - | 35.9 | 0.56 | 0.0432 | 130 | 0.243 | 0.104 | 13 | 5.68M | 1.73M | 13 | 0 | - |
| nvim-scroll | - | - | - | - | 0.183 | 0.025 | 147 | 0.053 | 0.0317 | 6 | 4.72M | 308k | 6 | 0 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=marco-nocomp / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | - | 0.18 | 0.0357 | 57.7 | 0.0611 | 0.0413 | 6 | 11.7M | 344k | 6 | 0 | - |
| tmux-type-load | 69.1 | - | - | - | - | - | 57.9 | 0.538 | 0.771 | 49 | 98.5M | 8.25M | 49 | 0 | - |
| bulk-ascii | - | - | - | 14.7 | 3.52 | 0.0544 | 58.1 | 2.7 | 0.765 | 29 | 58.6M | 10.2M | 29 | 0 | - |
| tmux-bulk-split | - | - | - | 34.4 | 0.568 | 0.0394 | 57.6 | 0.305 | 0.21 | 12 | 12.8M | 3.02M | 12 | 0 | - |
| sgr-color | - | - | - | 21.3 | 2.35 | 0.111 | 57.7 | 1.98 | 0.562 | 20 | 40.4M | 16.4M | 20 | 0 | - |
| fullscreen-redraw | - | - | - | 0.709 | 5 | 0.0038 | 56.5 | 0.314 | 2.01 | 159 | 321M | 2.98M | 159 | 0 | 300 |
| tmux-pane-switch | 27 | 36.3 | 0 | - | - | - | 57.3 | 0.042 | 0.0903 | 60 | 64.7M | 9.27e+03 | 60 | 0 | - |
| box-drawing | - | - | - | 35.6 | 1.38 | 0.0777 | 56.7 | 1.31 | 0.0757 | 13 | 26.3M | 139k | 13 | 0 | - |
| shell-echo | 25.6 | 34.4 | 0 | - | - | - | 57.7 | 0.0167 | 0.0516 | 60 | 2.42M | 3.42e+03 | 60 | 0 | - |
| tmux-type | 25.6 | 34.4 | 0 | - | - | - | 58.1 | 0.017 | 0.0507 | 60 | 2.04M | 4.04e+03 | 60 | 0 | - |
| unicode | - | - | - | 11.6 | 4.47 | 0.0558 | 56.8 | 3.87 | 0.756 | 36 | 72.8M | 8.31M | 36 | 0 | - |
| compile-log | - | - | - | 18.2 | 1 | 0.0536 | 58 | 0.824 | 0.17 | 10 | 20.2M | 2.13M | 10 | 0 | - |
| nvim-type | 26.7 | 36.1 | 0 | - | - | - | 57.5 | 0.039 | 0.114 | 60 | 113M | 5.74e+03 | 60 | 0 | - |

### display_kind=xvfb / wm=mutter / size=large / font=caskaydia

| workload | latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|
| shell-echo | 25.6 | 0 | - | - | - | 75.1 | 0.0117 | 0.0294 | 40 | 1.61M | - |
| box-drawing | - | - | 35.5 | 1.39 | 0.0779 | 67.6 | 1.31 | 0.0428 | 13 | 26M | - |
| nvim-type | 26.7 | 0 | - | - | - | 78.6 | 0.0265 | 0.075 | 40 | 74.2M | - |
| tmux-type-load | 70.8 | - | - | - | - | 75.2 | 0.525 | 0.175 | 49 | 96.7M | - |
| tmux-pane-switch | 27 | 0 | - | - | - | 75.2 | 0.0286 | 0.0562 | 40 | 42M | - |
| tmux-bulk-split | - | - | 33.6 | 0.576 | 0.0374 | 68.1 | 0.314 | 0.032 | 12 | 12.6M | - |
| nvim-scroll | - | - | - | 0.195 | 0.0191 | 75 | 0.0611 | 0.0172 | 6 | 11.4M | - |
| fullscreen-redraw | - | - | 0.695 | 5 | 0.00834 | 64.8 | 0.327 | 0.652 | 158 | 316M | 300 |
| bulk-ascii | - | - | 14.9 | 3.41 | 0.109 | 76.2 | 2.7 | 0.119 | 28 | 56.1M | - |
| tmux-type | 25.6 | 0 | - | - | - | 69.3 | 0.012 | 0.0293 | 40 | 1.99M | - |
| unicode | - | - | 11.6 | 4.47 | 0.0594 | 68.2 | 3.87 | 0.224 | 36 | 72.1M | - |
| sgr-color | - | - | 21.4 | 2.36 | 0.101 | 67.5 | 1.98 | 0.107 | 20 | 40.1M | - |
| compile-log | - | - | 18.3 | 0.996 | 0.0537 | 66.4 | 0.821 | 0.0368 | 10 | 20M | - |

### display_kind=xvnc+x11remote / vnc_encoding=zrle / wm=mutter / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sgr-color | - | - | - | 20.6 | 2.47 | 0.0802 | 349 | 2.01 | 1.19 | 21 | 42.1M | 15.2M | 21 | 0 | 2.17M | 1.34e+03 | 51.8k | 0 | - |
| compile-log | - | - | - | 18.3 | 1 | 0.0504 | 328 | 0.828 | 0.322 | 10 | 20M | 2.03M | 10 | 0 | 95.5k | 640 | 11.7k | 0 | - |
| unicode | - | - | - | 11.4 | 4.48 | 0.11 | 337 | 3.95 | 1.42 | 36 | 72.1M | 9.37M | 36 | 0 | 9.16M | 2.3e+03 | 137k | 0 | - |
| bulk-ascii | - | - | - | 14.6 | 3.52 | 0.0706 | 346 | 2.73 | 1.47 | 29 | 58.1M | 12.4M | 29 | 0 | 301k | 1.86e+03 | 12k | 0 | - |
| shell-echo | 26.1 | 35.8 | 0 | - | - | - | 301 | 0.0176 | 0.057 | 60 | 2.42M | 3.21e+03 | 60 | 0 | 22.1k | 41.3k | 124 | 9 | - |
| nvim-scroll | - | - | - | - | 0.194 | 0.0212 | 361 | 0.0613 | 0.0762 | 6 | 11.4M | 339k | 6 | 0 | 42.4k | 384 | 1.12e+03 | 0 | - |
| tmux-pane-switch | 27.6 | 40.2 | 0 | - | - | - | 341 | 0.0443 | 0.188 | 60 | 62.5M | 6.85e+03 | 60 | 0 | 540k | 42.4k | 728 | 9 | - |
| fullscreen-redraw | - | - | - | 0.697 | 5 | 0 | 342 | 0.313 | 2.87 | 158 | 316M | 2.49M | 158 | 0 | 2.61M | 10.2k | 12k | 2 | 300 |
| nvim-type | 27.4 | 40.5 | 0 | - | - | - | 345 | 0.0415 | 0.175 | 60 | 111M | 5.86e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 | - |
| tmux-type | 26.2 | 35.7 | 0 | - | - | - | 334 | 0.0182 | 0.0621 | 60 | 2M | 3.7e+03 | 60 | 0 | 17.9k | 42.4k | 728 | 9 | - |
| tmux-type-load | 53.8 | - | - | - | - | - | 342 | 0.554 | 1.48 | 51 | 101M | 10.4M | 51 | 0 | 703k | 25k | 0 | 6 | - |
| tmux-bulk-split | - | - | - | 33.2 | 0.586 | 0.0536 | 332 | 0.315 | 0.378 | 12 | 12.7M | 3.18M | 12 | 0 | 91.4k | 768 | 9.27e+03 | 0 | - |
| box-drawing | - | - | - | 35 | 1.44 | 0.0564 | 342 | 1.32 | 0.126 | 14 | 28M | 88.1k | 14 | 0 | 1.74M | 896 | 64 | 0 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=marco-comp / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sgr-color | - | - | - | 21.3 | 2.36 | 0.103 | 59.3 | 1.98 | 0.581 | 20 | 40.4M | 16.3M | 20 | 0 | - |
| tmux-pane-switch | 27.1 | 52.6 | 0 | - | - | - | 58.3 | 0.0428 | 0.0998 | 60 | 64.7M | 7.97e+03 | 60 | 0 | - |
| shell-echo | 25.6 | 50 | 0 | - | - | - | 57.8 | 0.0155 | 0.0194 | 60 | 2.42M | 3.43e+03 | 60 | 0 | - |
| fullscreen-redraw | - | - | - | 0.708 | 5 | 0.00922 | 59 | 0.317 | 2.16 | 158 | 319M | 3M | 158 | 0 | 300 |
| unicode | - | - | - | 11.6 | 4.47 | 0.0612 | 59.4 | 3.87 | 0.819 | 36 | 72.8M | 8.35M | 36 | 0 | - |
| tmux-bulk-split | - | - | - | 32.7 | 0.585 | 0.0558 | 58.7 | 0.325 | 0.227 | 12 | 12.8M | 2.87M | 12 | 0 | - |
| nvim-type | 26.8 | 53.1 | 0 | - | - | - | 58.8 | 0.0412 | 0.162 | 60 | 113M | 5.83e+03 | 60 | 0 | - |
| tmux-type-load | 70.9 | - | - | - | - | - | 58 | 0.539 | 0.807 | 49 | 98.5M | 7.97M | 48 | 0 | - |
| bulk-ascii | - | - | - | 14.6 | 3.53 | 0.0657 | 58.2 | 2.72 | 0.798 | 29 | 58.6M | 10.2M | 29 | 0 | - |
| nvim-scroll | - | - | - | - | 0.186 | 0.0314 | 58.8 | 0.0635 | 0.0487 | 6 | 11.7M | 390k | 6 | 0 | - |
| tmux-type | 25.6 | 50 | 0 | - | - | - | 58.7 | 0.0166 | 0.0214 | 60 | 2.04M | 4.22e+03 | 60 | 0 | - |
| box-drawing | - | - | - | 35.7 | 1.39 | 0.0686 | 58.6 | 1.3 | 0.0875 | 13 | 26.3M | 147k | 13 | 0 | - |
| compile-log | - | - | - | 18.1 | 1 | 0.0547 | 59 | 0.825 | 0.181 | 10 | 20.2M | 2.14M | 10 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=marco-nocomp / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | - | 0.179 | 0.0376 | 93.9 | 0.0608 | 0.0403 | 6 | 11.7M | 347k | 6 | 0 | 43.5k | 0 | 1.28e+03 | 0 | - |
| sgr-color | - | - | - | 21.1 | 2.36 | 0.122 | 91.5 | 1.99 | 0.56 | 20 | 40.4M | 16.5M | 20 | 0 | 2.16M | 32 | 51.8k | 1 | - |
| unicode | - | - | - | 11.5 | 4.48 | 0.0728 | 89.9 | 3.9 | 0.789 | 36 | 72.8M | 8.32M | 36 | 0 | 9.28M | 96 | 137k | 3 | - |
| fullscreen-redraw | - | - | - | 0.709 | 5 | 0.00357 | 89.2 | 0.302 | 2.01 | 159 | 321M | 2.98M | 159 | 0 | 2.68M | 64 | 11.5k | 2 | 300 |
| tmux-type-load | 70 | - | - | - | - | - | 90.3 | 0.544 | 0.768 | 49 | 98.5M | 8.14M | 49 | 0 | 672k | 21.7k | 0 | 6 | - |
| box-drawing | - | - | - | 35 | 1.44 | 0.0634 | 90.9 | 1.32 | 0.0761 | 14 | 28.3M | 146k | 14 | 0 | 1.73M | 0 | 64 | 0 | - |
| bulk-ascii | - | - | - | 14.7 | 3.52 | 0.0571 | 89.4 | 2.7 | 0.769 | 29 | 58.6M | 10.2M | 29 | 0 | 306k | 0 | 12k | 0 | - |
| tmux-type | 26.2 | 35 | 0 | - | - | - | 90.3 | 0.0172 | 0.0518 | 60 | 2.04M | 4.17e+03 | 60 | 0 | 17.8k | 38.5k | 636 | 9 | - |
| compile-log | - | - | - | 18.3 | 0.995 | 0.0584 | 93.4 | 0.817 | 0.17 | 10 | 20.2M | 2.16M | 10 | 0 | 97k | 0 | 11.7k | 0 | - |
| shell-echo | 26.1 | 35 | 0 | - | - | - | 90.2 | 0.0167 | 0.0507 | 60 | 2.42M | 3.41e+03 | 60 | 0 | 22.1k | 37.5k | 124 | 9 | - |
| nvim-type | 27.3 | 36.7 | 0 | - | - | - | 93.8 | 0.0392 | 0.114 | 60 | 113M | 5.74e+03 | 60 | 0 | 35.2k | 38.5k | 136 | 9 | - |
| tmux-bulk-split | - | - | - | 35.5 | 0.56 | 0.033 | 90.8 | 0.312 | 0.205 | 11 | 12M | 2.65M | 11 | 0 | 86.2k | 0 | 9.14e+03 | 0 | - |
| tmux-pane-switch | 27.6 | 36.8 | 0 | - | - | - | 90.9 | 0.0422 | 0.0891 | 60 | 64.7M | 9.27e+03 | 60 | 0 | 540k | 38.5k | 728 | 9 | - |

### display_kind=xvnc+x11remote / vnc_encoding=zrle / wm=marco-comp / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tmux-type | 26.1 | 50.5 | 0 | - | - | - | 91.9 | 0.0162 | 0.0215 | 60 | 2.04M | 3.62e+03 | 60 | 0 | 17.9k | 38.5k | 728 | 9 | - |
| tmux-pane-switch | 27.6 | 52.9 | 0 | - | - | - | 91.3 | 0.043 | 0.1 | 60 | 64.7M | 6.76e+03 | 60 | 0 | 540k | 38.5k | 728 | 9 | - |
| nvim-scroll | - | - | - | - | 0.181 | 0.0387 | 91.7 | 0.0611 | 0.0636 | 6 | 11.7M | 315k | 6 | 0 | 43.5k | 0 | 1.28e+03 | 0 | - |
| unicode | - | - | - | 11.5 | 4.47 | 0.0996 | 91.6 | 3.91 | 1.38 | 36 | 72.8M | 9.45M | 36 | 0 | 9.25M | 96 | 137k | 3 | - |
| box-drawing | - | - | - | 35.6 | 1.39 | 0.0811 | 91.6 | 1.32 | 0.101 | 13 | 26.3M | 91.4k | 13 | 0 | 1.74M | 0 | 64 | 0 | - |
| fullscreen-redraw | - | - | - | 0.708 | 5 | 0.0124 | 92.6 | 0.308 | 2.54 | 159 | 321M | 2.53M | 159 | 0 | 2.68M | 64 | 11.6k | 2 | 300 |
| shell-echo | 26.1 | 50.5 | 0 | - | - | - | 92.4 | 0.0158 | 0.0198 | 60 | 2.42M | 3.22e+03 | 60 | 0 | 22.1k | 37.5k | 124 | 9 | - |
| bulk-ascii | - | - | - | 14.6 | 3.52 | 0.0729 | 91.6 | 2.72 | 1.43 | 29 | 58.6M | 12.5M | 29 | 0 | 304k | 0 | 12k | 0 | - |
| tmux-type-load | 70.9 | - | - | - | - | - | 91.1 | 0.54 | 1.34 | 49 | 98.5M | 9.99M | 49 | 0 | 672k | 21.7k | 0 | 6 | - |
| compile-log | - | - | - | 18.1 | 1 | 0.0546 | 91.9 | 0.828 | 0.303 | 10 | 20.2M | 2.05M | 10 | 0 | 96.6k | 0 | 11.7k | 0 | - |
| sgr-color | - | - | - | 21.2 | 2.35 | 0.117 | 93 | 1.99 | 1.13 | 20 | 40.4M | 14.9M | 20 | 0 | 2.13M | 32 | 51.8k | 1 | - |
| nvim-type | 27.3 | 53.7 | 0 | - | - | - | 94.2 | 0.0412 | 0.161 | 60 | 113M | 5.7e+03 | 60 | 0 | 35.2k | 38.5k | 136 | 9 | - |
| tmux-bulk-split | - | - | - | 34.1 | 0.573 | 0.0426 | 91.2 | 0.318 | 0.358 | 11 | 12M | 2.99M | 11 | 0 | 86.6k | 0 | 9.14e+03 | 0 | - |

### display_kind=xvnc / vnc_encoding=zrle / wm=marco-comp / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| shell-echo | 25.5 | 50 | 0 | - | - | - | 59.9 | 0.0156 | 0.0197 | 60 | 2.42M | 3.22e+03 | 60 | 0 | - |
| nvim-scroll | - | - | - | - | 0.183 | 0.0355 | 58.8 | 0.0638 | 0.0669 | 6 | 11.7M | 344k | 6 | 0 | - |
| nvim-type | 26.8 | 53.1 | 0 | - | - | - | 58.3 | 0.0411 | 0.162 | 60 | 113M | 5.7e+03 | 60 | 0 | - |
| unicode | - | - | - | 11.5 | 4.47 | 0.0855 | 59.1 | 3.89 | 1.36 | 36 | 72.8M | 9.46M | 36 | 0 | - |
| tmux-bulk-split | - | - | - | 34.3 | 0.564 | 0.0566 | 59.2 | 0.326 | 0.346 | 11 | 11.9M | 2.97M | 11 | 0 | - |
| sgr-color | - | - | - | 21.2 | 2.35 | 0.115 | 60.7 | 1.99 | 1.12 | 20 | 40.4M | 14.8M | 20 | 0 | - |
| fullscreen-redraw | - | - | - | 0.708 | 5 | 0.0129 | 58.9 | 0.314 | 2.54 | 159 | 321M | 2.53M | 159 | 0 | 300 |
| tmux-type | 25.6 | 50.1 | 0 | - | - | - | 59.5 | 0.0159 | 0.0217 | 60 | 2.04M | 3.62e+03 | 60 | 0 | - |
| compile-log | - | - | - | 18.1 | 0.999 | 0.0604 | 58.8 | 0.831 | 0.298 | 10 | 20.2M | 2.07M | 10 | 0 | - |
| tmux-pane-switch | 27.1 | 52.5 | 0 | - | - | - | 58.7 | 0.0437 | 0.101 | 60 | 64.7M | 6.77e+03 | 60 | 0 | - |
| tmux-type-load | 71.1 | - | - | - | - | - | 58.1 | 0.538 | 1.32 | 49 | 98.5M | 9.79M | 48 | 0 | - |
| bulk-ascii | - | - | - | 14.5 | 3.53 | 0.0733 | 57.9 | 2.72 | 1.43 | 29 | 58.6M | 12.5M | 29 | 0 | - |
| box-drawing | - | - | - | 35 | 1.46 | 0.0532 | 59.1 | 1.32 | 0.102 | 14 | 28.3M | 91.3k | 14 | 0 | - |

### display_kind=xvnc / vnc_encoding=zrle / wm=mutter / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| compile-log | - | - | - | 18.1 | 0.997 | 0.0618 | 283 | 0.827 | 0.315 | 10 | 20M | 2.02M | 10 | 0 | - |
| fullscreen-redraw | - | - | - | 0.697 | 5 | 0 | 299 | 0.323 | 2.86 | 158 | 316M | 2.46M | 158 | 0 | 300 |
| tmux-type-load | 53.9 | - | - | - | - | - | 292 | 0.552 | 1.47 | 51 | 101M | 10.4M | 51 | 0 | - |
| box-drawing | - | - | - | 35.6 | 1.38 | 0.0853 | 293 | 1.31 | 0.121 | 13 | 26M | 87.4k | 13 | 0 | - |
| shell-echo | 25.6 | 35.4 | 0 | - | - | - | 270 | 0.018 | 0.0574 | 60 | 2.42M | 3.21e+03 | 60 | 0 | - |
| tmux-bulk-split | - | - | - | 33.5 | 0.582 | 0.0465 | 287 | 0.314 | 0.38 | 12 | 12.7M | 3.19M | 12 | 0 | - |
| sgr-color | - | - | - | 20.6 | 2.48 | 0.0684 | 307 | 2.02 | 1.21 | 21 | 42.1M | 15.4M | 21 | 0 | - |
| tmux-pane-switch | 27 | 39.5 | 0 | - | - | - | 302 | 0.0445 | 0.184 | 60 | 62.5M | 6.83e+03 | 60 | 0 | - |
| unicode | - | - | - | 11.5 | 4.48 | 0.0912 | 297 | 3.91 | 1.39 | 36 | 72.1M | 9.33M | 36 | 0 | - |
| bulk-ascii | - | - | - | 14.6 | 3.53 | 0.0663 | 292 | 2.73 | 1.47 | 29 | 58.1M | 12.4M | 29 | 0 | - |
| nvim-scroll | - | - | - | - | 0.194 | 0.022 | 317 | 0.061 | 0.0736 | 6 | 11.4M | 336k | 6 | 0 | - |
| nvim-type | 26.8 | 40 | 0 | - | - | - | 284 | 0.0424 | 0.174 | 60 | 111M | 5.86e+03 | 60 | 0 | - |
| tmux-type | 25.6 | 35.1 | 0 | - | - | - | 280 | 0.0184 | 0.0626 | 60 | 2M | 3.67e+03 | 60 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=zrle / wm=none / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fullscreen-redraw | - | - | - | 0.721 | 5 | 0.0074 | 85.5 | 0.309 | 2.47 | 159 | 330M | 2.63M | 159 | 0 | 2.73M | 5.27e+03 | 12k | 163 | 300 |
| box-drawing | - | - | - | 35 | 1.45 | 0.0575 | 85.9 | 1.32 | 0.0978 | 14 | 29M | 94.8k | 14 | 0 | 1.83M | 568 | 64 | 16 | - |
| compile-log | - | - | - | 18.2 | 1 | 0.0501 | 85.4 | 0.826 | 0.303 | 10 | 20.7M | 2.1M | 10 | 0 | 98.7k | 440 | 11.7k | 12 | - |
| unicode | - | - | - | 11.5 | 4.48 | 0.0715 | 85.8 | 3.91 | 1.35 | 36 | 74.6M | 9.73M | 36 | 0 | 9.57M | 1.27e+03 | 137k | 38 | - |
| shell-echo | 27 | 36 | 0 | - | - | - | 85.4 | 0.0198 | 0.0511 | 60 | 2.42M | 3.12e+03 | 60 | 0 | 24.9k | 43.2k | 124 | 129 | - |
| tmux-type | 27 | 35.9 | 0 | - | - | - | 89.6 | 0.0205 | 0.0503 | 60 | 2.07M | 6.8e+03 | 60 | 0 | 20.7k | 44.3k | 636 | 129 | - |
| nvim-scroll | - | - | - | - | 0.18 | 0.036 | 85.4 | 0.063 | 0.0638 | 6 | 11.9M | 352k | 6 | 0 | 44.3k | 312 | 1.28e+03 | 8 | - |
| sgr-color | - | - | - | 21.2 | 2.37 | 0.109 | 85.5 | 1.99 | 1.13 | 20 | 41.5M | 15.3M | 20 | 0 | 2.19M | 760 | 51.8k | 22 | - |
| tmux-bulk-split | - | - | - | 33.7 | 0.563 | 0.0468 | 86 | 0.308 | 0.368 | 12 | 13.2M | 3.28M | 12 | 0 | 93.6k | 504 | 9.03e+03 | 14 | - |
| bulk-ascii | - | - | - | 14.6 | 3.54 | 0.0566 | 85.5 | 2.72 | 1.43 | 29 | 60.1M | 12.8M | 29 | 0 | 312k | 1.05e+03 | 12k | 31 | - |
| nvim-type | 27.9 | 37.3 | 0 | - | - | - | 84.7 | 0.0422 | 0.113 | 60 | 116M | 5.62e+03 | 60 | 0 | 38.1k | 44.3k | 136 | 129 | - |
| tmux-pane-switch | 28 | 37.2 | 0 | - | - | - | 85.1 | 0.0455 | 0.0906 | 60 | 64.7M | 9.77e+03 | 60 | 0 | 543k | 44.3k | 728 | 129 | - |
| tmux-type-load | 58.5 | - | - | - | - | - | 85.1 | 0.581 | 1.38 | 51 | 104M | 10.8M | 51 | 0 | 710k | 25.9k | 0 | 97 | - |

### display_kind=xvnc / vnc_encoding=zrle / wm=none / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| box-drawing | - | - | - | 35.5 | 1.4 | 0.0837 | 54.2 | 1.32 | 0.0929 | 13 | 27M | 94.5k | 13 | 0 | - |
| compile-log | - | - | - | 18.2 | 1 | 0.0531 | 59.1 | 0.826 | 0.3 | 10 | 20.7M | 2.1M | 10 | 0 | - |
| tmux-type | 25.6 | 34.5 | 0 | - | - | - | 54.1 | 0.0187 | 0.051 | 60 | 2.07M | 6.75e+03 | 60 | 0 | - |
| tmux-pane-switch | 27 | 36.3 | 0 | - | - | - | 58.9 | 0.0449 | 0.0906 | 60 | 64.7M | 9.77e+03 | 60 | 0 | - |
| bulk-ascii | - | - | - | 14.5 | 3.56 | 0.0697 | 54 | 2.73 | 1.43 | 29 | 60.1M | 12.8M | 29 | 0 | - |
| nvim-type | 26.8 | 36.2 | 0 | - | - | - | 58.9 | 0.0415 | 0.113 | 60 | 116M | 5.62e+03 | 60 | 0 | - |
| sgr-color | - | - | - | 21.2 | 2.36 | 0.11 | 54.4 | 1.98 | 1.12 | 20 | 41.5M | 15.2M | 20 | 0 | - |
| shell-echo | 25.6 | 34.4 | 0 | - | - | - | 54.1 | 0.0182 | 0.0487 | 60 | 2.42M | 3.15e+03 | 60 | 0 | - |
| fullscreen-redraw | - | - | - | 0.722 | 5 | 0.00484 | 59.1 | 0.319 | 2.48 | 159 | 330M | 2.65M | 159 | 0 | 300 |
| tmux-type-load | 57.7 | - | - | - | - | - | 54.1 | 0.589 | 1.36 | 51 | 104M | 10.7M | 51 | 0 | - |
| unicode | - | - | - | 11.5 | 4.47 | 0.073 | 59 | 3.89 | 1.33 | 36 | 74.6M | 9.68M | 36 | 0 | - |
| tmux-bulk-split | - | - | - | 35.3 | 0.554 | 0.046 | 54.2 | 0.305 | 0.357 | 11 | 12.2M | 3.07M | 11 | 0 | - |
| nvim-scroll | - | - | - | - | 0.181 | 0.0344 | 58.9 | 0.0628 | 0.0625 | 6 | 11.9M | 348k | 6 | 0 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=mutter / size=large / font=dejavu

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tmux-type-load | 66.3 | - | - | - | - | - | 206 | 0.529 | 0.772 | 49 | 96.4M | 7.63M | 49 | 0 | - |
| sgr-color | - | - | - | 20.8 | 2.48 | 0.0488 | 221 | 2.01 | 0.632 | 21 | 42.1M | 16.2M | 21 | 0 | - |
| compile-log | - | - | - | 18.3 | 0.994 | 0.054 | 207 | 0.823 | 0.196 | 10 | 20M | 2.1M | 10 | 0 | - |
| tmux-type | 25.7 | 35.2 | 0 | - | - | - | 207 | 0.018 | 0.0625 | 60 | 2M | 4.16e+03 | 60 | 0 | - |
| fullscreen-redraw | - | - | - | 0.624 | 5 | 0.00866 | 213 | 0.292 | 2.42 | 159 | 318M | 3.04M | 159 | 0 | 300 |
| tmux-bulk-split | - | - | - | 34.4 | 0.573 | 0.0376 | 205 | 0.302 | 0.216 | 12 | 12.7M | 2.57M | 12 | 0 | - |
| box-drawing | - | - | - | 35.5 | 1.39 | 0.0858 | 212 | 1.31 | 0.111 | 13 | 26M | 151k | 13 | 0 | - |
| unicode | - | - | - | 11.5 | 4.47 | 0.0811 | 220 | 3.85 | 0.875 | 36 | 72.1M | 8.35M | 36 | 0 | - |
| nvim-type | 26.8 | 39.8 | 0 | - | - | - | 205 | 0.0401 | 0.176 | 60 | 110M | 5.99e+03 | 60 | 0 | - |
| tmux-pane-switch | 26.9 | 38.6 | 0 | - | - | - | 209 | 0.0421 | 0.129 | 60 | 62.2M | 8.97e+03 | 60 | 0 | - |
| shell-echo | 25.6 | 35.2 | 0 | - | - | - | 151 | 0.0179 | 0.0565 | 60 | 2.41M | 3.85e+03 | 60 | 0 | - |
| nvim-scroll | - | - | - | - | 0.191 | 0.0229 | 225 | 0.0589 | 0.0484 | 6 | 11.4M | 378k | 6 | 0 | - |
| bulk-ascii | - | - | - | 14.6 | 3.52 | 0.0581 | 214 | 2.73 | 0.83 | 29 | 58.1M | 9.37M | 29 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tmux-pane-switch | 27.6 | 40.2 | 0 | - | - | - | 263 | 0.044 | 0.186 | 60 | 62.5M | 7.86e+03 | 60 | 0 | 540k | 42.4k | 728 | 9 | - |
| tmux-type | 26.2 | 35.7 | 0 | - | - | - | 264 | 0.0179 | 0.062 | 60 | 2M | 4.42e+03 | 60 | 0 | 17.8k | 42.4k | 636 | 9 | - |
| nvim-scroll | - | - | - | - | 0.198 | 0.0187 | 282 | 0.0627 | 0.0588 | 6 | 11.4M | 384k | 6 | 0 | 42.6k | 384 | 1.28e+03 | 0 | - |
| sgr-color | - | - | - | 21.1 | 2.36 | 0.117 | 267 | 2 | 0.608 | 20 | 40.1M | 16.2M | 20 | 0 | 2.12M | 1.28e+03 | 51.8k | 0 | - |
| unicode | - | - | - | 11.5 | 4.48 | 0.1 | 275 | 3.92 | 0.871 | 36 | 72.1M | 8.19M | 36 | 0 | 9.16M | 2.3e+03 | 137k | 0 | - |
| tmux-bulk-split | - | - | - | 33.9 | 0.582 | 0.0385 | 261 | 0.309 | 0.224 | 12 | 12.7M | 2.82M | 12 | 0 | 91.5k | 768 | 9.14e+03 | 0 | - |
| bulk-ascii | - | - | - | 14.6 | 3.53 | 0.0573 | 263 | 2.72 | 0.845 | 29 | 58.1M | 10M | 29 | 0 | 299k | 1.86e+03 | 12k | 0 | - |
| box-drawing | - | - | - | 35.4 | 1.4 | 0.0739 | 264 | 1.31 | 0.11 | 13 | 26M | 137k | 13 | 0 | 1.67M | 832 | 64 | 0 | - |
| fullscreen-redraw | - | - | - | 0.697 | 5 | 0 | 262 | 0.314 | 2.46 | 158 | 316M | 2.93M | 158 | 0 | 2.61M | 10.2k | 12k | 2 | 300 |
| tmux-type-load | 64.7 | - | - | - | - | - | 264 | 0.538 | 0.903 | 50 | 98.7M | 8.3M | 50 | 0 | 686k | 24.9k | 0 | 6 | - |
| shell-echo | 26.1 | 35.8 | 0 | - | - | - | 265 | 0.0176 | 0.0574 | 60 | 2.42M | 3.43e+03 | 60 | 0 | 22.1k | 41.3k | 124 | 9 | - |
| compile-log | - | - | - | 18.4 | 0.992 | 0.0559 | 265 | 0.82 | 0.19 | 10 | 20M | 2.13M | 10 | 0 | 95.8k | 640 | 11.7k | 0 | - |
| nvim-type | 27.4 | 40.4 | 0 | - | - | - | 271 | 0.0415 | 0.173 | 60 | 111M | 5.99e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 | - |

### display_kind=xvnc+x11remote / vnc_encoding=zrle / wm=marco-nocomp / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| compile-log | - | - | - | 18.3 | 1 | 0.0511 | 90.1 | 0.821 | 0.3 | 10 | 20.2M | 2.07M | 10 | 0 | 97k | 0 | 11.7k | 0 | - |
| unicode | - | - | - | 11.5 | 4.47 | 0.101 | 89.4 | 3.93 | 1.34 | 36 | 72.8M | 9.46M | 36 | 0 | 9.3M | 96 | 137k | 3 | - |
| nvim-type | 27.3 | 36.5 | 0 | - | - | - | 91 | 0.0388 | 0.113 | 60 | 113M | 5.61e+03 | 60 | 0 | 35.2k | 38.5k | 136 | 9 | - |
| box-drawing | - | - | - | 35.7 | 1.39 | 0.0732 | 89.2 | 1.3 | 0.0935 | 13 | 26.3M | 91.8k | 13 | 0 | 1.79M | 0 | 64 | 0 | - |
| nvim-scroll | - | - | - | - | 0.185 | 0.0327 | 90.2 | 0.0621 | 0.0619 | 6 | 11.7M | 349k | 6 | 0 | 43.2k | 0 | 1.12e+03 | 0 | - |
| tmux-type-load | 59 | - | - | - | - | - | 90.3 | 0.564 | 1.32 | 51 | 103M | 10.1M | 50 | 0 | 697k | 21.7k | 0 | 6 | - |
| bulk-ascii | - | - | - | 14.6 | 3.53 | 0.0855 | 90.8 | 2.74 | 1.41 | 29 | 58.6M | 12.5M | 29 | 0 | 305k | 0 | 12k | 0 | - |
| tmux-type | 26.1 | 34.9 | 0 | - | - | - | 90.7 | 0.0167 | 0.0515 | 60 | 2.04M | 3.77e+03 | 60 | 0 | 17.9k | 38.5k | 728 | 9 | - |
| fullscreen-redraw | - | - | - | 0.709 | 5 | 0.00493 | 90 | 0.304 | 2.42 | 159 | 321M | 2.51M | 159 | 0 | 2.68M | 64 | 11.8k | 2 | 300 |
| tmux-pane-switch | 27.6 | 36.8 | 0 | - | - | - | 90.5 | 0.0423 | 0.0913 | 60 | 64.7M | 8.23e+03 | 60 | 0 | 540k | 38.5k | 728 | 9 | - |
| tmux-bulk-split | - | - | - | 35.3 | 0.555 | 0.0419 | 90.3 | 0.307 | 0.352 | 11 | 12M | 2.96M | 11 | 0 | 86k | 0 | 9.14e+03 | 0 | - |
| sgr-color | - | - | - | 21.1 | 2.36 | 0.124 | 89.9 | 2 | 1.1 | 20 | 40.4M | 14.9M | 20 | 0 | 2.14M | 32 | 51.8k | 1 | - |
| shell-echo | 26.2 | 35 | 0 | - | - | - | 90.7 | 0.0166 | 0.0495 | 60 | 2.42M | 3.22e+03 | 60 | 0 | 22.1k | 37.5k | 124 | 9 | - |

## rtt-sweep preset (xvnc+x11remote, Tight, mutter)


### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=20 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | - | 0.173 | 0.553 | 1.83e+03 | 0.2 | 0.0977 | 6 | 6.92M | 1.04M | 7 | 0 | 32k | 1.14e+03 | 9.19e+03 | 19 |
| shell-echo | 46 | 55.7 | 1 | - | - | - | 1.84e+03 | 0.0188 | 0.0785 | 61 | 6.38M | 5.56e+03 | 61 | 0 | 22.8k | 43.2k | 316 | 27 |
| bulk-ascii | - | - | - | 13 | 3.95 | 0.0829 | 1.82e+03 | 2.74 | 0.9 | 30 | 60.1M | 10.9M | 31 | 0 | 301k | 2.67e+03 | 12k | 19 |
| nvim-type | 47.3 | 60.4 | 1 | - | - | - | 1.83e+03 | 0.045 | 0.247 | 61 | 113M | 881k | 62 | 0 | 39k | 43.2k | 2.57e+03 | 28 |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | - | 0.194 | 0.0223 | 304 | 0.0614 | 0.0576 | 6 | 11.4M | 378k | 6 | 0 | 42.6k | 384 | 1.28e+03 | 0 |
| bulk-ascii | - | - | - | 14.6 | 3.53 | 0.058 | 294 | 2.72 | 0.842 | 29 | 58.1M | 9.98M | 29 | 0 | 298k | 1.86e+03 | 12k | 0 |
| shell-echo | 26.1 | 35.8 | 0 | - | - | - | 267 | 0.0172 | 0.0618 | 60 | 2.42M | 3.43e+03 | 60 | 0 | 22.1k | 42.4k | 124 | 9 |
| nvim-type | 27.4 | 40.5 | 0 | - | - | - | 304 | 0.0416 | 0.172 | 60 | 111M | 5.99e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=2 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bulk-ascii | - | - | - | 14.6 | 3.53 | 0.0585 | 437 | 2.72 | 0.852 | 29 | 58.1M | 9.98M | 29 | 0 | 301k | 1.86e+03 | 12k | 0 |
| nvim-type | 29.2 | 42.4 | 0 | - | - | - | 437 | 0.0512 | 0.175 | 60 | 111M | 5.99e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 |
| shell-echo | 27.9 | 37.6 | 0 | - | - | - | 441 | 0.0176 | 0.0647 | 60 | 2.42M | 3.43e+03 | 60 | 0 | 22.1k | 42.4k | 124 | 9 |
| nvim-scroll | - | - | - | - | 0.19 | 0.0271 | 435 | 0.0607 | 0.0572 | 6 | 11.4M | 381k | 6 | 0 | 42.8k | 384 | 1.28e+03 | 0 |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=0 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | latency_multi_paint | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-type | 27.1 | 40.3 | 0 | - | - | - | 250 | 0.0522 | 0.176 | 60 | 111M | 5.99e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 |
| shell-echo | 25.8 | 35.4 | 0 | - | - | - | 266 | 0.0181 | 0.0647 | 60 | 2.42M | 3.43e+03 | 60 | 0 | 22.1k | 42.4k | 124 | 9 |
| nvim-scroll | - | - | - | - | 0.189 | 0.0272 | 247 | 0.0611 | 0.0584 | 6 | 11.4M | 387k | 6 | 0 | 42.6k | 384 | 1.28e+03 | 0 |
| bulk-ascii | - | - | - | 14.6 | 3.52 | 0.071 | 251 | 2.72 | 0.849 | 29 | 58.1M | 9.97M | 29 | 0 | 298k | 1.86e+03 | 12k | 0 |
