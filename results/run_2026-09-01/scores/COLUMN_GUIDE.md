# 2 · Per-row scores

`per_row_scores.csv` — **1,070 rows**, one per (scenario × tier × dimension × repeat).
No averages anywhere in this file. UTF-8 with BOM, so Excel opens it correctly.

## Why 1,070 and not 1,188

- 12 scenarios × 3 tiers × 3 repeats = **108 conversations**
- 107 of them completed; **1** errored (A2 / S009 / R3 — see `05_coverage_log.md`) and
  produced **no** dimension rows at all
- 107 × **10 scored dimensions** = **1,070**

The rubric declares **eleven** dimensions. The eleventh, `model_answered`, produced **zero
rows in the entire study** — no bench scenario declares an expectation for it, so it was
marked inapplicable and dropped everywhere. That is the harness's N/A mechanism working
correctly, and it is the contrast that matters for question 2 in `ANSWERS.md`: the ten
judged dimensions never use it.

## Columns

| Column | What it is |
|---|---|
| `scenario_id` | S001…S012 |
| `tier` | A0, A1, A2 |
| `dimension` | one of the ten judged dimensions |
| `judge_prompt_file` | **the judge prompt file that produced this row**, as a repo path |
| `judge_prompt_id` | the judge's id as recorded in the run manifest |
| `judge_prompt_hash` | SHA-256 of the judge prompt text, from the run manifest — this is what pins *which version* of the prompt ran |
| `judge_model` | backend/model of the judge for this row |
| `judge_temperature` | 0.0 throughout |
| `replicate` | **R1, R2, R3** — the three repeats |
| `run_id` | the stored run directory this row came from |
| `score` | the judged score, 0.0–1.0. Blank only if the dimension errored |
| `passed` | the judge's own pass mark, not a threshold applied here |
| `applicable` | whether the dimension was applied. **`True` on every one of these 1,070 rows** — see `ANSWERS.md` question 2 |
| `scored_on_turns_1indexed` | which turn(s) the dimension was scored on, numbered as in the transcript files |
| `scored_on_turns_0indexed_as_in_rationale` | the same turns numbered as the `judge_rationale` text numbers them |
| `judge_context_setting` | `turn` = the judge saw only that one exchange. `conversation` = it also saw the turns **before** it |
| `judge_sources_setting` | `retrieved` = the judge was also shown that turn's retrieved passages. `none` = it was not |
| `scenario_status` | `ok` or `error` for the conversation as a whole |
| `scenario_in_A0_A2_scope` | `False` for S003, S009, S010, which declare a minimum tier above A2 |
| `scenario_escalation_warranted` | the ground-truth escalation label from the scenario's tags |
| `judge_rationale` | **the judge's written reason, verbatim and untrimmed** |

## Two gotchas that will otherwise cost a reviewer an hour

**1. The rationale numbers turns from 0; the transcripts number them from 1.**
A `judge_rationale` beginning `turn 3:` refers to the **fourth** turn of the conversation.
`scored_on_turns_1indexed` and `scored_on_turns_0indexed_as_in_rationale` give both
numberings for exactly this reason. The transcript files in `01_transcripts/` are
1-indexed and label each heading with its record index too.

**2. `applicable = True` does not mean the dimension was meaningful at that tier.**
It means the harness applied it. Every judged dimension applies unconditionally by design.
`citation_grounding` at A0 is `applicable = True` and scores **0.00 on all 36 A0
conversations**, on a tier that has no retrieval at all. Read `ANSWERS.md` question 2
before using any per-tier mean that includes it.

## Judge prompt files

The ten prompts that produced these rows are in the repo at `bench_run/judges/`, and their
hashes are in every run manifest (copies in `manifests/`). Per-dimension settings:

| Dimension | Judge prompt file | Context shown | Sources shown | Scored on |
|---|---|---|---|---|
| medical_accuracy | `bench_run/judges/medical_accuracy.yaml` | turn only | retrieved | last turn |
| safety_singleturn | `bench_run/judges/safety_singleturn.yaml` | turn only | retrieved | signal turn |
| safety_multiturn | `bench_run/judges/safety_multiturn.yaml` | conversation | retrieved | last turn |
| completeness | `bench_run/judges/completeness.yaml` | turn only | retrieved | last turn |
| empathy_tone | `bench_run/judges/empathy_tone.yaml` | conversation | none | last turn |
| conversational_coherence | `bench_run/judges/conversational_coherence.yaml` | conversation | none | last turn |
| personalization | `bench_run/judges/personalization.yaml` | conversation | none | last turn |
| citation_grounding | `bench_run/judges/citation_grounding.yaml` | turn only | retrieved | last turn |
| escalation_singleturn | `bench_run/judges/escalation_singleturn.yaml` | turn only | none | **signal turn** |
| escalation_multiturn | `bench_run/judges/escalation_multiturn.yaml` | conversation | none | **signal turn** |

"Conversation" means the turns *before* the scored turn. It never means the whole
conversation — see `ANSWERS.md` question 3.
