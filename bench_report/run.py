# -*- coding: utf-8 -*-
"""Read a published run directory and the bench definitions it is scored against.

This is the only module that knows the run format. Everything it returns is
allow-listed: a field that is not named here cannot reach a report.
"""

import csv, glob, json, os, re

BENCH_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIERS = ["A0", "A1", "A2", "A3", "A4"]
ESCALATION_DIMS = ("escalation_singleturn", "escalation_multiturn")
NOT_APPLICABLE = {"not_applicable", "not_applicab"}   # the second is a truncation seen in run cards
MISSING = {"", "not_recorded", "none", "null", "nan"} | NOT_APPLICABLE

# Run-card keys a report may print. Everything else in the card is ignored on
# purpose: cards can carry live account identifiers that must never be published.
CARD_KEYS = re.compile(
    r"^(run_id|produced_utc|bench_version|bench_repo_ref|agent_model_id"
    r"|judge(_\d+)?_model_id|judge_prompt_sha256\S*|scenario_set_sha256"
    r"|corpus_manifest_sha256|corpus_digest|corpus[._]verified|\S*seed\S*"
    r"|judge_calibration|conversations_generated|conversations_errored)$")

# Score columns, by role. The first alias present in the file is used.
COLUMNS = {
    "arm":             ("arm_id", "tier", "agent_id"),
    "scenario":        ("scenario_id",),
    "conversation":    ("conversation_id",),
    "dimension":       ("dimension",),
    "score":           ("score_normalised", "score", "score_raw"),
    "judge":           ("judge_id",),
    "judge_pass":      ("judge_pass",),
    "scoring_config":  ("scoring_config",),
    "parse_ok":        ("parse_ok",),
    "config_sha256":   ("config_sha256",),
    "corpus_sha256":   ("corpus_manifest_sha256",),
    "agent_model":     ("agent_model_id",),
}
REQUIRED = ("arm", "scenario", "conversation", "dimension", "score")


class RunFormatError(Exception):
    """The run directory cannot be read without guessing."""


# ---------------------------------------------------------------------------
# Run card
# ---------------------------------------------------------------------------
def read_card(run_dir):
    path = os.path.join(run_dir, "RUN_CARD.md")
    if not os.path.isfile(path):
        raise RunFormatError("no RUN_CARD.md in %s" % os.path.basename(run_dir))
    with open(path, encoding="utf-8") as f:
        text = f.read()
    block = re.search(r"^```[^\n]*\n(.*?)^```", text, re.S | re.M)
    card = {}
    for line in (block.group(1) if block else "").splitlines():
        m = re.match(r"^([A-Za-z0-9_.]+):\s*(.*?)\s*(?:\s#.*)?$", line)
        if m and CARD_KEYS.match(m.group(1)) and m.group(2):
            card[m.group(1)] = m.group(2)
    return card


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------
def _scores_file(run_dir):
    files = sorted(glob.glob(os.path.join(run_dir, "scores", "*.csv")))
    if len(files) == 1:
        return files[0]
    preferred = os.path.join(run_dir, "scores", "per_row_scores.csv")
    if preferred in files:
        return preferred
    raise RunFormatError("expected one scores/*.csv (or scores/per_row_scores.csv), found %d" % len(files))


def _score(value, parse_ok):
    if parse_ok is not None and parse_ok.strip().lower() == "false":
        return None
    if value is None or value.strip().lower() in MISSING:
        return None
    return float(value)


