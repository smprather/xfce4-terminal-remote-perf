"""xtrp command line: python3 -m xtrp <command> ..."""

import argparse
import os
import sys
import time


def _cmd_workload(args):
    from xtrp import workloads
    workloads.run_payload(args.name, args.status, n_bytes=args.bytes, lines=args.lines, seconds=args.seconds,
                          cols=args.cols, rows=args.rows, steps=args.steps, exit_after=args.exit, go=args.go)
    return 0


def _cmd_run(args):
    from xtrp import runner
    try:
        n = runner.run_preset(args.preset, args.build, args.out, iterations=args.iterations,
                              builds_path=args.builds, wms=args.wm)
    except KeyboardInterrupt:
        sys.stderr.write("interrupted; everything started has been stopped\n")
        return 130
    sys.stderr.write("wrote %d records to %s\n" % (n, args.out))
    return 0


def _cmd_report(args):
    from xtrp import report
    from xtrp.model import load_records
    base, cand = load_records(args.base), load_records(args.cand)
    for label, build in (("base", args.base_build), ("cand", args.cand_build)):
        if build is None:
            continue
        picked = [r for r in (base if label == "base" else cand) if r["key"]["build"] == build]
        if not picked:
            sys.stderr.write("no records for build %s in %s\n" % (build, args.base if label == "base" else args.cand))
            return 2
        if label == "base":
            base = picked
        else:
            cand = picked
    try:
        rows = report.compare(base, cand, threshold_pct=args.threshold, cross_platform=args.cross_platform)
    except report.PlatformMismatch as e:
        sys.stderr.write("%s\n" % e)
        return 2
    md = report.render_markdown(rows, cross_platform=args.cross_platform,
                                preamble=[report.flag_summary("base", base) + "  ",
                                          report.flag_summary("cand", cand)])
    data = md.encode("utf-8")          # independent of the locale (Python 3.6 under LANG=C)
    if args.out:
        with open(args.out, "wb") as f:
            f.write(data)
    else:
        sys.stdout.flush()
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    return 1 if any(r["regression"] for r in rows) else 0


def _emit_json(obj):
    import json
    sys.stdout.flush()
    sys.stdout.buffer.write((json.dumps(obj, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def _cmd_diag(args):
    import json
    from xtrp import diag
    d = diag.collect()
    if args.out:
        with open(args.out, "wb") as f:
            f.write((json.dumps(d, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    else:
        _emit_json(d)
    return 0


def _countdown(seconds):
    for n in range(seconds, 0, -1):
        sys.stderr.write("  %d...\n" % n)
        sys.stderr.flush()
        time.sleep(1)


def _cmd_live(args):
    from xtrp import diag, live, xlat
    display = os.environ.get("DISPLAY", "")
    if args.what == "latency":
        other = args.window is not None or args.pick
        if other:
            sys.stderr.write("In the terminal you want to measure, run `cat` and leave it there.\n"
                             "Press Enter here%s, then click into that terminal within 5 s.\n"
                             % (" (then click the terminal to pick it)" if args.pick else ""))
        else:
            sys.stderr.write("This measures the terminal you are typing in. Press Enter, then keep your hands\n"
                             "off the keyboard for about %d s. Only 'a' and BackSpace are typed.\n"
                             % (args.samples * 0.15 + 1))
        sys.stdin.readline()
        window = args.window
        if args.pick:
            window = xlat.run_json(["pick"], display, 120.0)[0]["window"]
        if other:
            _countdown(5)
        try:
            res = live.live_latency(display, window=window, samples=args.samples)
        except xlat.NotFocusedError:
            sys.stderr.write("refused: the target window does not have keyboard focus; nothing was typed\n")
            return 2
    else:
        sys.stderr.write("Watching window %d for %d s: run your workload in it now.\n" % (args.window, args.seconds))
        res = live.live_watch(display, args.window, args.seconds)
    _emit_json(diag.scrub(res))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m xtrp")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("workload", help="in-terminal payload side of a workload")
    p.add_argument("name")
    p.add_argument("--status", required=True, help="status file (JSON lines) to append to")
    p.add_argument("--bytes", type=int)
    p.add_argument("--lines", type=int)
    p.add_argument("--seconds", type=float)
    p.add_argument("--cols", type=int, default=120)
    p.add_argument("--rows", type=int, default=40)
    p.add_argument("--steps", type=int)
    p.add_argument("--go", help="wait for this file to exist before starting (set by the runner)")
    p.add_argument("--exit", action="store_true", help="return after the end event (tests)")
    p.set_defaults(func=_cmd_workload)

    from xtrp.runner import PRESETS
    p = sub.add_parser("run", help="run a preset matrix and write schema-1 records")
    p.add_argument("--preset", required=True, choices=list(PRESETS))
    p.add_argument("--build", action="append", required=True, help="build name from builds.json (repeatable)")
    p.add_argument("--out", required=True, help="output directory, e.g. results/raw/<stamp>")
    p.add_argument("--iterations", type=int,
                   help="override every block's iteration count (rounded up to even with several builds)")
    p.add_argument("--builds", help="alternative builds.json")
    p.add_argument("--wm", action="append", help="replace the preset's window managers (repeatable)")
    p.set_defaults(func=_cmd_run)

    p = sub.add_parser("report", help="compare two record directories")
    p.add_argument("base")
    p.add_argument("cand")
    p.add_argument("--threshold", type=float, default=5.0, help="regression threshold in percent")
    p.add_argument("--out", help="write markdown here instead of stdout")
    p.add_argument("--base-build", help="only records of this build from BASE (interleaved runs)")
    p.add_argument("--cand-build", help="only records of this build from CAND (interleaved runs)")
    p.add_argument("--cross-platform", action="store_true",
                   help="compare records from different platforms (informational, never flags)")
    p.set_defaults(func=_cmd_report)

    p = sub.add_parser("diag", help="scrubbed diagnostics for the display in $DISPLAY")
    p.add_argument("--out", help="write JSON here instead of stdout")
    p.set_defaults(func=_cmd_diag)

    p = sub.add_parser("live", help="measure on a real desktop (focus-guarded)")
    live_sub = p.add_subparsers(dest="what")
    q = live_sub.add_parser("latency", help="keypress latency of a focused terminal")
    g = q.add_mutually_exclusive_group()
    g.add_argument("--window", type=lambda v: int(v, 0), help="window id (default: this terminal, $WINDOWID)")
    g.add_argument("--pick", action="store_true", help="click the terminal to measure")
    q.add_argument("--samples", type=int, default=40)
    q.set_defaults(func=_cmd_live)
    q = live_sub.add_parser("watch", help="damage and X server CPU while you drive a window")
    q.add_argument("--window", type=lambda v: int(v, 0), required=True)
    q.add_argument("--seconds", type=int, default=30)
    q.set_defaults(func=_cmd_live)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
