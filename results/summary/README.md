# Results summaries

Committed, scrubbed summaries of harness runs. Raw run records (one JSON per
run, schema 1) stay in `results/raw/`, which git ignores.

| File | What |
|---|---|
| `<date>-baseline.md` | Baselines: EL8 (primary), EL9 and the CachyOS host (informational) |
| `<date>-baseline-medians.md` | Every EL8 configuration's medians, all metrics (appendix to the above) |

How the numbers are produced:

- **Running.** `python3 -m xtrp run --preset <smoke|quick|full|rtt-sweep> --build <name> ...` writes the
  records, inside the bench container for el8 and el9 (`bench/container [--el 9] ...`), and natively on
  the host.
- **Comparing.** Builds are compared interleaved, in one invocation:
  `python3 -m xtrp report DIR DIR --base-build A --cand-build B`. Each run is reduced to its own median
  first. A row is flagged when the candidate's median over runs is worse than the baseline's by more than
  `max(5%, baseline p10-p90 run-to-run band)`. A cost that was 0 in the baseline is flagged when the
  candidate rises above the baseline's p90. More failed runs or drain timeouts in the candidate, or a
  gated metric the candidate lacks, is flagged too. Before acting on a flag, re-run that configuration
  interleaved with `--iterations 8` or more.
- **Gated metrics** are outcomes: latency, end-to-end VNC latency, throughput and total time, CPU, VNC
  and X11 bytes, X11 replies, repaint area per keystroke, and keystrokes that painted twice. Components and structure counters
  (elapsed/drain split, rect/update/damage-event counts, CopyRect area, launch time) are informational.
- **Workload metrics** cover the workload phase only: startup settles first and the counters are reset.
- **Scrubbing.** Anything from a real site passes through `xtrp.diag.scrub` before it lands here.
