# Dataset Filtering Method

Rationale for the domain filter. The authoritative implementation is
[`build.py`](build.py); the per-file results, counts, and checksums are in
[`DATASET_CARD.md`](DATASET_CARD.md) and [`manifest.json`](manifest.json).

> **Version 2.0.** Version 1.0 used a flat 13-term substring match. It is superseded. The v1.0
> description also did not match what was actually applied to the MedMCQA file — see
> [Correction history](#correction-history).

---

## The problem with flat keyword matching

A single undifferentiated term list fails in both directions on medical corpora.

**False positives.** Hormone and bone-density vocabulary appears throughout general medicine. A flat
list containing `estradiol` and `osteoporosis` admits male infertility workups, male osteoporosis
cases, adolescent primary amenorrhoea, and anaesthesia questions that happen to involve an older
patient. All four classes were present in the v1.0 MedQA output.

**False negatives.** Conversational health questions often describe the domain without naming it.
"My periods haven't come for a few months" is a core perimenopause presentation containing no term
from the v1.0 list.

## Two-stage gate

**Stage 1 — tiered term match.**

*Core terms* name the domain directly and qualify a row on their own. *Context terms* are
domain-adjacent but individually ambiguous, and are admitted only when a **supporting signal** is
also present: a female subject, gynaecological anatomy, a menstrual reference, or an age band in the
45–69 range. This is what separates "a 52-year-old woman with osteoporosis" from "a 65-year-old man
with osteoporosis".

**Stage 2 — exclusion.** Male-subject, paediatric, adolescent, pregnancy, postpartum, and
contraception patterns drop a row.

## Two precedence rules

Both exist because their absence produced measurable errors.

**Exclusions are tested against the question stem only, never the answer.** A correct answer to
"why have my periods stopped?" legitimately discusses pregnancy as a differential diagnosis. Testing
the answer text removed 434 MENST rows, a large share of them core perimenopause questions.

**A core-term match outranks an exclusion.** "Can I still get pregnant during menopause?" is a
menopause question that mentions pregnancy. Without this rule the pregnancy filter removes it.

Order of evaluation in `classify()`: core match → exclusion → context match with support.

## Auditability

Every retained row carries three added columns:

| Column | Meaning |
|---|---|
| `_matched_terms` | Which vocabulary terms fired |
| `_match_reason` | `core_term` / `context_term_with_support` |
| `_manual_review` | Empty. A reviewer records `keep`, `drop`, or `edit` |

Rows admitted by `context_term_with_support` are the ones most likely to need human judgment, and
are the recommended starting point for manual review.

## What this method does not do

- **No stemming or fuzzy matching.** Precision is preferred over recall; a missed row costs less
  than a wrong row in a safety benchmark.
- **No semantic or embedding-based retrieval.** A keyword gate is inspectable and reproducible by
  anyone without a model dependency. Semantic filtering is a roadmap item.
- **No clinical validation.** Filtering establishes topical relevance, not clinical correctness or
  answer quality. See the per-file limitations in [`DATASET_CARD.md`](DATASET_CARD.md).

---

## Correction history

**v1.0 → v2.0.**

The v1.0 MedMCQA output was selected by `subject_name = "Gynaecology & Obstetrics"` (532 of 537
rows) rather than by the documented term vocabulary — only 8.8% of those rows match any v1.0 term
and only 1.9% contain "menopaus". It was also drawn from the MedMCQA test split, which ships with
`cop = -1` and no explanations, so it carried no answer labels at all. That file is withdrawn; see
[`quarantine/README.md`](quarantine/README.md). `build.py` now asserts label presence and aborts the
build rather than emitting an unlabeled file.

The v1.0 row counts published for MedQA (51) and MENST (5,273) were newline counts. The true logical
record counts were 17 and 1,873. All counts are now produced by a standards-compliant CSV parser and
recorded in `manifest.json` alongside a SHA-256 for each file.
