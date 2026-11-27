"""xtrp command line: python3 -m xtrp <command> ..."""

import argparse
import sys


def _cmd_workload(args):
    from xtrp import workloads
    workloads.run_payload(args.name, args.status, n_bytes=args.bytes, lines=args.lines, seconds=args.seconds,
                          cols=args.cols, rows=args.rows, steps=args.steps, exit_after=args.exit)
    return 0


def _cmd_run(args):
    from xtrp import runner
    try:
        n = runner.run_preset(args.preset, args.build, args.out, iterations=args.iterations,
                              builds_path=args.builds)
    except KeyboardInterrupt:
        sys.stderr.write("interrupted; everything started has been stopped\n")
        return 130
    sys.stderr.write("wrote %d records to %s\n" % (n, args.out))
    return 0


def _cmd_report(args):
    from xtrp import report
    from xtrp.model import load_records
    base, cand = load_records(args.base), load_records(args.cand)
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
    p.add_argument("--exit", action="store_true", help="return after the end event (tests)")
    p.set_defaults(func=_cmd_workload)

    from xtrp.runner import PRESETS
    p = sub.add_parser("run", help="run a preset matrix and write schema-1 records")
    p.add_argument("--preset", required=True, choices=list(PRESETS))
    p.add_argument("--build", action="append", required=True, help="build name from builds.json (repeatable)")
    p.add_argument("--out", required=True, help="output directory, e.g. results/raw/<stamp>")
    p.add_argument("--iterations", type=int, help="override every block's iteration count")
    p.add_argument("--builds", help="alternative builds.json")
    p.set_defaults(func=_cmd_run)

    p = sub.add_parser("report", help="compare two record directories")
    p.add_argument("base")
    p.add_argument("cand")
    p.add_argument("--threshold", type=float, default=5.0, help="regression threshold in percent")
    p.add_argument("--out", help="write markdown here instead of stdout")
    p.add_argument("--cross-platform", action="store_true",
                   help="compare records from different platforms (informational, never flags)")
    p.set_defaults(func=_cmd_report)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
