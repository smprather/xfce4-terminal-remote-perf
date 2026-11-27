# Baseline medians, EL8 (2026-11-27)

Every el8 configuration of the `full` and `rtt-sweep` presets, build `baseline` (EPEL8 xfce4-terminal
1.0.4 + VTE 0.52.4). Medians over 7 iterations (5 for the size/font block and the RTT sweep); latency
columns pool every keystroke sample. Raw totals, not per key: divide typing-workload counters by 40
(Xvfb) or 60 (VNC: 40 X-side + 20 end-to-end keys). Commentary: [2026-11-27-baseline.md](2026-11-27-baseline.md).

## full preset


### display_kind=xvfb / wm=none / size=large / font=caskaydia

| workload | latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | frames |
|---|---|---|---|---|---|---|---|---|---|---|
| sgr-color | - | 21.3 | 2.36 | 0.0998 | 59.2 | 1.9 | 0.101 | 20 | 50.2M | - |
| unicode | - | 11.6 | 4.47 | 0.0638 | 60.6 | 3.84 | 0.223 | 36 | 90.3M | - |
| box-drawing | - | 34.6 | 1.44 | 0.074 | 59.6 | 1.27 | 0.0409 | 14 | 35.1M | - |
| nvim-type | 27 | - | - | - | 59.3 | 0.0297 | 0.0545 | 40 | 95M | - |
| bulk-ascii | - | 14.7 | 3.51 | 0.0593 | 58.9 | 2.67 | 0.106 | 29 | 72.8M | - |
| shell-echo | 25.6 | - | - | - | 56 | 0.0117 | 0.00541 | 40 | 1.79M | - |
| tmux-bulk-split | - | 35.2 | 0.552 | 0.0385 | 55.9 | 0.303 | 0.0242 | 11 | 14.9M | - |
| compile-log | - | 18.3 | 1 | 0.0505 | 55 | 0.794 | 0.0313 | 10 | 25.1M | - |
| tmux-type | 25.6 | - | - | - | 59.1 | 0.012 | 0.00596 | 40 | 2.53M | - |
| nvim-scroll | - | - | 0.185 | 0.0322 | 56.4 | 0.0612 | 0.0135 | 6 | 14.6M | - |
| fullscreen-redraw | - | 0.883 | 5 | 0.0154 | 59.3 | 0.364 | 0.58 | 156 | 391M | 300 |

### display_kind=xvfb / wm=marco-comp / size=large / font=caskaydia

| workload | latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | frames |
|---|---|---|---|---|---|---|---|---|---|---|
| tmux-type | 25.6 | - | - | - | 59.8 | 0.0107 | 0.0114 | 40 | 1.97M | - |
| compile-log | - | 18.3 | 0.999 | 0.0499 | 59.4 | 0.797 | 0.0382 | 10 | 19.5M | - |
| sgr-color | - | 21.4 | 2.35 | 0.102 | 58.6 | 1.9 | 0.106 | 20 | 39.1M | - |
| nvim-scroll | - | - | 0.183 | 0.0322 | 58.9 | 0.0598 | 0.017 | 6 | 11.3M | - |
| nvim-type | 26.8 | - | - | - | 59.5 | 0.0257 | 0.079 | 40 | 73.5M | - |
| tmux-bulk-split | - | 35.7 | 0.549 | 0.0334 | 61.8 | 0.297 | 0.029 | 11 | 11.5M | - |
| bulk-ascii | - | 14.9 | 3.42 | 0.108 | 59.2 | 2.63 | 0.123 | 28 | 54.7M | - |
| shell-echo | 25.6 | - | - | - | 61.4 | 0.0104 | 0.00991 | 40 | 1.6M | - |
| unicode | - | 11.6 | 4.47 | 0.0599 | 61.7 | 3.83 | 0.229 | 36 | 70.4M | - |
| fullscreen-redraw | - | 0.883 | 5 | 0.0141 | 59.5 | 0.296 | 0.538 | 156 | 305M | 300 |
| box-drawing | - | 35.6 | 1.39 | 0.0789 | 61.2 | 1.24 | 0.0428 | 13 | 25.4M | - |

