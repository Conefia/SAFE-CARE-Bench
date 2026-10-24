# -*- coding: utf-8 -*-
"""The private check a report must pass before `--final` writes it.

Two inputs, both kept outside this repository:

* The deny list. One entry per line, `#` starts a comment. A plain entry matches
  case-insensitively as a substring; an entry starting `re:` is a Python regular
  expression. Hits name the report line and the deny-list line, never the matched
  text, so the check's own output is safe to paste.
* The ip-check verdict, written by `/ip-check report <draft>` in the engine repo.
  One `key: value` per line, exactly the keys in VERDICT_KEYS. It is bound to the
  draft by sha256, so it proves which bytes were checked.
"""

import hashlib, os, re

from .run import BENCH_ROOT


class CheckError(Exception):
    """The check could not run, so the report must not be finalised."""


def _outside_repo(path, what):
    real, root = os.path.realpath(path), os.path.realpath(BENCH_ROOT)
    try:
        inside = os.path.commonpath([real, root]) == root
    except ValueError:      # different drives on Windows
        inside = False
    if inside:
        raise CheckError("the %s must live outside the public bench repository" % what)
    if not os.path.isfile(real):
        raise CheckError("%s not found: %s" % (what, path))
    return real


# ---------------------------------------------------------------------------
# Deny list
# ---------------------------------------------------------------------------
def load_deny_list(path):
    if not path:
        raise CheckError("--final needs a deny list (--deny-list or SAFE_CARE_DENY_LIST)")
    real = _outside_repo(path, "deny list")
    entries = []
    with open(real, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("re:"):
                pattern = re.compile(line[3:])
            else:
                pattern = re.compile(re.escape(line), re.I)
            entries.append((lineno, pattern))
    if not entries:
        raise CheckError("deny list is empty: %s" % path)
    return entries


def deny_hits(text, entries):
    """[(report line, deny-list line)] for every match."""
    hits = []
    for report_line, line in enumerate(text.splitlines(), 1):
        for deny_line, pattern in entries:
            if pattern.search(line):
                hits.append((report_line, deny_line))
    return hits


# ---------------------------------------------------------------------------
# ip-check verdict
# ---------------------------------------------------------------------------
CHECKED_ITEMS = ("item_1", "item_2", "item_4", "item_5", "item_7")
NOT_APPLICABLE_ITEMS = ("item_3", "item_6")
VERDICT_KEYS = (("ip_check_verdict", "report_sha256", "report_file", "checked_by", "checked_utc",
                 "ip_check_commit") + CHECKED_ITEMS + NOT_APPLICABLE_ITEMS + ("bottom_line",))

_SHAPES = {
    "ip_check_verdict": re.compile(r"1"),
    "report_sha256":    re.compile(r"[0-9a-f]{64}"),
    "report_file":      re.compile(r"[^/\\]+"),
    "checked_by":       re.compile(r"\S.*"),
    "checked_utc":      re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"),
    "ip_check_commit":  re.compile(r"[0-9a-f]{40}"),
    "bottom_line":      re.compile(r"SAFE TO PUSH|DO NOT PUSH"),
}
_ITEM = re.compile(r"PASS|FAIL|NEEDS HUMAN|PASS \(cleared by \S.* \d{4}-\d{2}-\d{2}\)")


def read_verdict(path):
    """Parse a verdict file. Any line, key or value out of shape is an error."""
    if not path:
        raise CheckError("--final needs an ip-check verdict (--verdict)")
    real = _outside_repo(path, "ip-check verdict")
    with open(real, encoding="utf-8") as f:
        lines = f.read().splitlines()
    verdict = {}
    for lineno, line in enumerate(lines, 1):
        m = re.match(r"^([a-z_0-9]+): (.*)$", line)
        if not m or m.group(1) not in VERDICT_KEYS or m.group(1) in verdict:
            raise CheckError("verdict line %d is not one of the expected `key: value` lines" % lineno)
        verdict[m.group(1)] = m.group(2).strip()
    missing = [k for k in VERDICT_KEYS if k not in verdict]
    if missing:
        raise CheckError("verdict is missing: %s" % ", ".join(missing))
    for key, shape in _SHAPES.items():
        if not shape.fullmatch(verdict[key]):
            raise CheckError("verdict field %s is not in the expected form" % key)
    for key in CHECKED_ITEMS:
        if not _ITEM.fullmatch(verdict[key]):
            raise CheckError("verdict field %s must be PASS, FAIL or NEEDS HUMAN" % key)
    for key in NOT_APPLICABLE_ITEMS:
        if verdict[key] != "N/A":
            raise CheckError("verdict field %s must be N/A for a report" % key)
    return verdict


def verdict_problems(verdict, draft_bytes, draft_name):
    """Every reason this verdict does not clear this draft. Empty means it does."""
    problems = []
    if hashlib.sha256(draft_bytes).hexdigest() != verdict["report_sha256"]:
        problems.append("the draft's sha256 does not match the verdict: the draft changed after it was checked")
    if verdict["report_file"] != draft_name:
        problems.append("the verdict is for %s, not %s" % (verdict["report_file"], draft_name))
    for key in CHECKED_ITEMS:
        if not verdict[key].startswith("PASS"):
            problems.append("%s is %s" % (key, verdict[key]))
    if verdict["bottom_line"] != "SAFE TO PUSH":
        problems.append("bottom line is %s" % verdict["bottom_line"])
    return problems
