# Results

Published evaluation runs of SAFE-CARE Bench.

Until this directory existed, the repository shipped an instrument and no measurements. The
README said so explicitly. That is no longer true, and the claims below replace it.

## What is here

| Run | Kind | Tiers | Scenarios | Conversations | Date |
|---|---|---|---|---|---|
| [`run_2026-09-01`](run_2026-09-01/) | generation and scoring | A0, A1, A2 | 12 (9 in headline scope) | 108 | 1 September 2026 |
| [`run_2026-09-08`](run_2026-09-08/) | re-scoring only | A0, A1, A2 | 12 (9 in headline scope) | 108, not regenerated | 8 September 2026 |

Each run directory contains a `RUN_CARD.md` recording exactly what produced it.

**The two directories answer different questions and are not interchangeable.**
`run_2026-09-01` generated the conversations and scored them once; it holds the full
per-row scores, every transcript, and the analyses derived from them.
`run_2026-09-08` generated nothing. It re-scores those same transcripts under altered
evaluator conditions — a pinned judge snapshot, a repeat pass, a widened context scope, and
a second-vendor pilot — and reports what moved. Read `run_2026-09-08/PAPER_MAP.md` for
which artifact backs which published claim.

## What these results are

A capability-incremental ablation. The generation model, the system prompt and the scoring
rubric were held byte-identical across tiers and verified by hash. The declared capability set
is the only variable. The A1-to-A2 step changes exactly one capability flag and is the only
step in the ladder that supports attributing a change to a named control.

## What these results are not

- **Not a model comparison.** One model, held constant. Nothing here says which model to use.
- **Not clinical validation.** Technical performance inside a tested scenario boundary, level
  M1 on the SAFE-CARE evidence maturity model. Clinical claims require prospective evaluation.
- **Not produced by a calibrated judge.** Judging used the same model family as generation,
  and no judge–human agreement has been measured. Treat every dimension score as indicative.
- **Not a variance decomposition of the agent.** `run_2026-09-08` separates judge-only
  instability (5.9% of cells) from combined agent-and-judge instability (15.9%). It does not
  establish why the agent varies.
- **Not exactly reproducible.** The model was reached through a floating alias with no
  response fingerprint recorded, and both repositories were dirty at run time. See the run
  card.
- **Not a safety certificate.** A tier that scores well here is not safe for deployment.

## The headline finding is negative

Adding the single safety-guardrail flag **degraded medical accuracy** by 0.157 across six of
nine scenarios, every one downward, while the safety improvement it produced did not clear its
own noise. Four defects in the measurement apparatus itself are documented in
[`analysis/`](run_2026-09-01/analysis/), including that 44% of turns were scored by no judge
and a third of enforced safety actions were read by no safety judge.

We publish the defects alongside the results because a reader cannot assess one without the
other.

The 8 September re-scoring sharpens two of them. The repeat-instability figure decomposes:
of the 15.9% cell disagreement across replicates, judge-only disagreement is 5.9%, so most
replicate variance is the agent answering differently rather than the instrument scoring
differently. And widening the judge's context — the obvious fix for a truncated evaluation
window — produced no effect above floor on seven of ten dimensions, because the defect is
which turn a dimension scores, not how much of the conversation it is shown.

## Redaction

Guardrail rule identifiers, classifier reasoning, suppressed pre-rewrite drafts, client
identifiers and configuration hashes are removed from this release. Guardrail behaviour is
reported only as an action: `flagged`, `rerouted`, `rewrote`, `allowed` or `none`. Redactions
are marked in place as `<redacted>`; nothing was silently dropped.

## Reproducing

Follow the reproduction steps in the repository README, then compare against
`scores/per_row_scores.csv`. You will not reproduce these numbers exactly, for the reasons in
the run card. The analyses in `analysis/` are computed from the score file and the transcripts
alone and can be re-derived from them.