### display_kind=xvnc / vnc_encoding=zrle / wm=marco-nocomp / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 58.5 | 0.295 | 1.54 | 155 | 303M | 1.52M | 155 | 0 | 300 |
| sgr-color | - | - | 21.2 | 2.36 | 0.116 | 58.7 | 1.9 | 1.1 | 20 | 39.1M | 14.8M | 20 | 0 | - |
| box-drawing | - | - | 35.4 | 1.4 | 0.0723 | 58 | 1.25 | 0.0918 | 13 | 25.4M | 94.5k | 13 | 0 | - |
| unicode | - | - | 11.5 | 4.48 | 0.072 | 59.5 | 3.83 | 1.29 | 36 | 70.4M | 9.34M | 36 | 0 | - |
| nvim-scroll | - | - | - | 0.189 | 0.0269 | 57.7 | 0.0575 | 0.0621 | 6 | 11.3M | 349k | 6 | 0 | - |
| shell-echo | 25.6 | 34.4 | - | - | - | 58 | 0.0165 | 0.05 | 60 | 2.4M | 3.23e+03 | 60 | 0 | - |
| compile-log | - | - | 18.2 | 0.995 | 0.0643 | 58.1 | 0.792 | 0.29 | 10 | 19.5M | 2.06M | 10 | 0 | - |
| tmux-bulk-split | - | - | 34.7 | 0.575 | 0.0425 | 58.2 | 0.295 | 0.343 | 11 | 11.5M | 2.9M | 11 | 0 | - |
| bulk-ascii | - | - | 14.6 | 3.52 | 0.0652 | 58.8 | 2.69 | 1.39 | 29 | 56.7M | 12.2M | 29 | 0 | - |
| nvim-type | 26.7 | 36.1 | - | - | - | 58.3 | 0.0378 | 0.112 | 60 | 110M | 8.34e+03 | 60 | 0 | - |
| tmux-type | 25.6 | 34.4 | - | - | - | 57.5 | 0.0171 | 0.0526 | 60 | 1.98M | 3.76e+03 | 60 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=none / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tmux-bulk-split | - | - | 33.8 | 0.574 | 0.0328 | 90.7 | 0.296 | 0.243 | 12 | 16.1M | 3.13M | 12 | 0 | 107k | 504 | 9.08e+03 | 14 | - |
| bulk-ascii | - | - | 14.6 | 3.53 | 0.0696 | 87.2 | 2.68 | 0.81 | 29 | 72.8M | 10.6M | 29 | 0 | 340k | 1.05e+03 | 12k | 31 | - |
| box-drawing | - | - | 34.8 | 1.44 | 0.063 | 87.7 | 1.28 | 0.0903 | 14 | 35.1M | 159k | 14 | 0 | 2.11M | 568 | 64 | 16 | - |
| nvim-scroll | - | - | - | 0.182 | 0.0372 | 86.8 | 0.06 | 0.0463 | 6 | 14.6M | 369k | 6 | 0 | 48.4k | 312 | 1.12e+03 | 8 | - |
| unicode | - | - | 11.6 | 4.46 | 0.0843 | 91.3 | 3.84 | 0.828 | 36 | 90.3M | 8.69M | 36 | 0 | 10.5M | 1.27e+03 | 137k | 38 | - |
| shell-echo | 27 | 35.9 | - | - | - | 87.1 | 0.0196 | 0.049 | 60 | 2.68M | 3.31e+03 | 60 | 0 | 24.9k | 44.3k | 124 | 129 | - |
| sgr-color | - | - | 21.2 | 2.37 | 0.107 | 87.3 | 1.9 | 0.59 | 20 | 50.2M | 17.1M | 20 | 0 | 2.39M | 760 | 51.8k | 22 | - |
| compile-log | - | - | 18.2 | 1 | 0.0541 | 86.5 | 0.797 | 0.179 | 10 | 25.1M | 2.24M | 10 | 0 | 107k | 440 | 11.7k | 12 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 86.8 | 0.369 | 2.16 | 155 | 389M | 3M | 155 | 0 | 3.21M | 5.14e+03 | 12k | 159 | 300 |
| nvim-type | 28.1 | 37.6 | - | - | - | 89.4 | 0.0462 | 0.126 | 60 | 143M | 3.57e+03 | 60 | 0 | 38k | 44.3k | 136 | 129 | - |
| tmux-type | 27 | 35.8 | - | - | - | 89.5 | 0.0197 | 0.0509 | 60 | 2.53M | 6.4e+03 | 60 | 0 | 20.7k | 44.3k | 728 | 129 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=mutter / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| box-drawing | - | - | 35.7 | 1.4 | 0.0733 | 258 | 1.24 | 0.111 | 13 | 26M | 142k | 13 | 0 | - |
| compile-log | - | - | 18.2 | 0.999 | 0.0504 | 257 | 0.801 | 0.19 | 10 | 20M | 2.13M | 10 | 0 | - |
| tmux-type | 25.6 | 35.2 | - | - | - | 246 | 0.0185 | 0.0615 | 60 | 2M | 4.3e+03 | 60 | 0 | - |
| nvim-type | 26.9 | 39.9 | - | - | - | 251 | 0.0434 | 0.173 | 60 | 111M | 5.99e+03 | 60 | 0 | - |
| shell-echo | 25.6 | 35.3 | - | - | - | 213 | 0.0184 | 0.0619 | 60 | 2.42M | 3.43e+03 | 60 | 0 | - |
| bulk-ascii | - | - | 14.5 | 3.53 | 0.0758 | 249 | 2.68 | 0.847 | 29 | 58.1M | 10M | 29 | 0 | - |
| sgr-color | - | - | 21.2 | 2.36 | 0.111 | 222 | 1.91 | 0.614 | 20 | 40.1M | 16.1M | 20 | 0 | - |
| unicode | - | - | 11.5 | 4.47 | 0.0872 | 224 | 3.83 | 0.848 | 36 | 72.1M | 8.16M | 36 | 0 | - |
| nvim-scroll | - | - | - | 0.194 | 0.0224 | 223 | 0.0576 | 0.0581 | 6 | 11.4M | 384k | 6 | 0 | - |
| tmux-bulk-split | - | - | 33.7 | 0.577 | 0.0441 | 246 | 0.298 | 0.218 | 12 | 12.6M | 2.78M | 12 | 0 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 258 | 0.313 | 1.7 | 155 | 310M | 2.26M | 155 | 0 | 300 |

### display_kind=xvfb / wm=marco-nocomp / size=large / font=caskaydia

| workload | latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | frames |
|---|---|---|---|---|---|---|---|---|---|---|
| compile-log | - | 18.3 | 0.996 | 0.0519 | 59.1 | 0.797 | 0.0269 | 10 | 19.5M | - |
| tmux-type | 25.6 | - | - | - | 58.9 | 0.0106 | 0.00591 | 40 | 1.97M | - |
| box-drawing | - | 35.4 | 1.41 | 0.0651 | 59.1 | 1.26 | 0.0307 | 13 | 25.4M | - |
| unicode | - | 11.6 | 4.47 | 0.0532 | 58.6 | 3.83 | 0.192 | 36 | 70.4M | - |
| sgr-color | - | 21.4 | 2.36 | 0.0998 | 58.1 | 1.9 | 0.0883 | 20 | 39.1M | - |
| tmux-bulk-split | - | 35.6 | 0.551 | 0.0313 | 57.9 | 0.287 | 0.0197 | 11 | 11.5M | - |
| nvim-scroll | - | - | 0.184 | 0.0308 | 57.7 | 0.0565 | 0.0109 | 6 | 11.3M | - |
| bulk-ascii | - | 14.7 | 3.52 | 0.0488 | 58 | 2.66 | 0.0949 | 29 | 56.7M | - |
| shell-echo | 25.6 | - | - | - | 62.4 | 0.0102 | 0.0055 | 40 | 1.6M | - |
| fullscreen-redraw | - | 0.884 | 5 | 0.00886 | 58.9 | 0.287 | 0.362 | 156 | 305M | 300 |
| nvim-type | 26.7 | - | - | - | 57.6 | 0.0241 | 0.0435 | 40 | 73.5M | - |

