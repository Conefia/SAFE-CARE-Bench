# -*- coding: utf-8 -*-
"""
SAFE-CARE Bench - evaluation report generator.

Turns a published run directory into a Markdown report with seven fixed sections:
summary, scores by tier, differences between adjacent tiers, missed escalations,
calibration status, what was run, and the limitations that apply.

Usage
-----
    python -m bench_report results/run_2026-09-01 --out report.draft.md
    # then, in the engine repo: /ip-check report report.draft.md  ->  report.draft.md.verdict
    python -m bench_report results/run_2026-09-01 --final --draft report.draft.md \\
        --verdict /outside/repo/report.draft.md.verdict --deny-list /outside/repo/deny.txt --out report.md

Design notes
------------
* A formatter, not a runner. It reads only the published run format (`RUN_CARD.md`,
  `manifests/`, `scores/`) plus this repository's scenarios, tier configs and
  ROADMAP. No engine code, no model calls.
* `run.py` is the only module that knows the run format. Fields reach a report
  through an allow-list; anything else in a run directory (knowledge base ids,
  judge rationales, engine paths) is never read into it.
* Output is deterministic: the same run directory gives a byte-identical report.
  Nothing time-dependent is written.
* A draft and its final report are the same bytes; only the `*.draft.md` name
  marks a draft. `--final` fails closed: it publishes the draft unchanged only if
  the draft is what the run renders now, the ip-check verdict's sha256 matches it
  with every item PASS and no NEEDS HUMAN, and the deny list and the shape checks
  (`shapes.py`) pass. A draft run prints the same findings as warnings. The verdict
  and the deny list must both be configured and live outside this repository.
"""

__version__ = "0.4.0"