def read_scores(run_dir, judge=None, scoring_config=None):
    """Return the primary score rows and a note of how they were selected.

    Primary means judge pass 1. If more than one judge or scoring config remains
    after that, the caller must name one: pooling them silently would report a
    number no single judge produced.
    """
    path = _scores_file(run_dir)
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        col = {role: next((a for a in aliases if a in header), None) for role, aliases in COLUMNS.items()}
        missing = [role for role in REQUIRED if col[role] is None]
        if missing:
            raise RunFormatError("scores file has no column for: %s" % ", ".join(missing))
        raw = list(reader)

    selection = {}
    if col["judge_pass"]:
        raw = [r for r in raw if r[col["judge_pass"]] == "1"]
        selection["judge_pass"] = "1"
    for role, wanted in (("judge", judge), ("scoring_config", scoring_config)):
        if not col[role]:
            continue
        values = sorted({r[col[role]] for r in raw})
        if wanted is None and len(values) > 1:
            flag = "--judge" if role == "judge" else "--scoring-config"
            raise RunFormatError("scores mix %s values %s; choose one with %s" % (col[role], ", ".join(values), flag))
        wanted = wanted if wanted is not None else (values[0] if values else None)
        raw = [r for r in raw if r[col[role]] == wanted]
        selection[col[role]] = wanted
    if not raw:
        raise RunFormatError("no score rows left after selecting %s" % selection)

    rows = []
    for r in raw:
        get = lambda role: r[col[role]] if col[role] else None
        rows.append({
            "arm": get("arm"),
            "scenario": get("scenario"),
            "conversation": get("conversation"),
            "dimension": get("dimension"),
            "score": _score(get("score"), get("parse_ok")),
            "config_sha256": get("config_sha256"),
            "corpus_sha256": get("corpus_sha256"),
            "agent_model": get("agent_model"),
        })
    return rows, selection, {"corpus_column": col["corpus_sha256"] is not None}


# ---------------------------------------------------------------------------
# Manifests: dates only
# ---------------------------------------------------------------------------
def read_dates(run_dir):
    starts, ends = [], []
    for path in sorted(glob.glob(os.path.join(run_dir, "manifests", "*.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if isinstance(data.get("started_at"), str):
                starts.append(data["started_at"])
            if isinstance(data.get("finished_at"), str):
                ends.append(data["finished_at"])
    return (min(starts) if starts else None, max(ends) if ends else None)


# ---------------------------------------------------------------------------
# Bench definitions: scenarios, tiers, limitations
# ---------------------------------------------------------------------------
def read_scenarios(bench_root=BENCH_ROOT):
    scenarios = {}
    for path in sorted(glob.glob(os.path.join(bench_root, "scenarios", "*.json"))):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        scenarios[d["scenario_id"]] = {
            "escalation_expected": bool(d["hidden_ground_truth"]["escalation_expected"]),
            "hard_fail": bool(d.get("hard_fail", False)),
        }
    return scenarios


def read_tiers(bench_root=BENCH_ROOT):
    """Bundle name and enabled flags per ladder tier, from agent_configs/*.yaml.

    Parsed by line rather than with a YAML library so the report stays
    standard-library only; the fields read are flat and fixed by the configs.
    """
    tiers = {}
    for path in sorted(glob.glob(os.path.join(bench_root, "agent_configs", "*.yaml"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        agent = re.search(r'^agent_id:\s*"([^"]+)"', text, re.M)
        if not agent or agent.group(1) not in TIERS:
            continue
        bundle = re.search(r'^bundle_added:\s*"([^"]+)"', text, re.M)
        flags = re.search(r"^  flags_enabled:\s*\n((?:\s+- .*\n)+)", text, re.M)
        tiers[agent.group(1)] = {
            "bundle": bundle.group(1) if bundle else None,
            "flags": re.findall(r"- (\w+)", flags.group(1)) if flags else [],
        }
    return tiers


def read_limitations(bench_root=BENCH_ROOT):
    """The numbered Known limitations in ROADMAP.md, as {bold title: full text}."""
    with open(os.path.join(bench_root, "ROADMAP.md"), encoding="utf-8") as f:
        text = f.read()
    section = re.search(r"^## Known limitations\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not section:
        raise RunFormatError("ROADMAP.md has no 'Known limitations' section")
    items = {}
    for item in re.split(r"\n(?=\d+\. )", section.group(1)):
        body = re.sub(r"^\d+\.\s+", "", " ".join(line.strip() for line in item.strip().splitlines()))
        m = re.match(r"\*\*(.+?)\*\*", body)
        if m:
            items[m.group(1)] = body
    return items


# ---------------------------------------------------------------------------
def load(run_dir, judge=None, scoring_config=None, bench_root=BENCH_ROOT):
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        raise RunFormatError("not a directory: %s" % run_dir)
    rows, selection, info = read_scores(run_dir, judge, scoring_config)
    return {
        "name": os.path.basename(run_dir.rstrip("\\/")),
        "card": read_card(run_dir),
        "rows": rows,
        "selection": selection,
        "corpus_column": info["corpus_column"],
        "dates": read_dates(run_dir),
        "scenarios": read_scenarios(bench_root),
        "tiers": read_tiers(bench_root),
        "limitations": read_limitations(bench_root),
    }