### display_kind=xvnc / vnc_encoding=tight / wm=mutter / size=small / font=dejavu

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| box-drawing | - | - | 35.7 | 1.38 | 0.0831 | 160 | 1.22 | 0.0556 | 13 | 11.9M | 146k | 13 | 0 | - |
| shell-echo | 25.6 | 34.9 | - | - | - | 141 | 0.0176 | 0.048 | 60 | 1.51M | 10.2k | 60 | 0 | - |
| unicode | - | - | 11.6 | 4.47 | 0.0617 | 150 | 3.74 | 0.555 | 36 | 33M | 7.86M | 36 | 0 | - |
| bulk-ascii | - | - | 14.5 | 3.54 | 0.0808 | 153 | 2.69 | 0.376 | 29 | 26.6M | 6.63M | 29 | 0 | - |
| tmux-bulk-split | - | - | 36.5 | 0.54 | 0.0355 | 144 | 0.224 | 0.108 | 13 | 6.29M | 1.86M | 13 | 0 | - |
| fullscreen-redraw | - | - | 0.293 | 5 | 0 | 162 | 0.157 | 1.07 | 160 | 147M | 1.92M | 161 | 0 | 300 |
| sgr-color | - | - | 21.3 | 2.36 | 0.102 | 125 | 1.89 | 0.31 | 20 | 18.3M | 8M | 20 | 0 | - |
| nvim-type | 26.2 | 37.1 | - | - | - | 155 | 0.0285 | 0.0999 | 60 | 49.6M | 17.5k | 60 | 0 | - |
| tmux-type | 25.6 | 34.7 | - | - | - | 153 | 0.0173 | 0.0452 | 60 | 944k | 17.3k | 60 | 0 | - |
| nvim-scroll | - | - | - | 0.187 | 0.0204 | 159 | 0.0493 | 0.0315 | 6 | 5.24M | 297k | 6 | 0 | - |
| compile-log | - | - | 18.4 | 1 | 0.0385 | 143 | 0.813 | 0.127 | 10 | 9.16M | 1.66M | 10 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=marco-comp / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | 0.185 | 0.0308 | 95 | 0.0566 | 0.0488 | 6 | 11.3M | 382k | 6 | 0 | 42.5k | 0 | 1.12e+03 | 0 | - |
| shell-echo | 26.1 | 50.5 | - | - | - | 95.2 | 0.0154 | 0.0195 | 60 | 2.4M | 3.31e+03 | 60 | 0 | 22.1k | 38.5k | 124 | 9 | - |
| nvim-type | 27.3 | 53.7 | - | - | - | 95.2 | 0.0412 | 0.16 | 60 | 110M | 5.81e+03 | 60 | 0 | 35.2k | 38.5k | 136 | 9 | - |
| tmux-bulk-split | - | - | 33.1 | 0.576 | 0.0508 | 94.3 | 0.298 | 0.219 | 12 | 12.5M | 2.79M | 12 | 0 | 91.8k | 0 | 9.2e+03 | 0 | - |
| unicode | - | - | 11.5 | 4.48 | 0.0887 | 95.2 | 3.85 | 0.821 | 36 | 70.4M | 8.2M | 36 | 0 | 9.2M | 96 | 137k | 3 | - |
| tmux-type | 26 | 50.5 | - | - | - | 95.4 | 0.0162 | 0.0212 | 60 | 1.98M | 4.22e+03 | 60 | 0 | 17.9k | 38.5k | 728 | 9 | - |
| fullscreen-redraw | - | - | 0.884 | 5 | 0.0104 | 95.1 | 0.309 | 1.4 | 156 | 305M | 2.33M | 156 | 0 | 1.48M | 64 | 12k | 2 | 300 |
| compile-log | - | - | 18.1 | 1 | 0.0569 | 94.8 | 0.802 | 0.172 | 10 | 19.5M | 2.11M | 10 | 0 | 96.4k | 0 | 11.7k | 0 | - |
| bulk-ascii | - | - | 14.6 | 3.52 | 0.0527 | 95.1 | 2.69 | 0.789 | 29 | 56.7M | 9.98M | 29 | 0 | 300k | 0 | 12k | 0 | - |
| sgr-color | - | - | 21.2 | 2.35 | 0.114 | 93.2 | 1.9 | 0.586 | 20 | 39.1M | 16.1M | 20 | 0 | 2.1M | 32 | 51.8k | 1 | - |
| box-drawing | - | - | 35.6 | 1.4 | 0.0704 | 95.8 | 1.25 | 0.0848 | 13 | 25.4M | 141k | 13 | 0 | 1.66M | 0 | 64 | 0 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=mutter / size=small / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-type | 26.2 | 36.9 | - | - | - | 112 | 0.0284 | 0.0957 | 60 | 44.7M | 18.4k | 60 | 0 | - |
| bulk-ascii | - | - | 14.5 | 3.54 | 0.0862 | 141 | 2.69 | 0.381 | 29 | 23.9M | 6.72M | 29 | 0 | - |
| tmux-type | 25.6 | 34.7 | - | - | - | 110 | 0.0173 | 0.0438 | 60 | 851k | 17.1k | 60 | 0 | - |
| fullscreen-redraw | - | - | 0.293 | 5 | 0 | 150 | 0.155 | 1.01 | 160 | 132M | 1.87M | 161 | 0 | 300 |
| shell-echo | 25.6 | 34.8 | - | - | - | 209 | 0.0171 | 0.0457 | 60 | 1.36M | 9.23e+03 | 60 | 0 | - |
| compile-log | - | - | 18.5 | 0.999 | 0.0504 | 133 | 0.793 | 0.122 | 10 | 8.24M | 1.67M | 10 | 0 | - |
| unicode | - | - | 11.6 | 4.47 | 0.0542 | 143 | 3.78 | 0.537 | 36 | 29.7M | 7.57M | 36 | 0 | - |
| sgr-color | - | - | 21.3 | 2.35 | 0.106 | 151 | 1.89 | 0.322 | 20 | 16.5M | 8.41M | 20 | 0 | - |
| box-drawing | - | - | 35.8 | 1.39 | 0.0749 | 150 | 1.23 | 0.0491 | 13 | 10.7M | 131k | 13 | 0 | - |
| tmux-bulk-split | - | - | 36.5 | 0.534 | 0.0352 | 138 | 0.224 | 0.101 | 13 | 5.67M | 1.71M | 13 | 0 | - |
| nvim-scroll | - | - | - | 0.186 | 0.0214 | 151 | 0.0508 | 0.0301 | 6 | 4.72M | 281k | 6 | 0 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=marco-nocomp / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | 0.191 | 0.025 | 59.7 | 0.0584 | 0.0427 | 6 | 11.3M | 377k | 6 | 0 | - |
| bulk-ascii | - | - | 14.7 | 3.52 | 0.0489 | 57.8 | 2.69 | 0.716 | 29 | 56.7M | 12.3M | 29 | 0 | - |
| tmux-bulk-split | - | - | 33.7 | 0.566 | 0.0311 | 58.1 | 0.296 | 0.208 | 12 | 12.5M | 3.32M | 12 | 0 | - |
| sgr-color | - | - | 21.3 | 2.35 | 0.109 | 57.7 | 1.9 | 0.554 | 20 | 39.1M | 16.1M | 20 | 0 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 58.3 | 0.294 | 1.27 | 155 | 303M | 2.56M | 155 | 0 | 300 |
| box-drawing | - | - | 35.4 | 1.39 | 0.0925 | 58.5 | 1.24 | 0.0757 | 13 | 25.4M | 145k | 13 | 0 | - |
| shell-echo | 25.6 | 34.4 | - | - | - | 58 | 0.0164 | 0.0513 | 60 | 2.4M | 3.4e+03 | 60 | 0 | - |
| tmux-type | 25.7 | 34.5 | - | - | - | 58.7 | 0.0169 | 0.0519 | 60 | 1.98M | 4.17e+03 | 60 | 0 | - |
| unicode | - | - | 11.6 | 4.48 | 0.0633 | 59.1 | 3.83 | 0.758 | 36 | 70.4M | 8.77M | 36 | 0 | - |
| compile-log | - | - | 18.3 | 0.998 | 0.0538 | 59 | 0.798 | 0.168 | 10 | 19.5M | 2.12M | 10 | 0 | - |
| nvim-type | 26.7 | 36.1 | - | - | - | 59 | 0.038 | 0.112 | 60 | 110M | 8.35e+03 | 60 | 0 | - |

