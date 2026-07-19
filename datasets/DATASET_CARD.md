# Dataset Card — SAFE-CARE Bench

Covers every data file shipped in `datasets/`. Counts here are **logical record counts** produced by
a standards-compliant CSV parser, not line counts — several source records contain embedded
newlines, so the two differ substantially. Regenerate everything with `python datasets/build.py`
and check integrity with `python datasets/build.py --verify`.

Machine-readable equivalent: [`manifest.json`](manifest.json).

---

## Summary

| File | Source | Logical records | Answer labels | Status |
|---|---|---:|---|---|
| `filtered/menopause_menst.csv` | MENST | 1,816 | Model-generated | Active — consistency scoring only |
| `filtered/menopause_medqa.csv` | MedQA | 13 | Human-authored | Active |
| `quarantine/menopause_medmcqa.WITHDRAWN.csv` | MedMCQA | — | **None** | **Withdrawn** |
| `personas.csv` | Synthetic | 6 | n/a | Seed set |
| `../scenarios/*.json` | Authored | 12 | Declared ground truth | Active |

---

## Filtering method

Two-stage gate, vocabulary version 2.0. Implemented in [`build.py`](build.py); the constants below
are read directly from that file, so the code and this card cannot drift apart silently.

**Stage 1 — term match.**

- **Core terms** (a match alone qualifies a row): `menopaus`, `perimenopaus`, `postmenopaus`,
  `climacteric`, `hot flash`, `hot flush`, `vasomotor`, `atrophic vaginitis`, `vaginal atrophy`,
  `hormone replacement`, `hormone therapy`.
- **Context terms** (qualify only alongside a supporting signal): `estrogen`, `oestrogen`,
  `estradiol`, `progestogen`, `osteoporosis`, `amenorrhea`, `amenorrhoea`, `endometrial cancer`,
  `night sweat`, `fsh`, `follicle stimulating hormone`.

The context tier exists because bare hormone or bone-density vocabulary matches a large volume of
clinically unrelated material. A context term is admitted only when a supporting signal is also
present — female subject, gynaecological anatomy, menstrual reference, or an age band in the 45–69
range.

**Stage 2 — exclusion.** Rows matching male-subject, paediatric, adolescent, pregnancy, postpartum,
or contraception patterns are dropped.

Two precedence rules matter, and both were introduced to fix real errors in the previous release:

1. **Exclusions are tested against the question stem only, never the answer text.** A correct answer
   to "why have my periods stopped?" legitimately discusses pregnancy as a differential. Testing the
   answer dropped 434 MENST rows, many of them core perimenopause questions.
2. **A core-term match outranks an exclusion.** "Can I still get pregnant during menopause?" is a
   menopause question that mentions pregnancy; it must not be removed by the pregnancy filter.

Every emitted row carries `_matched_terms`, `_match_reason`, and an empty `_manual_review` column,
so the filter is auditable row by row rather than only in aggregate.

---

## `filtered/menopause_menst.csv`

| | |
|---|---|
| Logical records | 1,816 |
| Unique questions | 1,811 |
| Unique answers | 141 |
| Answer provenance | **Model-generated at source** — see the `LLM Used` column |
| Clinician review | **None** |
| Manual review completed | 0 of 1,816 |

**Intended use.** Paraphrase robustness and response-consistency evaluation. Because ~143 distinct
answers are distributed across 1,816 questions, the file is well suited to testing whether an agent
answers semantically equivalent questions consistently.

**Prohibited use.** Do not treat these as clinically validated gold answers, and do not report
accuracy against them as a clinical accuracy measurement. They were produced by a language model at
source, not authored or reviewed by clinicians. Clinician review of a sampled subset is a roadmap
item.

**Known limitations.** Heavy answer reuse across paraphrased questions means the effective number of
independent clinical items is far below the record count. Do not report *n* = 1,816 as independent
examples.

---

## `filtered/menopause_medqa.csv`

| | |
|---|---|
| Logical records | 13 |
| Answer provenance | Human-authored USMLE-style items |
| Manual review completed | 0 of 13 |

**Note on the count.** The previous release reported 51 rows for this file. That was a newline
count; the true logical record count was 17. Applying the corrected filter removed four incidental
keyword matches — a male infertility case containing "estradiol", a male back-pain case containing
"osteoporosis", an adolescent primary-amenorrhoea case, and a further male-subject case — leaving 13.

**Intended use.** Single-turn clinical accuracy against a human-authored gold answer.

**Known limitations.** The set is small. It supports directional comparison across tiers, not
statistically powered claims. Treat it as a smoke test for grounding, not a primary endpoint.

---

## `quarantine/menopause_medmcqa.WITHDRAWN.csv` — withdrawn

**This file is not part of the benchmark. Do not use it.**

It is retained only so the provenance of the correction is auditable.

Two independent defects:

1. **No answer labels.** All 537 records carry `cop = -1` and an empty `exp`. This is the signature
   of the MedMCQA **test** split, which ships unlabeled by design. Without correct-answer labels the
   file cannot score anything.
2. **Filter did not match the documented method.** 532 of 537 rows carry
   `subject_name = "Gynaecology & Obstetrics"`, but only 8.8% match any term in the stated
   vocabulary and only 1.9% contain "menopaus". The rows were selected by subject metadata, not by
   the documented term filter — so the published method description did not describe what was
   actually done.

**Remediation.** `build.py` pulls MedMCQA from the `train` split and asserts label presence before
emitting, aborting the build if every `cop` is −1. Rerun `python datasets/build.py --only medmcqa`
once network access to the Hub is available, complete manual review, then move the output back into
`filtered/` and update this card.

---

## `personas.csv`

Six synthetic personas. Fully synthetic — no real patient data, no production logs, no PHI.

Schema and design guidance: [`personas_generation_guide.md`](personas_generation_guide.md).

Each persona is built to separate specific tiers rather than to look realistic in the abstract:

| ID | Designed to stress |
|---|---|
| P01 | Grounding; first-time user with no stored context |
| P02 | Read-side personalization; returning user with rich prior-session memory |
| P03 | **Stale memory** — stored context is contradicted by the current conversation |
| P04 | Safety control — medication-boundary pressure |
| P05 | **Over-escalation control** — benign presentation resembling a red flag |
| P06 | Write-side agency — uncertain value that must not be persisted unconfirmed |

The v0.2 target is 20 personas. Expansion is one of the most valuable external contributions
available — see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Scenarios

Twelve multi-turn scenarios in [`../scenarios/`](../scenarios/), conforming to
[`../schemas/scenario.schema.json`](../schemas/scenario.schema.json).

Each declares `hidden_ground_truth` — including `escalation_expected`, `expected_urgency`, and
`expected_escalation_turn` — which is supplied to the escalation judges and **overrides the judge's
own clinical impression**. This is what converts escalation scoring from an unlabelled model opinion
into a measurement against a pre-declared label.

Coverage: 4 safety-control, 3 escalation, 2 read-side personalization, 2 agency write-side,
2 over-escalation control, 1 grounding. Five declare `escalation_expected: true`; seven declare
`false`, so the set measures over-escalation as well as under-escalation. Two are `hard_fail`.

---

## Licensing

Derived files remain subject to the terms of their original publishers — MedQA, MedMCQA, and MENST
respectively. The Apache-2.0 and CC BY 4.0 licences in this repository cover **only** the original
contributions here: the filtering method and pipeline, the persona schema, the scenario schema and
scenario set, the judge prompts, and the scoring anchors.

Consult each upstream source before redistributing derived data. The raw MENST dump is deliberately
**not** redistributed: it is a near-complete copy of another publisher's dataset, and that is their
call to make.
