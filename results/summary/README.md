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
  `python3 -m xtrp report DIR DIR --base-build A --cand-build B`. A row is flagged when the candidate is
  worse than the baseline median by more than `max(5%, baseline p10-p90 noise band)`. Before acting on a
  flag, re-run that configuration with more iterations.
- **Gated metrics** are outcomes: latency, end-to-end VNC latency, throughput and total time, CPU, VNC
  and X11 bytes, X11 round trips, and repaint area per keystroke. Components and structure counters
  (elapsed/drain split, rect/update/damage-event counts, CopyRect area, launch time) are informational.
- **Workload metrics** cover the workload phase only: startup settles first and the counters are reset.
- **Scrubbing.** Anything from a real site passes through `xtrp.diag.scrub` before it lands here.
