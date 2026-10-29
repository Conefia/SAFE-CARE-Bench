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

# Run-card keys a report may print, as published cards name them in their key
# block. Everything else in the card is ignored on purpose: cards can carry live
# account identifiers that must never be published.
CARD_KEYS = re.compile(r"^(produced_utc|judge_model_id|judge_prompt_sha256)$")

# Run-card table rows a report may print, as {row label: card key}. Published
# cards are prose with tables rather than a key block; only these rows are read.
# The engine repository is private, but its commit names the version that ran.
CARD_ROWS = {"Seed": "seed", "Bench": "bench_commit", "Engine": "engine_commit"}

# Run-card headings a report may point to, as {key: heading pattern}. Only the
# section number is kept, never the text under the heading.
CARD_SECTIONS = {
    "models": re.compile(r"^## (\d+)\. Models\b", re.M),
    "defects": re.compile(r"^## (\d+)\. Known defects\b", re.M),
}
DIVERGENCES = re.compile(r"^### .*declared divergences", re.M | re.I)

# Score columns, by role, as the published scores file names them; no other names
# are accepted. A conversation is identified by arm, scenario and replicate together.
COLUMNS = {
    "arm":          "tier",
    "scenario":     "scenario_id",
    "conversation": "replicate",
    "dimension":    "dimension",
    "score":        "score",
    "in_scope":     "scenario_in_A0_A2_scope",
    "judge":        "judge_model",
}


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
        if cells[0] in ("Bench", "Engine") and len(cells) > 2 and "dirty" in cells[2].lower():
            value += " (tree dirty at run time)"
        if value:
            card[CARD_ROWS[cells[0]]] = value
    return card


def read_card_sections(run_dir):
    """{key: section number} for the run-card sections a report points readers to."""
    with open(os.path.join(run_dir, "RUN_CARD.md"), encoding="utf-8") as f:
        text = f.read()
    sections = {}
    for key, pattern in CARD_SECTIONS.items():
        m = pattern.search(text)
        if m:
            sections[key] = m.group(1)
    m = DIVERGENCES.search(text)
    if m:
        parents = re.findall(r"^## (\d+)\. ", text[:m.start()], re.M)
        if parents:
            sections["divergences"] = parents[-1]
    return sections


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


def _score(value):
    if value is None or value.strip().lower() in MISSING:
        return None
    return float(value)


def read_scores(run_dir, judge=None, all_scenarios=False):
    """Return the score rows, how they were selected, and the scenario scope.

    The file must use the published column names. If it holds more than one judge
    model, the caller must name one: pooling them silently would report a number
    no single judge produced. Scenarios the run marks out of scope for its tiers
    are dropped unless `all_scenarios` is set, so the headline matches the run
    card's denominators.
    """
    path = _scores_file(run_dir)
    # utf-8-sig: the published per_row_scores.csv starts with a byte-order mark
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        missing = [name for name in COLUMNS.values() if name not in header]
        if missing:
            raise RunFormatError(
                "%s is not in the published run format: it has no column %s. bench_report reads only "
                "the published format; see scores/COLUMN_GUIDE.md in a published run"
                % (os.path.basename(path), ", ".join(missing)))
        raw = list(reader)

    col = COLUMNS
    excluded = sorted({r[col["scenario"]] for r in raw if r[col["in_scope"]].strip().lower() == "false"})
    if not all_scenarios:
        raw = [r for r in raw if r[col["scenario"]] not in excluded]

    values = sorted({r[col["judge"]] for r in raw})
    if judge is None and len(values) > 1:
        raise RunFormatError("scores mix %s values %s; choose one with --judge" % (col["judge"], ", ".join(values)))
    judge = judge if judge is not None else (values[0] if values else None)
    raw = [r for r in raw if r[col["judge"]] == judge]
    selection = {col["judge"]: judge}
    if not raw:
        raise RunFormatError("no score rows left after selecting %s" % selection)

    rows = [{
        "arm": r[col["arm"]],
        "scenario": r[col["scenario"]],
        "conversation": r[col["conversation"]],
        "dimension": r[col["dimension"]],
        "score": _score(r[col["score"]]),
    } for r in raw]
    scope = {"column": col["in_scope"], "excluded": excluded, "included": all_scenarios}
    return rows, selection, scope


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

    Only named fields are read: agent spec hash, generation model, corpus set,
    corpus digest and corpus preflight result per arm, judge model and prompt hash
    per dimension, per-scenario digests, and whether the run's own hard-fail
    override fired. Engine commits and paths are never read from here;
    the report takes the engine commit from the run card only.
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
            entry = arms.setdefault(arm, {"spec_hash": set(), "model": set(), "corpus_set": set(),
                                          "corpus_digest": set(), "corpus_verified": set()})
            for key, value in (("spec_hash", _get(prov, "agent", "spec_hash")),
                               ("model", _get(prov, "model", "model_id")),
                               ("corpus_set", _get(prov, "corpus", "set")),
                               ("corpus_digest", _get(prov, "corpus", "digest"))):
                if isinstance(value, str):
                    entry[key].add(value)
            # The corpus preflight's result: true, false, "offline" or "not_applicable".
            verified = _get(prov, "execution", "corpus", "verified")
            if isinstance(verified, bool):
                entry["corpus_verified"].add("true" if verified else "false")
            elif isinstance(verified, str):
                entry["corpus_verified"].add(verified)
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
def load(run_dir, judge=None, bench_root=BENCH_ROOT, all_scenarios=False):
    run_dir = os.path.abspath(run_dir)
    if not os.path.isdir(run_dir):
        raise RunFormatError("not a directory: %s" % run_dir)
    rows, selection, scope = read_scores(run_dir, judge, all_scenarios)
    manifests = read_manifests(run_dir)
    return {
        "name": os.path.basename(run_dir.rstrip("\\/")),
        "card": read_card(run_dir),
        "card_sections": read_card_sections(run_dir),
        "rows": rows,
        "selection": selection,
        "scope": scope,
        "dates": manifests["dates"],
        "manifests": manifests,
        "scenarios": read_scenarios(bench_root),
        "tiers": read_tiers(bench_root),
        "limitations": read_limitations(bench_root),
    }
