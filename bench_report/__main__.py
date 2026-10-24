# -*- coding: utf-8 -*-
"""Command line: python -m bench_report <run_dir> --out report.md [--final ...]"""

import argparse, os, sys

from .check import CheckError, deny_hits, ip_scan, load_deny_list
from .report import render
from .run import BENCH_ROOT, RunFormatError, load


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m bench_report", description="Turn a run directory into a report.")
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True, help="report path (Markdown)")
    ap.add_argument("--final", action="store_true",
                    help="refuse to write unless the deny-list check and ip-scan both pass")
    ap.add_argument("--deny-list", default=os.environ.get("SAFE_CARE_DENY_LIST"),
                    help="deny list kept outside this repository (default: $SAFE_CARE_DENY_LIST)")
    ap.add_argument("--ip-scan", default=os.environ.get("SAFE_CARE_IP_SCAN"),
                    help="command that scans a file and exits 0 when clean (default: $SAFE_CARE_IP_SCAN)")
    ap.add_argument("--judge", help="judge id to report when the scores hold more than one")
    ap.add_argument("--scoring-config", help="scoring config to report when the scores hold more than one")
    ap.add_argument("--all-scenarios", action="store_true",
                    help="include scenarios the run marks out of scope for its tiers (left out by default)")
    ap.add_argument("--bench-root", default=BENCH_ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    try:
        run = load(args.run_dir, args.judge, args.scoring_config, args.bench_root, args.all_scenarios)
        text = render(run, final=args.final)
    except RunFormatError as e:
        print("bench_report: %s" % e, file=sys.stderr)
        return 1

    if not args.final:
        write(args.out, text)
        print("draft written: %s" % args.out)
        return 0

    try:
        entries = load_deny_list(args.deny_list)
        hits = deny_hits(text, entries)
        if hits:
            for report_line, deny_line in hits:
                print("refused: report line %d matches deny-list entry on line %d" % (report_line, deny_line),
                      file=sys.stderr)
            return 2
        # ip-scan reads a file, so the report is staged beside --out and only
        # moved into place once the scan passes.
        staged = args.out + ".unchecked"
        write(staged, text)
        try:
            ok, output = ip_scan(args.ip_scan, staged)
        except Exception:
            os.remove(staged)
            raise
        if not ok:
            os.remove(staged)
            print("refused: ip-scan failed\n%s" % output, file=sys.stderr)
            return 2
        os.replace(staged, args.out)
    except CheckError as e:
        print("refused: %s" % e, file=sys.stderr)
        return 2
    print("final report written: %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