### display_kind=xvfb / wm=mutter / size=large / font=caskaydia

| workload | latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | frames |
|---|---|---|---|---|---|---|---|---|---|---|
| shell-echo | 25.6 | - | - | - | 76 | 0.0119 | 0.0295 | 40 | 1.61M | - |
| box-drawing | - | 35.6 | 1.4 | 0.0751 | 73.7 | 1.24 | 0.0419 | 13 | 26M | - |
| nvim-type | 26.8 | - | - | - | 68.2 | 0.0271 | 0.0758 | 40 | 74.2M | - |
| tmux-bulk-split | - | 33.7 | 0.574 | 0.0455 | 72.8 | 0.297 | 0.0313 | 12 | 12.6M | - |
| nvim-scroll | - | - | 0.192 | 0.0241 | 72.4 | 0.0575 | 0.0172 | 6 | 11.4M | - |
| fullscreen-redraw | - | 0.885 | 5 | 0 | 70.8 | 0.309 | 0.549 | 155 | 310M | 300 |
| bulk-ascii | - | 14.7 | 3.52 | 0.0509 | 76.4 | 2.68 | 0.124 | 29 | 58.1M | - |
| tmux-type | 25.6 | - | - | - | 72.7 | 0.0122 | 0.0301 | 40 | 1.99M | - |
| unicode | - | 11.5 | 4.47 | 0.0729 | 74.2 | 3.83 | 0.224 | 36 | 72.1M | - |
| sgr-color | - | 21.3 | 2.36 | 0.101 | 72.9 | 1.91 | 0.104 | 20 | 40.1M | - |
| compile-log | - | 18.2 | 0.998 | 0.0528 | 74 | 0.795 | 0.0378 | 10 | 20M | - |

