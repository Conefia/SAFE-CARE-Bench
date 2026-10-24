# -*- coding: utf-8 -*-
"""The private check a report must pass before `--final` writes it.

The deny list is kept outside this repository. Format: one entry per line, `#`
starts a comment. A plain entry matches case-insensitively as a substring; an
entry starting `re:` is a Python regular expression. Hits name the report line
and the deny-list line, never the matched text, so the check's own output is
safe to paste.
"""

import os, re, subprocess

from .run import BENCH_ROOT


class CheckError(Exception):
    """The check could not run, so the report must not be finalised."""


def load_deny_list(path):
    if not path:
        raise CheckError("--final needs a deny list (--deny-list or SAFE_CARE_DENY_LIST)")
    real, root = os.path.realpath(path), os.path.realpath(BENCH_ROOT)
    try:
        inside = os.path.commonpath([real, root]) == root
    except ValueError:      # different drives on Windows
        inside = False
    if inside:
        raise CheckError("the deny list must live outside the public bench repository")
    if not os.path.isfile(real):
        raise CheckError("deny list not found: %s" % path)
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


def ip_scan(command, path):
    """Run the configured ip-scan command on `path`. Exit status 0 is a pass."""
    if not command:
        raise CheckError("--final needs an ip-scan command (--ip-scan or SAFE_CARE_IP_SCAN)")
    quoted = subprocess.list2cmdline([path]) if os.name == "nt" else "'%s'" % path.replace("'", "'\\''")
    done = subprocess.run("%s %s" % (command, quoted), shell=True, capture_output=True, text=True)
    return done.returncode == 0, (done.stdout + done.stderr).strip()
