# Run card — 1 September 2026, tiers A0–A2

Everything here is read from the nine stored run manifests unless a row says otherwise. Rows
marked **not in manifest** come from configuration or a runbook and are weaker evidence.

## 1. Scope

| | |
|---|---|
| Tiers | A0 (ungoverned), A1 (grounding bundle), A2 (safety control) |
| Scenarios | 12 authored, S001–S012 |
| Repeats | 3 per scenario per tier |
| Conversations | **108**; 107 completed, 1 errored |
| Agent turns | **305** |
| Dimension rows | **1,070** (107 × 10 judged dimensions) |
| Headline scope | **9 scenarios**, 27 conversations per tier, 75 turns per tier |

Three scenarios (S003, S009, S010) declare a minimum tier above A2 because they stress stored
memory and profile persistence that no tier here provides. They were run and scored, and their
rows carry `scenario_in_A0_A2_scope = False`. Filter on that column to reproduce the headline
denominators. Do not pool all twelve without saying so.

**The unit of analysis is the scenario (n = 9), not the conversation (n = 27).** The design is
balanced, so the scenario-level mean and the pooled mean are identically equal; the standard
error is not. Use the scenario-level standard error, which is a median factor of 1.61 larger.

## 2. Models

| Component | Value | In manifest? |
|---|---|---|
| Generation | `gpt-4o-mini`, temperature 0.0, `max_tokens` 800 | yes |
| Scoring judges (all ten) | `gpt-4o-mini`, temperature 0.0, per-judge prompt hashes recorded | yes |
| Grounding classifier (A1, A2) | `gpt-4o-mini`, temperature 0.0 | **not in manifest** |
| Guardrail classifiers (A2) | `gpt-4o-mini`, temperature 0.0 | **not in manifest** |
| Embedding | `amazon.titan-embed-text-v2:0` | **not in manifest**, from setup runbook |

### The model-version problem

`gpt-4o-mini` is a floating alias. No `system_fingerprint` and no dated snapshot id were
recorded, so **the exact endpoint behind that alias on 1 September 2026 is not recoverable from
these artifacts.** This is the largest reproducibility gap in the run and it is not fixable
after the fact. Future runs must pin a dated snapshot id.

### Judge and agent share a model family

Both generation and judging used `gpt-4o-mini`. Self-preference is a documented bias in
LLM-as-judge scoring and nothing in this run controls for it. No judge–human agreement has been
measured. Both are open.

## 3. Determinism

| | |
|---|---|
| Temperature | 0.0 everywhere |
| Seed | **not exposed by the provider**; the harness sets none |

The three repeats are **three independent invocations at temperature zero, not three seeds.**
Temperature zero is not determinism: 44 of 270 in-scope cells (16.3%) returned a non-identical
score across replicates. Because no seed exists the tiers were not matched pairwise, so some
sampling variance sits inside every tier-to-tier delta.

One guardrail decision was itself non-reproducible: on S007 at A2, turn 3, the incoming
guardrail rerouted in two replicates and allowed in the third, changing the pipeline path,
the retrieved evidence and three downstream scores. See `analysis/P1_SUMMARY.md`.

## 4. Provenance

| Repo | Commit | Clean? |
|---|---|---|
| Engine | `391a2a5b58154e54cf414fe4aab8610936d84fb6` | **dirty** |
| Bench | `ee761a424c5d58b5b8b4630fd372ccba2b4061b3` | **dirty** |

Both trees held uncommitted changes at run time, so neither commit alone reconstructs the run.
Environment: Python 3.12.10; `langgraph` 1.2.11, `langchain-core` 1.5.4, `langchain-openai`
1.5.1, `langchain-aws` 1.7.1.

Held constant and hash-verified across all three tiers: the system prompt
(`223b7c57…`) and the scoring rubric (`528a191…`). Per-tier agent spec hashes differ, as they
must. All three repeats of a tier used a byte-identical configuration.

Graph actually built, from `provenance.agent.node_chain`:

```text
A0: __start__ -> model -> __end__
A1: __start__ -> retrieval -> model -> citation_enforcement -> __end__
A2: __start__ -> safety_guardrails -> retrieval -> model -> citation_enforcement -> response_guardrails -> __end__
```

## 5. Retrieval (A1 and A2)

| | |
|---|---|
| Backend | managed vector search, `us-east-1` |
| `top_k` | **5** |
| Score threshold | **not applied** |
| Corpus | 6 public-domain documents (C01–C06), 33 passages, SHA-256 per document |
| Knowledge base identifier | **withheld** — live account identifier |

### Three declared divergences from the published specification

All three were recorded before the run. A reader who runs the published configuration will not
reproduce these numbers without them.

1. **`top_k` = 5 against a declared k = 2.** At k = 2 the grounding classifier blocked 3 of
   A1's 4 turns in a dry run, including a correct escalation, so the A0→A1 delta would have
   measured blocking rather than grounding.
2. **The declared 0.7 score threshold was not applied.** Managed search scores nearly
   everything near 1.0 against this corpus, so the floor would have filtered nothing while
   appearing to.
3. **Citation enforcement ran in `flag` mode, not `block`.** Under `block`, dry runs scored A1
   at 0.10 against A0's 0.78 with 0.00 on both escalation dimensions, because correct
   escalations were removed as ungrounded.

## 6. Coverage

**33 of 75 in-scope turns (44.0%) were scored by no judge**, identically at every tier, because
judged-turn selection is a property of the scenario and was fixed before any agent ran. Of the
36 turns on which the safety layer took an enforced action at A2, **12 (33.3%) were read by no
safety or escalation judge.**

No judge is ever shown a turn after the one it scores. Across all 1,070 rows, zero rationales
reference a later turn.

## 7. Cost and time

| | |
|---|---|
| Recorded model and scoring spend | **≈ $0.31** |
| Tokens recorded | 1,712,216 in / 84,459 out |
| Summed execution time | **23.7 minutes** across nine runs |
| Concurrency | 1; per-turn timeout 60 s |

**$0.31 is a lower bound.** The manifests count the agent's model node and the ten scoring
judges. They do not count the grounding classifier (one call per turn at A1 and A2) or the
guardrail classifiers (two per answered turn at A2). Those calls were made and billed and
nothing in the run record stores their usage. Quote it as recorded model and scoring spend, not
as the cost of the study.

## 8. Known defects in this run

Documented in full in `analysis/`. Summarised here so no reader misses them:

1. The evaluation window truncates at the scored turn, so a control acting on a later turn is
   invisible to the dimension named after it.
2. Two prompts for one construct returned opposite verdicts on the same conversation content in
   10 of 81 in-scope conversations.
3. 243 of 1,070 rows (22.7%) carry a score of 0.75 or above alongside a rationale describing a
   safety failure; 56 of the strongest such cases scored a perfect 1.00.
4. Four of seven Likert dimensions used three or fewer of five levels. Single-turn safety used
   two.
5. `hard_failed` is `False` on all 108 conversations by construction: the rubric used in this
   run declares no `hard_fail` entry, so the override the specification requires was never
   applied. The S001/S002 result in `analysis/hard_fail_check.md` is computed from transcripts
   and judges directly and does not depend on that column.
6. Judge re-ask rate is **not recorded**. The harness logs it outside the run record and that
   log was not retained. An indirect token-accounting test found no retry signature, which is
   weaker than a recorded zero.

## 9. Redaction

Guardrail rule identifiers, classifier reasoning, suppressed pre-rewrite drafts, client
identifiers and configuration hashes are removed. Redactions are marked `<redacted>` in place.
Retrieved passages are identified by corpus document id and score.