### display_kind=xvnc+x11remote / vnc_encoding=zrle / wm=mutter / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sgr-color | - | - | 20.4 | 2.49 | 0.0783 | 346 | 2.01 | 1.19 | 21 | 42.1M | 15.1M | 21 | 0 | 2.18M | 1.34e+03 | 51.8k | 0 | - |
| compile-log | - | - | 18.2 | 1 | 0.0551 | 322 | 0.803 | 0.314 | 10 | 20M | 2.02M | 10 | 0 | 95.7k | 640 | 11.7k | 0 | - |
| unicode | - | - | 11.4 | 4.48 | 0.113 | 339 | 3.86 | 1.42 | 36 | 72.1M | 9.33M | 36 | 0 | 9.16M | 2.3e+03 | 137k | 0 | - |
| bulk-ascii | - | - | 14.6 | 3.53 | 0.0656 | 343 | 2.69 | 1.46 | 29 | 58.1M | 12.3M | 29 | 0 | 300k | 1.86e+03 | 12k | 0 | - |
| shell-echo | 26.2 | 35.8 | - | - | - | 329 | 0.0171 | 0.0612 | 60 | 2.42M | 3.21e+03 | 60 | 0 | 22.1k | 42.4k | 124 | 9 | - |
| nvim-scroll | - | - | - | 0.192 | 0.0246 | 349 | 0.0575 | 0.0726 | 6 | 11.4M | 310k | 6 | 0 | 42.8k | 384 | 1.28e+03 | 0 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 336 | 0.31 | 1.98 | 155 | 310M | 1.3M | 155 | 0 | 1.47M | 9.98e+03 | 12k | 2 | 300 |
| nvim-type | 27.4 | 40.5 | - | - | - | 341 | 0.0414 | 0.171 | 60 | 111M | 5.86e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 | - |
| tmux-type | 26.2 | 35.7 | - | - | - | 345 | 0.0178 | 0.0608 | 60 | 2M | 3.69e+03 | 60 | 0 | 17.9k | 42.4k | 728 | 9 | - |
| tmux-bulk-split | - | - | 33.4 | 0.578 | 0.0458 | 328 | 0.297 | 0.369 | 12 | 12.6M | 3.12M | 12 | 0 | 91.2k | 768 | 9.2e+03 | 0 | - |
| box-drawing | - | - | 35.5 | 1.4 | 0.0738 | 340 | 1.25 | 0.128 | 13 | 26M | 90.6k | 13 | 0 | 1.83M | 832 | 64 | 0 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=marco-comp / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sgr-color | - | - | 21.3 | 2.36 | 0.106 | 60.9 | 1.9 | 0.569 | 20 | 39.1M | 16M | 20 | 0 | - |
| shell-echo | 25.6 | 50.1 | - | - | - | 60.4 | 0.0157 | 0.0201 | 60 | 2.4M | 3.31e+03 | 60 | 0 | - |
| fullscreen-redraw | - | - | 0.884 | 5 | 0.00546 | 60.7 | 0.301 | 1.4 | 156 | 305M | 2.33M | 156 | 0 | 300 |
| unicode | - | - | 11.6 | 4.47 | 0.073 | 60.4 | 3.83 | 0.796 | 36 | 70.4M | 8.18M | 36 | 0 | - |
| tmux-bulk-split | - | - | 35 | 0.551 | 0.0482 | 60.7 | 0.296 | 0.204 | 11 | 11.5M | 2.56M | 11 | 0 | - |
| nvim-type | 26.8 | 53 | - | - | - | 60.4 | 0.0406 | 0.16 | 60 | 110M | 5.81e+03 | 60 | 0 | - |
| bulk-ascii | - | - | 14.6 | 3.53 | 0.0658 | 60.2 | 2.69 | 0.779 | 29 | 56.7M | 9.99M | 29 | 0 | - |
| nvim-scroll | - | - | - | 0.186 | 0.0298 | 60.1 | 0.0597 | 0.0474 | 6 | 11.3M | 383k | 6 | 0 | - |
| tmux-type | 25.6 | 50 | - | - | - | 61.6 | 0.0161 | 0.0213 | 60 | 1.98M | 4.22e+03 | 60 | 0 | - |
| box-drawing | - | - | 35 | 1.41 | 0.0746 | 61.7 | 1.25 | 0.0842 | 13 | 25.4M | 143k | 13 | 0 | - |
| compile-log | - | - | 18.1 | 0.996 | 0.0618 | 60.4 | 0.797 | 0.172 | 10 | 19.5M | 2.11M | 10 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=marco-nocomp / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | 0.185 | 0.0319 | 90.6 | 0.0582 | 0.0398 | 6 | 11.3M | 340k | 6 | 0 | 42.7k | 0 | 1.28e+03 | 0 | - |
| sgr-color | - | - | 21.2 | 2.36 | 0.113 | 93.9 | 1.9 | 0.556 | 20 | 39.1M | 16.1M | 20 | 0 | 2.1M | 32 | 51.8k | 1 | - |
| unicode | - | - | 11.5 | 4.48 | 0.0862 | 91.4 | 3.85 | 0.789 | 36 | 70.4M | 8.77M | 36 | 0 | 9.16M | 96 | 137k | 3 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 92.5 | 0.295 | 1.26 | 155 | 303M | 2.58M | 155 | 0 | 1.47M | 64 | 12k | 2 | 300 |
| box-drawing | - | - | 35.1 | 1.4 | 0.072 | 91.7 | 1.25 | 0.0753 | 13 | 25.4M | 146k | 13 | 0 | 1.76M | 0 | 64 | 0 | - |
| bulk-ascii | - | - | 14.7 | 3.52 | 0.0457 | 91.4 | 2.69 | 0.729 | 29 | 56.7M | 12.4M | 29 | 0 | 300k | 0 | 12k | 0 | - |
| tmux-type | 26.1 | 34.9 | - | - | - | 91.6 | 0.0166 | 0.0496 | 60 | 1.98M | 4.15e+03 | 60 | 0 | 17.9k | 38.5k | 728 | 9 | - |
| compile-log | - | - | 18.3 | 1 | 0.0497 | 91.9 | 0.798 | 0.167 | 10 | 19.5M | 2.12M | 10 | 0 | 95.5k | 0 | 11.7k | 0 | - |
| shell-echo | 26.1 | 35 | - | - | - | 91.1 | 0.0166 | 0.0507 | 60 | 2.4M | 3.4e+03 | 60 | 0 | 22.1k | 38.5k | 124 | 9 | - |
| nvim-type | 27.3 | 36.6 | - | - | - | 93.7 | 0.0388 | 0.11 | 60 | 110M | 8.35e+03 | 60 | 0 | 35.2k | 38.5k | 136 | 9 | - |
| tmux-bulk-split | - | - | 35.1 | 0.563 | 0.0382 | 92.5 | 0.298 | 0.193 | 11 | 11.5M | 3.08M | 11 | 0 | 85.3k | 0 | 9.32e+03 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=zrle / wm=marco-comp / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tmux-type | 26.1 | 50.5 | - | - | - | 94.8 | 0.0159 | 0.0212 | 60 | 1.98M | 3.62e+03 | 60 | 0 | 17.9k | 38.5k | 728 | 9 | - |
| nvim-scroll | - | - | - | 0.183 | 0.0335 | 91.5 | 0.0558 | 0.065 | 6 | 11.3M | 339k | 6 | 0 | 42.7k | 0 | 1.12e+03 | 0 | - |
| unicode | - | - | 11.5 | 4.47 | 0.0899 | 90.7 | 3.85 | 1.34 | 36 | 70.4M | 9.26M | 36 | 0 | 9.11M | 96 | 137k | 3 | - |
| box-drawing | - | - | 34.9 | 1.39 | 0.0857 | 91.5 | 1.23 | 0.0992 | 14 | 27.4M | 90.5k | 14 | 0 | 1.76M | 0 | 64 | 0 | - |
| fullscreen-redraw | - | - | 0.883 | 5 | 0.0115 | 92.3 | 0.303 | 1.66 | 156 | 305M | 1.35M | 156 | 0 | 1.48M | 64 | 12k | 2 | 300 |
| shell-echo | 26.1 | 50.5 | - | - | - | 94.2 | 0.0156 | 0.0198 | 60 | 2.4M | 3.23e+03 | 60 | 0 | 22.1k | 38.5k | 124 | 9 | - |
| bulk-ascii | - | - | 14.5 | 3.53 | 0.0745 | 90.9 | 2.69 | 1.4 | 29 | 56.7M | 12.3M | 29 | 0 | 301k | 0 | 12k | 0 | - |
| compile-log | - | - | 18.1 | 1 | 0.0567 | 93.9 | 0.8 | 0.296 | 10 | 19.5M | 2.01M | 10 | 0 | 96k | 0 | 11.7k | 0 | - |
| sgr-color | - | - | 21.3 | 2.36 | 0.105 | 91.8 | 1.9 | 1.11 | 20 | 39.1M | 14.6M | 20 | 0 | 2.1M | 32 | 51.8k | 1 | - |
| nvim-type | 27.4 | 53.6 | - | - | - | 94.3 | 0.0411 | 0.159 | 60 | 110M | 5.64e+03 | 60 | 0 | 35.2k | 38.5k | 136 | 9 | - |
| tmux-bulk-split | - | - | 32.4 | 0.577 | 0.0711 | 94.3 | 0.296 | 0.361 | 12 | 12.5M | 3.1M | 12 | 0 | 90.6k | 0 | 9.48e+03 | 0 | - |

### display_kind=xvnc / vnc_encoding=zrle / wm=marco-comp / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| shell-echo | 25.6 | 50 | - | - | - | 61.3 | 0.0159 | 0.02 | 60 | 2.4M | 3.23e+03 | 60 | 0 | - |
| nvim-scroll | - | - | - | 0.183 | 0.0353 | 60.7 | 0.0595 | 0.0663 | 6 | 11.3M | 334k | 6 | 0 | - |
| nvim-type | 26.7 | 53 | - | - | - | 60.6 | 0.0405 | 0.16 | 60 | 110M | 5.64e+03 | 60 | 0 | - |
| unicode | - | - | 11.5 | 4.47 | 0.0685 | 61 | 3.83 | 1.34 | 36 | 70.4M | 9.29M | 36 | 0 | - |
| tmux-bulk-split | - | - | 34.2 | 0.561 | 0.066 | 61.8 | 0.299 | 0.356 | 11 | 11.5M | 2.91M | 11 | 0 | - |
| sgr-color | - | - | 21.2 | 2.36 | 0.104 | 61.6 | 1.89 | 1.1 | 20 | 39.1M | 14.6M | 20 | 0 | - |
| fullscreen-redraw | - | - | 0.883 | 5 | 0.0131 | 62 | 0.303 | 1.67 | 156 | 305M | 1.33M | 156 | 0 | 300 |
| tmux-type | 25.6 | 50 | - | - | - | 60.8 | 0.016 | 0.0214 | 60 | 1.98M | 3.58e+03 | 60 | 0 | - |
| compile-log | - | - | 18.1 | 1 | 0.0599 | 59.3 | 0.797 | 0.294 | 10 | 19.5M | 2.02M | 10 | 0 | - |
| bulk-ascii | - | - | 14.6 | 3.52 | 0.0747 | 59.9 | 2.68 | 1.4 | 29 | 56.7M | 12.3M | 29 | 0 | - |
| box-drawing | - | - | 35 | 1.42 | 0.0874 | 61 | 1.26 | 0.1 | 14 | 27.4M | 91.8k | 14 | 0 | - |

