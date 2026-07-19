#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAFE-CARE Bench - dataset build pipeline.

Downloads the upstream sources, applies the documented domain filter, validates the
result, and writes both the filtered CSVs and a machine-readable manifest with
SHA-256 checksums and true logical record counts.

The filtered CSVs in `datasets/filtered/` are the OUTPUT of this script. They are
committed for convenience, but this script is the authoritative definition of how
they were produced. Anyone can re-run it and diff the manifest.

Usage
-----
    pip install datasets pandas
    python datasets/build.py                 # build all sources
    python datasets/build.py --only medqa    # build one source
    python datasets/build.py --verify        # re-check committed files against manifest

Design notes
------------
* MedMCQA is pulled from the TRAIN split, not the test split. The MedMCQA test split
  ships with `cop = -1` and empty `exp` by design - it carries no answer labels. Any
  build that draws from the test split produces an unusable benchmark file. This is
  asserted below and the build fails loudly if labels are missing.
* Filtering is a two-stage gate: a term must match, AND the match must survive the
  precision check. Subject-level metadata alone is NOT sufficient to include a row.
* Every emitted row records which terms matched it, so the filter is auditable
  row-by-row rather than only in aggregate.
"""

import argparse, csv, hashlib, json, os, re, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "filtered")
MANIFEST = os.path.join(HERE, "manifest.json")

# ---------------------------------------------------------------------------
# Domain vocabulary. Ordered, versioned, and reported in the manifest.
# ---------------------------------------------------------------------------
VOCAB_VERSION = "2.0"
CORE_TERMS = [          # a match on any of these alone qualifies a row
    "menopaus", "perimenopaus", "postmenopaus", "climacteric",
    "hot flash", "hot flush", "vasomotor", "atrophic vaginitis",
    "vaginal atrophy", "hormone replacement", "hormone therapy",
]
CONTEXT_TERMS = [       # these qualify a row ONLY alongside a supporting signal
    "estrogen", "oestrogen", "estradiol", "progestogen",
    "osteoporosis", "amenorrhea", "amenorrhoea", "endometrial cancer",
    "night sweat", "fsh", "follicle stimulating hormone",
]
# Supporting signals that make a CONTEXT term admissible. Prevents the
# "male infertility mentions estradiol" class of false positive.
SUPPORT_PATTERNS = [
    r"\bwoman\b", r"\bwomen\b", r"\bfemale\b", r"\bshe\b", r"\bher\b",
    r"\bmenstrua", r"\bperiod\b", r"\bperiods\b", r"\bovar", r"\buter",
    r"\bendometri", r"\bhysterectom", r"\bgynaec", r"\bgynec",
    r"\b4[5-9][- ]year", r"\b5[0-9][- ]year", r"\b6[0-9][- ]year",
]
# Hard exclusions - if present, drop regardless of term matches.
EXCLUDE_PATTERNS = [
    r"\bmale\b(?!\s*(and|or)\s*female)", r"\bman\b", r"\bhis\b",
    r"\bprostat", r"\btesticul", r"\bpuberty\b", r"\badolescen",
    r"\bpregnan", r"\bpostpartum\b", r"\bneonat", r"\bcontracept",
]

CORE_RE    = re.compile("|".join(re.escape(t) for t in CORE_TERMS), re.I)
CONTEXT_RE = re.compile("|".join(re.escape(t) for t in CONTEXT_TERMS), re.I)
SUPPORT_RE = re.compile("|".join(SUPPORT_PATTERNS), re.I)
EXCLUDE_RE = re.compile("|".join(EXCLUDE_PATTERNS), re.I)


def classify(text, exclude_scope=None):
    """Return (keep: bool, matched_terms: list, reason: str).

    `exclude_scope` is the text the exclusion patterns are tested against. It defaults
    to `text`, but callers should pass the QUESTION STEM ONLY. Exclusions must not be
    tested against answer text: a correct answer to "why have my periods stopped?"
    legitimately discusses pregnancy as a differential, and testing the answer would
    wrongly drop a core perimenopause question.
    """
    t = (text or "").lower()
    x = (exclude_scope if exclude_scope is not None else text or "").lower()
    core = sorted(set(m.group(0).lower() for m in CORE_RE.finditer(t)))
    ctx  = sorted(set(m.group(0).lower() for m in CONTEXT_RE.finditer(t)))

    # Precedence: an explicit core-domain term outranks an exclusion pattern.
    # "Can I still get pregnant during menopause?" is a menopause question that
    # happens to mention pregnancy - it must not be dropped by the pregnancy filter.
    if core:
        return True, core + ctx, "core_term"
    if EXCLUDE_RE.search(x):
        return False, [], "excluded_pattern"
    if ctx and SUPPORT_RE.search(t):
        return True, ctx, "context_term_with_support"
    if ctx:
        return False, ctx, "context_term_without_support"
    return False, [], "no_match"


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
SOURCES = {
    "medqa": dict(
        hf_id="bigbio/med_qa", config="med_qa_en_source", split="train",
        out="menopause_medqa.csv",
        text_cols=["question", "options"],
        exclude_cols=["question"],
        label_cols=["answer", "answer_idx"],
        license="Upstream MedQA terms (MIT for the corpus; verify before redistribution).",
    ),
    "medmcqa": dict(
        hf_id="openlifescienceai/medmcqa", config=None, split="train",
        out="menopause_medmcqa.csv",
        text_cols=["question", "opa", "opb", "opc", "opd"],
        exclude_cols=["question"],
        label_cols=["cop", "exp"],
        license="Upstream MedMCQA terms (Apache-2.0; verify before redistribution).",
    ),
    "menst": dict(
        hf_id=None, config=None, split=None,          # not on the Hub
        out="menopause_menst.csv",
        local_hint="datasets/raw/menst.csv",
        text_cols=["Question", "Answer", "Topic", "Keywords"],
        exclude_cols=["Question", "Topic"],
        label_cols=["Answer"],
        license="Upstream MENST publisher terms. Raw dump is NOT redistributed here.",
    ),
}


def load_source(key, raw_dir):
    cfg = SOURCES[key]
    local = os.path.join(raw_dir, os.path.basename(cfg.get("local_hint") or f"{key}.csv"))
    if os.path.exists(local):
        print(f"  [{key}] loading local raw file {local}")
        with open(local, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    if not cfg["hf_id"]:
        raise SystemExit(
            f"\n[{key}] no local raw file at {local} and this source is not on the "
            f"HuggingFace Hub.\nPlace the upstream dump there and re-run.\n")
    try:
        from datasets import load_dataset
    except ImportError:
        raise SystemExit("\n`pip install datasets pandas` first.\n")
    print(f"  [{key}] downloading {cfg['hf_id']} split={cfg['split']}")
    ds = (load_dataset(cfg["hf_id"], cfg["config"], split=cfg["split"])
          if cfg["config"] else load_dataset(cfg["hf_id"], split=cfg["split"]))
    return [dict(r) for r in ds]


def assert_labels_present(key, rows):
    """Fail loudly if the source carries no usable answer labels."""
    cfg = SOURCES[key]
    if key == "medmcqa":
        cops = {str(r.get("cop", "")).strip() for r in rows}
        if cops <= {"-1", "", "None"}:
            raise SystemExit(
                f"\n[{key}] ABORT: every `cop` value is -1 or empty.\n"
                f"This is the signature of the MedMCQA TEST split, which ships unlabeled.\n"
                f"Set split='train' or 'validation'. Refusing to emit an unusable file.\n")
    missing = [c for c in cfg["label_cols"] if rows and c not in rows[0]]
    if missing:
        raise SystemExit(f"\n[{key}] ABORT: expected label column(s) missing: {missing}\n")


def build_one(key, raw_dir):
    cfg = SOURCES[key]
    rows = load_source(key, raw_dir)
    print(f"  [{key}] {len(rows)} upstream rows")
    assert_labels_present(key, rows)

    kept, reasons = [], {}
    for r in rows:
        blob = " ".join(str(r.get(c, "") or "") for c in cfg["text_cols"])
        xscope = " ".join(str(r.get(c, "") or "") for c in cfg.get("exclude_cols", cfg["text_cols"]))
        keep, terms, why = classify(blob, exclude_scope=xscope)
        reasons[why] = reasons.get(why, 0) + 1
        if keep:
            out = dict(r)
            out["_matched_terms"] = "|".join(terms)
            out["_match_reason"] = why
            out["_manual_review"] = ""      # reviewer fills: keep / drop / edit
            kept.append(out)

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, cfg["out"])
    if kept:
        cols = list(kept[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in kept:
                w.writerow({c: r.get(c, "") for c in cols})
    print(f"  [{key}] kept {len(kept)} / {len(rows)}  ->  {cfg['out']}")
    print(f"  [{key}] filter outcomes: {reasons}")
    return dict(source=key, hf_id=cfg["hf_id"], split=cfg["split"], file=cfg["out"],
                upstream_rows=len(rows), kept_rows=len(kept), filter_outcomes=reasons,
                license=cfg["license"], sha256=sha256(path) if kept else None,
                logical_records=logical_count(path) if kept else 0)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def logical_count(path):
    """True record count via a standards-compliant CSV parser, NOT a line count."""
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def verify():
    if not os.path.exists(MANIFEST):
        raise SystemExit("No manifest.json. Run the build first.")
    man = json.load(open(MANIFEST, encoding="utf-8"))
    bad = 0
    for e in man["datasets"]:
        p = os.path.join(OUT_DIR, e["file"])
        if not os.path.exists(p):
            print(f"MISSING  {e['file']}"); bad += 1; continue
        got_sha, got_n = sha256(p), logical_count(p)
        ok = got_sha == e["sha256"] and got_n == e["logical_records"]
        print(f"{'OK      ' if ok else 'MISMATCH'} {e['file']}  n={got_n} (manifest {e['logical_records']})")
        bad += 0 if ok else 1
    print("\nVERIFY PASSED" if not bad else f"\nVERIFY FAILED ({bad})")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(SOURCES))
    ap.add_argument("--raw-dir", default=os.path.join(HERE, "raw"))
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        sys.exit(verify())

    keys = [a.only] if a.only else list(SOURCES)
    print(f"SAFE-CARE Bench dataset build - vocabulary v{VOCAB_VERSION}\n")
    entries = [build_one(k, a.raw_dir) for k in keys]

    man = dict(
        generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        vocabulary_version=VOCAB_VERSION,
        core_terms=CORE_TERMS, context_terms=CONTEXT_TERMS,
        support_patterns=SUPPORT_PATTERNS, exclude_patterns=EXCLUDE_PATTERNS,
        note=("Logical record counts come from a standards-compliant CSV parser. They will differ "
              "from newline counts wherever a field contains embedded newlines."),
        datasets=entries)
    if a.only and os.path.exists(MANIFEST):
        old = json.load(open(MANIFEST, encoding="utf-8"))
        keep = [e for e in old["datasets"] if e["source"] != a.only]
        man["datasets"] = keep + entries
    json.dump(man, open(MANIFEST, "w", encoding="utf-8"), indent=2)
    print(f"\nwrote {MANIFEST}")
    print("Next: review rows where _match_reason == 'context_term_with_support',")
    print("      record the outcome in _manual_review, and update DATASET_CARD.md.")


if __name__ == "__main__":
    main()
