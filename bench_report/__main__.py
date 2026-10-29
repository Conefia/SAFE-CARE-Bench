# -*- coding: utf-8 -*-
"""Command line.

    python -m bench_report <run_dir> --out report.draft.md
    python -m bench_report <run_dir> --final --draft report.draft.md --verdict <verdict> --out report.md
"""

import argparse, os, sys

from .check import CheckError, deny_hits, load_deny_list, read_verdict, verdict_problems
from .report import render
from .run import BENCH_ROOT, RunFormatError, load
from .shapes import field_problems, text_hits

DRAFT_SUFFIX = ".draft.md"


def write_bytes(path, data):
    # staged beside the target and moved into place, so a failed write leaves nothing
    staged = path + ".partial"
    with open(staged, "wb") as f:
        f.write(data)
    os.replace(staged, path)


def refuse(message):
    print("refused: %s" % message, file=sys.stderr)
    return 2


def shape_findings(run, text):
    """Shape-check findings as printable lines; they name places and rules, never values."""
    return (["field %s: %s" % p for p in field_problems(run)]
            + ["report line %d: %s" % h for h in text_hits(text)])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m bench_report", description="Turn a run directory into a report.")
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True,
                    help="report path; without --final it must end in %s" % DRAFT_SUFFIX)
    ap.add_argument("--final", action="store_true",
                    help="publish --draft as --out, only if the draft matches this run, the ip-check "
                         "verdict clears it and the deny list passes")
    ap.add_argument("--draft", help="with --final: the checked draft")
    ap.add_argument("--verdict", help="with --final: the ip-check verdict for the draft, kept outside this repository")
    ap.add_argument("--deny-list", default=os.environ.get("SAFE_CARE_DENY_LIST"),
                    help="deny list kept outside this repository (default: $SAFE_CARE_DENY_LIST)")
    ap.add_argument("--judge", help="judge model to report when the scores hold more than one")
    ap.add_argument("--all-scenarios", action="store_true",
                    help="include scenarios the run marks out of scope for its tiers (left out by default)")
    ap.add_argument("--bench-root", default=BENCH_ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    try:
        run = load(args.run_dir, args.judge, args.bench_root, args.all_scenarios)
        data = render(run).encode("utf-8")
    except RunFormatError as e:
        print("bench_report: %s" % e, file=sys.stderr)
        return 1

    if not args.final:
        if not args.out.endswith(DRAFT_SUFFIX):
            print("bench_report: a draft's --out must end in %s; --final writes the published name" % DRAFT_SUFFIX,
                  file=sys.stderr)
            return 1
        write_bytes(args.out, data)
        print("draft written: %s" % args.out)
        for finding in shape_findings(run, data.decode("utf-8")):
            print("warning: shape check, %s" % finding)
        if args.deny_list:
            try:
                hits = deny_hits(data.decode("utf-8"), load_deny_list(args.deny_list))
            except CheckError as e:
                print("deny list not run: %s" % e)
            else:
                for report_line, deny_line in hits:
                    print("warning: report line %d matches deny-list entry on line %d" % (report_line, deny_line))
        print("next: /ip-check report %s, then --final with its verdict" % args.out)
        return 0

    try:
        if not args.draft:
            raise CheckError("--final needs the checked draft (--draft)")
        if args.out.endswith(DRAFT_SUFFIX) or os.path.abspath(args.out) == os.path.abspath(args.draft):
            raise CheckError("--out must be the published name, not a draft")
        entries = load_deny_list(args.deny_list)
        verdict = read_verdict(args.verdict)
        with open(args.draft, "rb") as f:
            draft = f.read()
    except (CheckError, OSError) as e:
        return refuse(e)

    if draft != data:
        return refuse("the draft is not what this run renders now; generate a new draft and check it again")
    problems = verdict_problems(verdict, draft, os.path.basename(args.draft))
    if problems:
        return refuse("the ip-check verdict does not clear this draft:\n  " + "\n  ".join(problems))
    text = draft.decode("utf-8")
    findings = ["report line %d matches deny-list entry on line %d" % h for h in deny_hits(text, entries)]
    findings += ["shape check, %s" % f for f in shape_findings(run, text)]
    if findings:
        for finding in findings:
            print("refused: %s" % finding, file=sys.stderr)
        return 2

    write_bytes(args.out, draft)
    print("final report written: %s (sha256 %s, checked by %s on %s)"
          % (args.out, verdict["report_sha256"], verdict["checked_by"], verdict["checked_utc"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