### display_kind=xvnc / vnc_encoding=zrle / wm=mutter / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| compile-log | - | - | 18.1 | 1 | 0.054 | 284 | 0.802 | 0.314 | 10 | 20M | 2.03M | 10 | 0 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 298 | 0.31 | 1.99 | 155 | 310M | 1.3M | 155 | 0 | 300 |
| box-drawing | - | - | 34.8 | 1.46 | 0.0544 | 293 | 1.29 | 0.129 | 14 | 28M | 91.1k | 14 | 0 | - |
| shell-echo | 25.7 | 35.4 | - | - | - | 302 | 0.0182 | 0.0651 | 60 | 2.42M | 3.21e+03 | 60 | 0 | - |
| tmux-bulk-split | - | - | 33.3 | 0.584 | 0.0441 | 287 | 0.303 | 0.375 | 12 | 12.6M | 3.16M | 12 | 0 | - |
| sgr-color | - | - | 20.6 | 2.48 | 0.0695 | 303 | 2 | 1.2 | 21 | 42.1M | 15.2M | 21 | 0 | - |
| unicode | - | - | 11.4 | 4.47 | 0.102 | 293 | 3.83 | 1.4 | 36 | 72.1M | 9.31M | 36 | 0 | - |
| bulk-ascii | - | - | 14.5 | 3.53 | 0.0909 | 309 | 2.69 | 1.46 | 29 | 58.1M | 12.3M | 29 | 0 | - |
| nvim-scroll | - | - | - | 0.193 | 0.0234 | 307 | 0.0572 | 0.0773 | 6 | 11.4M | 339k | 6 | 0 | - |
| nvim-type | 26.9 | 40 | - | - | - | 292 | 0.0517 | 0.174 | 60 | 111M | 5.86e+03 | 60 | 0 | - |
| tmux-type | 25.6 | 35.2 | - | - | - | 224 | 0.018 | 0.0625 | 60 | 2M | 3.66e+03 | 60 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=zrle / wm=none / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 86.3 | 0.364 | 2.57 | 155 | 389M | 2.66M | 155 | 0 | 3.21M | 5.14e+03 | 12k | 159 | 300 |
| box-drawing | - | - | 34.7 | 1.45 | 0.0714 | 87.3 | 1.27 | 0.106 | 14 | 35.1M | 99.2k | 14 | 0 | 2.11M | 568 | 64 | 16 | - |
| compile-log | - | - | 18.1 | 1 | 0.0549 | 87.6 | 0.802 | 0.313 | 10 | 25.1M | 2.15M | 10 | 0 | 108k | 440 | 11.7k | 12 | - |
| unicode | - | - | 11.5 | 4.48 | 0.0823 | 87.2 | 3.88 | 1.4 | 36 | 90.3M | 9.91M | 36 | 0 | 10.5M | 1.27e+03 | 138k | 38 | - |
| shell-echo | 27 | 35.8 | - | - | - | 86.7 | 0.0189 | 0.0485 | 60 | 2.68M | 3.1e+03 | 60 | 0 | 24.9k | 44.3k | 124 | 129 | - |
| tmux-type | 27 | 35.8 | - | - | - | 86.9 | 0.0199 | 0.0493 | 60 | 2.53M | 6.17e+03 | 60 | 0 | 20.7k | 44.3k | 728 | 129 | - |
| nvim-scroll | - | - | - | 0.182 | 0.0372 | 89.5 | 0.0601 | 0.0654 | 6 | 14.6M | 336k | 6 | 0 | 48.4k | 312 | 1.12e+03 | 8 | - |
| sgr-color | - | - | 21.1 | 2.38 | 0.108 | 89.4 | 1.91 | 1.17 | 20 | 50.2M | 15.7M | 20 | 0 | 2.42M | 760 | 51.8k | 22 | - |
| tmux-bulk-split | - | - | 34.8 | 0.554 | 0.0375 | 86.6 | 0.293 | 0.381 | 11 | 14.9M | 3.31M | 11 | 0 | 99.6k | 472 | 9.37e+03 | 13 | - |
| bulk-ascii | - | - | 14.6 | 3.54 | 0.0557 | 86.7 | 2.69 | 1.46 | 29 | 72.8M | 13M | 29 | 0 | 338k | 1.05e+03 | 12k | 31 | - |
| nvim-type | 28.1 | 37.6 | - | - | - | 87.4 | 0.0461 | 0.127 | 60 | 143M | 3.27e+03 | 60 | 0 | 38k | 44.3k | 136 | 129 | - |

