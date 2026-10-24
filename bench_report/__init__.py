# -*- coding: utf-8 -*-
"""
SAFE-CARE Bench - evaluation report generator.

Turns a published run directory into a Markdown report with seven fixed sections:
summary, scores by tier, differences between adjacent tiers, missed escalations,
calibration status, what was run, and the limitations that apply.

Usage
-----
    python -m bench_report results/run_2026-09-01 --out report.md
    python -m bench_report results/run_2026-09-01 --out report.md --final \\
        --deny-list /path/outside/repo/deny.txt --ip-scan "ip-scan"

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
* Without `--final` the report carries a DRAFT banner. `--final` fails closed: it
  refuses to write unless the deny-list check and ip-scan both pass, and both must
  be configured.
"""

__version__ = "0.2.0"
