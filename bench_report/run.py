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

# Run-card table rows a report may print, as {row label: card key}. Published
# cards are prose with tables rather than a key block; only these rows are read.
CARD_ROWS = {"Seed": "seed", "Bench": "bench_repo_ref"}

# Score columns, by role. The first alias present in the file is used.
# A conversation is identified by arm, scenario and this column together.
COLUMNS = {
    "arm":             ("arm_id", "tier", "agent_id"),
    "scenario":        ("scenario_id",),
    "conversation":    ("conversation_id", "replicate"),
    "dimension":       ("dimension",),
    "score":           ("score_normalised", "score", "score_raw"),
    "in_scope":        ("scenario_in_A0_A2_scope",),
    "judge":           ("judge_id", "judge_model"),
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
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] not in CARD_ROWS or CARD_ROWS[cells[0]] in card:
            continue
        value = re.sub(r"[`*]", "", cells[1]).strip()
        if cells[0] == "Bench" and len(cells) > 2 and "dirty" in cells[2].lower():
            value += " (tree dirty at run time)"
        if value:
            card[CARD_ROWS[cells[0]]] = value
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


def read_scores(run_dir, judge=None, scoring_config=None, all_scenarios=False):
    """Return the primary score rows and a note of how they were selected.

    Primary means judge pass 1. If more than one judge or scoring config remains
    after that, the caller must name one: pooling them silently would report a
    number no single judge produced. Scenarios the run marks out of scope for its
    tiers are dropped unless `all_scenarios` is set, so the headline matches the
    run card's denominators.
    """
    path = _scores_file(run_dir)
    # utf-8-sig: the published per_row_scores.csv starts with a byte-order mark
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        col = {role: next((a for a in aliases if a in header), None) for role, aliases in COLUMNS.items()}
        missing = [role for role in REQUIRED if col[role] is None]
        if missing:
            raise RunFormatError("scores file has no column for: %s" % ", ".join(missing))
        raw = list(reader)

    excluded = []
    if col["in_scope"]:
        excluded = sorted({r[col["scenario"]] for r in raw if r[col["in_scope"]].strip().lower() == "false"})
        if not all_scenarios:
            raw = [r for r in raw if r[col["scenario"]] not in excluded]

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
    scope = {"column": col["in_scope"], "excluded": excluded, "included": all_scenarios}
    return rows, selection, {"corpus_column": col["corpus_sha256"] is not None, "scope": scope}


# ---------------------------------------------------------------------------
# Manifests: dates and the provenance fields a report may print
# ---------------------------------------------------------------------------
def _get(data, *keys):
    for k in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(k)
    return data


def read_manifests(run_dir):
    """Dates, plus per-arm provenance from manifests that carry a `provenance` block.

    Only named fields are read: agent spec hash, generation model, judge model and
    prompt hash per dimension, per-scenario digests, and whether the run's own
    hard-fail override fired. Engine commits and paths are never read.
    """
    starts, ends = [], []
    arms, judges, scenario_sets, hard_fail = {}, {}, set(), []
    for path in sorted(glob.glob(os.path.join(run_dir, "manifests", "*.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            continue
        if isinstance(data.get("started_at"), str):
            starts.append(data["started_at"])
        if isinstance(data.get("finished_at"), str):
            ends.append(data["finished_at"])
        prov = data.get("provenance")
        if not isinstance(prov, dict):
            continue
        arm = _get(prov, "agent", "id")
        if isinstance(arm, str):
            entry = arms.setdefault(arm, {"spec_hash": set(), "model": set()})
            for key, value in (("spec_hash", _get(prov, "agent", "spec_hash")),
                               ("model", _get(prov, "model", "model_id"))):
                if isinstance(value, str):
                    entry[key].add(value)
        for dim, judge in sorted((_get(prov, "judge") or {}).items()):
            entry = judges.setdefault(dim, {"model": set(), "prompt_hash": set()})
            for key, value in (("model", _get(judge, "model_id")), ("prompt_hash", _get(judge, "prompt_hash"))):
                if isinstance(value, str):
                    entry[key].add(value)
        digests = _get(prov, "scenarios", "scenarios")
        if isinstance(digests, dict):
            scenario_sets.add(tuple(sorted(digests.items())))
        fired = _get(prov, "execution", "hard_fail_fired")
        if isinstance(fired, bool):
            hard_fail.append(fired)
    return {
        "dates": (min(starts) if starts else None, max(ends) if ends else None),
        "arms": arms,
        "judges": judges,
        "scenario_sets": scenario_sets,
        "hard_fail_fired": hard_fail,
    }


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
def load(run_dir, judge=None, scoring_config=None, bench_root=BENCH_ROOT, all_scenarios=False):
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        raise RunFormatError("not a directory: %s" % run_dir)
    rows, selection, info = read_scores(run_dir, judge, scoring_config, all_scenarios)
    manifests = read_manifests(run_dir)
    return {
        "name": os.path.basename(run_dir.rstrip("\\/")),
        "card": read_card(run_dir),
        "rows": rows,
        "selection": selection,
        "scope": info["scope"],
        "corpus_column": info["corpus_column"],
        "dates": manifests["dates"],
        "manifests": manifests,
        "scenarios": read_scenarios(bench_root),
        "tiers": read_tiers(bench_root),
        "limitations": read_limitations(bench_root),
    }