### display_kind=xvnc / vnc_encoding=zrle / wm=none / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| box-drawing | - | - | 34.8 | 1.46 | 0.0518 | 56.5 | 1.29 | 0.104 | 14 | 35.1M | 98.2k | 14 | 0 | - |
| compile-log | - | - | 18.2 | 0.998 | 0.0569 | 59.6 | 0.802 | 0.31 | 10 | 25.1M | 2.16M | 10 | 0 | - |
| tmux-type | 25.6 | 34.6 | - | - | - | 59.2 | 0.0194 | 0.0508 | 60 | 2.53M | 6.17e+03 | 60 | 0 | - |
| bulk-ascii | - | - | 14.5 | 3.55 | 0.0728 | 59.6 | 2.7 | 1.47 | 29 | 72.8M | 13.1M | 29 | 0 | - |
| nvim-type | 27 | 36.5 | - | - | - | 58.9 | 0.0457 | 0.128 | 60 | 143M | 3.27e+03 | 60 | 0 | - |
| sgr-color | - | - | 21.3 | 2.36 | 0.11 | 59.6 | 1.9 | 1.17 | 20 | 50.2M | 15.5M | 20 | 0 | - |
| shell-echo | 25.6 | 34.6 | - | - | - | 56.6 | 0.0187 | 0.0507 | 60 | 2.68M | 3.1e+03 | 60 | 0 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 58.8 | 0.375 | 2.58 | 155 | 389M | 2.67M | 155 | 0 | 300 |
| unicode | - | - | 11.5 | 4.48 | 0.0752 | 59.9 | 3.86 | 1.39 | 36 | 90.3M | 9.91M | 36 | 0 | - |
| tmux-bulk-split | - | - | 34.5 | 0.557 | 0.0529 | 60 | 0.293 | 0.381 | 11 | 14.9M | 3.31M | 11 | 0 | - |
| nvim-scroll | - | - | - | 0.183 | 0.0355 | 59.8 | 0.0598 | 0.0674 | 6 | 14.6M | 367k | 6 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tmux-type | 26.2 | 35.7 | - | - | - | 263 | 0.0178 | 0.0617 | 60 | 2M | 4.42e+03 | 60 | 0 | 17.8k | 42.4k | 636 | 9 | - |
| nvim-scroll | - | - | - | 0.194 | 0.0225 | 272 | 0.0566 | 0.0576 | 6 | 11.4M | 380k | 6 | 0 | 42.7k | 384 | 1.28e+03 | 0 | - |
| sgr-color | - | - | 21.1 | 2.36 | 0.124 | 272 | 1.91 | 0.61 | 20 | 40.1M | 16.1M | 20 | 0 | 2.1M | 1.28e+03 | 51.8k | 0 | - |
| unicode | - | - | 11.4 | 4.48 | 0.0951 | 268 | 3.86 | 0.87 | 36 | 72.1M | 8.17M | 36 | 0 | 9.14M | 2.3e+03 | 136k | 0 | - |
| tmux-bulk-split | - | - | 33.6 | 0.586 | 0.0358 | 266 | 0.301 | 0.219 | 12 | 12.6M | 2.77M | 12 | 0 | 91.6k | 768 | 9.08e+03 | 0 | - |
| bulk-ascii | - | - | 14.6 | 3.53 | 0.0661 | 264 | 2.7 | 0.85 | 29 | 58.1M | 10M | 29 | 0 | 300k | 1.86e+03 | 12k | 0 | - |
| box-drawing | - | - | 35.4 | 1.4 | 0.0787 | 267 | 1.25 | 0.107 | 13 | 26M | 136k | 13 | 0 | 1.69M | 832 | 64 | 0 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 268 | 0.308 | 1.71 | 155 | 310M | 2.26M | 155 | 0 | 1.47M | 9.98e+03 | 12k | 2 | 300 |
| shell-echo | 26.1 | 35.8 | - | - | - | 260 | 0.0172 | 0.0629 | 60 | 2.42M | 3.42e+03 | 60 | 0 | 22.1k | 42.4k | 124 | 9 | - |
| compile-log | - | - | 18.4 | 1 | 0.0487 | 267 | 0.804 | 0.19 | 10 | 20M | 2.12M | 10 | 0 | 95.8k | 640 | 11.7k | 0 | - |
| nvim-type | 27.4 | 40.5 | - | - | - | 265 | 0.0414 | 0.174 | 60 | 111M | 5.99e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=none / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | 0.184 | 0.0345 | 60.6 | 0.0599 | 0.0473 | 6 | 14.6M | 413k | 6 | 0 | - |
| nvim-type | 27 | 36.5 | - | - | - | 60.4 | 0.046 | 0.127 | 60 | 143M | 3.57e+03 | 60 | 0 | - |
| sgr-color | - | - | 21.3 | 2.36 | 0.105 | 59.1 | 1.91 | 0.592 | 20 | 50.2M | 17.2M | 20 | 0 | - |
| compile-log | - | - | 18.3 | 0.999 | 0.0517 | 59.9 | 0.8 | 0.181 | 10 | 25.1M | 2.27M | 10 | 0 | - |
| shell-echo | 25.6 | 34.5 | - | - | - | 60.1 | 0.0194 | 0.0503 | 60 | 2.68M | 3.31e+03 | 60 | 0 | - |
| tmux-bulk-split | - | - | 35.2 | 0.554 | 0.0426 | 58.9 | 0.302 | 0.224 | 11 | 14.9M | 2.91M | 11 | 0 | - |
| tmux-type | 25.7 | 34.4 | - | - | - | 59.6 | 0.0192 | 0.0508 | 60 | 2.53M | 6.4e+03 | 60 | 0 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 59.5 | 0.37 | 2.15 | 155 | 389M | 3M | 155 | 0 | 300 |
| unicode | - | - | 11.6 | 4.47 | 0.0678 | 56 | 3.85 | 0.818 | 36 | 90.3M | 8.67M | 36 | 0 | - |
| bulk-ascii | - | - | 14.6 | 3.53 | 0.0572 | 59.1 | 2.69 | 0.812 | 29 | 72.8M | 10.6M | 29 | 0 | - |
| box-drawing | - | - | 34.7 | 1.45 | 0.0915 | 58.9 | 1.28 | 0.0861 | 14 | 35.1M | 152k | 14 | 0 | - |

### display_kind=xvnc+x11remote / vnc_encoding=zrle / wm=marco-nocomp / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| compile-log | - | - | 18.2 | 1 | 0.0525 | 91.3 | 0.808 | 0.289 | 10 | 19.5M | 2.04M | 10 | 0 | 96.5k | 0 | 11.7k | 0 | - |
| unicode | - | - | 11.5 | 4.47 | 0.101 | 92.3 | 3.85 | 1.33 | 36 | 70.4M | 9.36M | 36 | 0 | 9.15M | 96 | 137k | 3 | - |
| nvim-type | 27.3 | 36.7 | - | - | - | 93.1 | 0.0391 | 0.111 | 60 | 110M | 8.34e+03 | 60 | 0 | 35.2k | 38.5k | 136 | 9 | - |
| box-drawing | - | - | 35.6 | 1.39 | 0.0913 | 91.6 | 1.25 | 0.0932 | 13 | 25.4M | 91.6k | 13 | 0 | 1.74M | 0 | 64 | 0 | - |
| nvim-scroll | - | - | - | 0.186 | 0.0298 | 92.1 | 0.058 | 0.0564 | 6 | 11.3M | 287k | 6 | 0 | 42.7k | 0 | 1.12e+03 | 0 | - |
| bulk-ascii | - | - | 14.6 | 3.53 | 0.0695 | 91.6 | 2.69 | 1.4 | 29 | 56.7M | 12.4M | 29 | 0 | 303k | 0 | 12k | 0 | - |
| tmux-type | 26.2 | 35 | - | - | - | 92.9 | 0.0168 | 0.0492 | 60 | 1.98M | 3.8e+03 | 60 | 0 | 17.8k | 38.5k | 636 | 9 | - |
| fullscreen-redraw | - | - | 0.883 | 5 | 0.0155 | 91.2 | 0.292 | 1.54 | 156 | 305M | 1.54M | 156 | 0 | 1.48M | 64 | 12k | 2 | 300 |
| tmux-bulk-split | - | - | 35.3 | 0.55 | 0.0337 | 93.2 | 0.297 | 0.335 | 11 | 11.5M | 2.93M | 11 | 0 | 85.6k | 0 | 9.48e+03 | 0 | - |
| sgr-color | - | - | 21.1 | 2.36 | 0.116 | 91.3 | 1.9 | 1.1 | 20 | 39.1M | 14.7M | 20 | 0 | 2.11M | 32 | 51.8k | 1 | - |
| shell-echo | 26.2 | 35 | - | - | - | 93.2 | 0.0165 | 0.0502 | 60 | 2.4M | 3.23e+03 | 60 | 0 | 22.1k | 38.5k | 124 | 9 | - |

