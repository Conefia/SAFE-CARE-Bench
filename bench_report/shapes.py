# -*- coding: utf-8 -*-
"""Shape checks: the public half of the leak check behind `--final`.

The private deny list catches what someone thought to write down. These checks
catch identifiers nobody listed, by their shape:

* Field shapes. Every value a report can print from a run (run-card keys and
  rows, manifest provenance, score-file ids) must have the shape its field
  allows. A knowledge-base id pasted into `bench_version` fails here.
* A whole-report scan for ARNs, storage URLs, AWS keys and account ids,
  10-character AWS resource ids, UUIDs, long hex or base64 blobs, email
  addresses and local paths. The one exception is hashes: 64 lowercase hex
  characters in backticks, and a 40-character commit in backticks.

Problems name the report line or the field and the rule, never the matched
text, so the check's output is safe to paste.
"""

import re

# ---------------------------------------------------------------------------
# Field shapes
# ---------------------------------------------------------------------------
_ID = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_MODEL = re.compile(r"[A-Za-z0-9._:/-]{1,80}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z")
_PROSE = re.compile(r"[^|`\n]{1,160}")
_NOT_RECORDED = re.compile(r"not_recorded|not_applicable|not_applicab|none|null|nan|", re.I)

CARD_SHAPES = [
    (re.compile(r"run_id"), _ID),
    (re.compile(r"produced_utc"), _UTC),
    (re.compile(r"bench_version"), re.compile(r"v?[0-9][A-Za-z0-9.+-]{0,39}")),
    (re.compile(r"bench_repo_ref|engine_repo_ref"), re.compile(r"[0-9a-f]{7,40}( \(tree dirty at run time\))?")),
    (re.compile(r"agent_model_id|judge(_\d+)?_model_id"), _MODEL),
    (re.compile(r"judge_prompt_sha256\S*|scenario_set_sha256|corpus_manifest_sha256|corpus_digest"), _SHA256),
    (re.compile(r"conversations_generated|conversations_errored"), re.compile(r"\d{1,6}")),
    (re.compile(r"\S*seed\S*|judge_calibration|corpus[._]verified"), _PROSE),
]

ROW_SHAPES = {
    "arm": _ID, "scenario": _ID, "conversation": _ID, "dimension": _ID,
    "agent_model": _MODEL, "config_sha256": _SHA256, "corpus_sha256": _SHA256,
}


def _ok(shape, value):
    return value is None or bool(shape.fullmatch(value))


def field_problems(run):
    """[(field, rule)] for every allow-listed value whose shape is wrong."""
    problems = set()
    for key, value in run["card"].items():
        shape = next((s for k, s in CARD_SHAPES if k.fullmatch(key)), None)
        if shape is None or not shape.fullmatch(value):
            problems.add(("run card %s" % key, "unexpected shape"))
    for row in run["rows"]:
        for field, shape in ROW_SHAPES.items():
            value = row.get(field)
            if value is not None and not _NOT_RECORDED.fullmatch(value.strip()) and not _ok(shape, value):
                problems.add(("scores %s" % field, "unexpected shape"))
    manifests = run["manifests"]
    for arm, entry in manifests["arms"].items():
        if not _ID.fullmatch(arm):
            problems.add(("manifest agent id", "unexpected shape"))
        for value in entry["spec_hash"]:
            if not _SHA256.fullmatch(value):
                problems.add(("manifest agent spec_hash", "unexpected shape"))
        for value in entry["model"]:
            if not _MODEL.fullmatch(value):
                problems.add(("manifest model id", "unexpected shape"))
    for dim, judge in manifests["judges"].items():
        if not _ID.fullmatch(dim):
            problems.add(("manifest judge name", "unexpected shape"))
        for value in judge["model"]:
            if not _MODEL.fullmatch(value):
                problems.add(("manifest judge model id", "unexpected shape"))
        for value in judge["prompt_hash"]:
            if not _SHA256.fullmatch(value):
                problems.add(("manifest judge prompt_hash", "unexpected shape"))
    for value in [d for d in manifests["dates"] if d]:
        if not _UTC.fullmatch(value):
            problems.add(("manifest date", "unexpected shape"))
    return sorted(problems)


# ---------------------------------------------------------------------------
# Whole-report scan
# ---------------------------------------------------------------------------
def _kb_like(m):
    token = m.group(0)
    return any(c.isdigit() for c in token) and any(c.isalpha() for c in token)


TEXT_RULES = [
    ("ARN", re.compile(r"\barn:aws[a-z-]*:", re.I), None),
    ("storage URL", re.compile(r"\bs3://|amazonaws\.com|\bgs://|blob\.core\.windows\.net", re.I), None),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA|AIDA|AROA|ANPA|AGPA|AIPA)[A-Z0-9]{16}\b"), None),
    ("AWS account id", re.compile(r"(?<![\d.])\d{12}(?![\d.])"), None),
    ("10-character resource id", re.compile(r"(?<![A-Za-z0-9])[A-Z0-9]{10}(?![A-Za-z0-9])"), _kb_like),
    ("UUID", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), None),
    ("base64 blob", re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{32,}={0,2}"),
     lambda m: re.search(r"[A-Z]", m.group(0)) and re.search(r"[a-z]", m.group(0)) and re.search(r"\d", m.group(0))),
    ("email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), None),
    ("local path", re.compile(r"\b[A-Za-z]:[\\/]|(?<![\w.])/(?:Users|home|tmp|var|opt|mnt|private)/"), None),
]

# Hashes the report is allowed to print: backticked sha256, backticked commit.
_ALLOWED_HEX = re.compile(r"`[0-9a-f]{64}`|`[0-9a-f]{40}`")
# at least one a-f letter, so a long decimal fraction is not a hex blob
_HEX = re.compile(r"(?<![0-9A-Za-z])(?=[0-9]*[a-f])[0-9a-f]{16,}(?![0-9A-Za-z])")


def text_hits(text):
    """[(report line, rule)] for every suspicious shape in the report."""
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for rule, pattern, keep in TEXT_RULES:
            if any(keep is None or keep(m) for m in pattern.finditer(line)):
                hits.append((lineno, rule))
        if _HEX.search(_ALLOWED_HEX.sub("``", line)):
            hits.append((lineno, "long hex outside an allowed hash"))
    return hits