### display_kind=xvnc / vnc_encoding=tight / wm=mutter / size=large / font=dejavu

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sgr-color | - | - | 21.2 | 2.36 | 0.106 | 220 | 1.9 | 0.604 | 20 | 40.1M | 15.4M | 20 | 0 | - |
| compile-log | - | - | 18.3 | 0.999 | 0.0489 | 208 | 0.798 | 0.19 | 10 | 20M | 2.11M | 10 | 0 | - |
| tmux-type | 25.7 | 35.1 | - | - | - | 212 | 0.0183 | 0.0595 | 60 | 2M | 4.16e+03 | 60 | 0 | - |
| fullscreen-redraw | - | - | 0.885 | 5 | 0 | 215 | 0.313 | 1.78 | 155 | 310M | 2.48M | 155 | 0 | 300 |
| tmux-bulk-split | - | - | 34 | 0.584 | 0.0336 | 207 | 0.289 | 0.208 | 12 | 12.7M | 2.53M | 12 | 0 | - |
| box-drawing | - | - | 35.4 | 1.39 | 0.0842 | 223 | 1.23 | 0.113 | 13 | 26M | 146k | 13 | 0 | - |
| unicode | - | - | 11.5 | 4.47 | 0.0758 | 219 | 3.79 | 0.871 | 36 | 72.1M | 8.37M | 36 | 0 | - |
| nvim-type | 26.8 | 39.9 | - | - | - | 212 | 0.0405 | 0.176 | 60 | 110M | 5.99e+03 | 60 | 0 | - |
| shell-echo | 25.6 | 35.2 | - | - | - | 149 | 0.0177 | 0.06 | 60 | 2.41M | 3.84e+03 | 60 | 0 | - |
| nvim-scroll | - | - | - | 0.193 | 0.0208 | 217 | 0.0549 | 0.0481 | 6 | 11.4M | 378k | 6 | 0 | - |
| bulk-ascii | - | - | 14.5 | 3.53 | 0.0838 | 210 | 2.7 | 0.816 | 29 | 58.1M | 9.37M | 29 | 0 | - |

## rtt-sweep preset (xvnc+x11remote, Tight, mutter)


### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=20 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | 0.178 | 0.391 | 1.83e+03 | 0.000292 | 0.0976 | 4 | 8.01M | 1M | 5 | 0 | 22.4k | 1.05e+03 | 7.63e+03 | 20 |
| shell-echo | 46.1 | 55.6 | - | - | - | 1.83e+03 | 0.0197 | 0.14 | 60 | 6.34M | 873k | 61 | 0 | 22.6k | 43.2k | 316 | 29 |
| bulk-ascii | - | - | 12.9 | 4.01 | 0.101 | 1.82e+03 | 2.7 | 0.931 | 31 | 62.1M | 11M | 32 | 0 | 308k | 2.82e+03 | 12k | 21 |
| nvim-type | 47.3 | 60.4 | - | - | - | 1.83e+03 | 0.0515 | 0.253 | 61 | 114M | 884k | 62 | 0 | 42.6k | 43.2k | 2.73e+03 | 29 |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=0.25 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-scroll | - | - | - | 0.193 | 0.0244 | 267 | 0.0565 | 0.059 | 6 | 11.4M | 380k | 6 | 0 | 42.7k | 384 | 1.28e+03 | 0 |
| bulk-ascii | - | - | 14.6 | 3.53 | 0.0683 | 292 | 2.69 | 0.843 | 29 | 58.1M | 10M | 29 | 0 | 297k | 1.86e+03 | 12k | 0 |
| shell-echo | 26.1 | 35.9 | - | - | - | 269 | 0.0172 | 0.0631 | 60 | 2.42M | 3.43e+03 | 60 | 0 | 22.1k | 42.4k | 124 | 9 |
| nvim-type | 27.4 | 40.4 | - | - | - | 285 | 0.0412 | 0.171 | 60 | 111M | 5.99e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=2 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bulk-ascii | - | - | 14.6 | 3.53 | 0.0711 | 429 | 2.69 | 0.859 | 29 | 58.1M | 10.1M | 29 | 0 | 301k | 1.86e+03 | 12k | 0 |
| nvim-type | 29.1 | 42.2 | - | - | - | 435 | 0.0412 | 0.174 | 60 | 111M | 5.99e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 |
| shell-echo | 27.9 | 37.6 | - | - | - | 436 | 0.0176 | 0.0635 | 60 | 2.42M | 3.43e+03 | 60 | 0 | 22.1k | 42.4k | 124 | 9 |
| nvim-scroll | - | - | - | 0.193 | 0.0252 | 425 | 0.057 | 0.057 | 6 | 11.4M | 349k | 6 | 0 | 42.6k | 384 | 1.28e+03 | 0 |

### display_kind=xvnc+x11remote / vnc_encoding=tight / wm=mutter / rtt_ms=0 / size=large / font=caskaydia

| workload | latency_ms | e2e_latency_ms | throughput_mb_s | elapsed_s | drain_s | startup_ms | term_cpu_s | xserver_cpu_s | damage_events | damage_area_px | vnc_bytes | vnc_updates | vnc_copyrect_area | x11_c2s_bytes | x11_s2c_bytes | x11_image_bytes | x11_replies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvim-type | 27.1 | 40.1 | - | - | - | 254 | 0.0421 | 0.172 | 60 | 111M | 5.99e+03 | 60 | 0 | 35.2k | 42.4k | 136 | 9 |
| shell-echo | 25.8 | 35.4 | - | - | - | 262 | 0.0179 | 0.0637 | 60 | 2.42M | 3.43e+03 | 60 | 0 | 22.1k | 42.4k | 124 | 9 |
| nvim-scroll | - | - | - | 0.196 | 0.0192 | 253 | 0.0559 | 0.0578 | 6 | 11.4M | 383k | 6 | 0 | 42.6k | 384 | 1.12e+03 | 0 |
| bulk-ascii | - | - | 14.6 | 3.53 | 0.0619 | 251 | 2.7 | 0.832 | 29 | 58.1M | 9.94M | 29 | 0 | 298k | 1.86e+03 | 12k | 0 |
