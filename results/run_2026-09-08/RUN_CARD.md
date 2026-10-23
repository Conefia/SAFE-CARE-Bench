# Run card — `run_2026-09-08`

**This is a re-scoring study, not a new generation run.**

No conversations were generated here. Every figure in this directory is computed over the
108 transcripts produced by [`run_2026-09-01`](../run_2026-09-01/), re-scored under altered
evaluator conditions. The agent, the system prompt, the corpus and the rubric are those of
the 1 September run and were not varied.

`run_2026-09-01` answers *what did the agent do*. This directory answers *what does the
instrument see, and what changes when the instrument changes*.

## Provenance

Reproduced verbatim from the delivery header. Unknown values are written `not_recorded`
rather than omitted.

```
produced_utc:        2026-09-07T21:32:04Z
judge_model_id:      gpt-4o-mini-2024-07-18
judge_prompt_sha256: 012099c0e47cf251cdae48c0529f1d3e1209f40c9eedf19eb763d71e071ecfb0
configs_used:        C1, C1', C2 (and the 1 September run, as sep01)
corpus_frozen_at:    2026-09-06T15:16:37Z
code_ref:            48d9d2a-dirty
computed_by:         bench_run/p2_tables.py
model_calls_made:    0
```

The cross-vendor pilot in [`cross_vendor_pilot_C3/`](cross_vendor_pilot_C3/) was produced
separately, later on 8 September, and is the only part of this directory that made model
calls: 108, of which 74 parsed. Its own provenance is in `P2_T3_runlog.csv`.

The directory is dated **8 September 2026**, the date the phase was delivered complete.
Component timestamps differ and are recorded above and in each note.

### Judge prompt hashes

`judge_prompt_sha256` is one value over ten per-dimension prompts: SHA-256 of `name=hash`
lines, sorted by name. The ten are listed so the combined value can be rebuilt rather than
trusted.

| dimension | judge prompt sha256 |
|---|---|
| `citation_grounding` | `a5a73dad31332bc303ee4669c56b47504ea547316d70286f2e3f8bbdda2d30d6` |
| `completeness` | `ad6d4035a45688e61c2fb3c6e704e2b48c16c6a5749c8cd4e8a45bd94a355e72` |
| `conversational_coherence` | `d888dbf5d6cb0eed9bd97239cc9c57c5c3c06ba116d9db8392ae909c21ddb54a` |
| `empathy_tone` | `35751b81490bde9e53825f37faa9808d8d8b10d8679228fcfbbc72e1327fce4c` |
| `escalation_multiturn` | `357120f40ec93d5575a0d32cf394bd94957f908ed144c83e80c586882bdbe267` |
| `escalation_singleturn` | `0200e6c31995fcc2c91b1a327b09a8307c97dbc3e29fd57115f3238b61c8a920` |
| `medical_accuracy` | `b119508fdc7f6fe49eb306291828e4cf05a98a77c8d64af92d992c827a053fb0` |
| `personalization` | `1f23b24549dc365fdda943a9dfdf981147b1a6cd2e8670361c7088ed6e0564c1` |
| `safety_multiturn` | `6f5b56ddcb5b644208c035c66dbc26d4586b5f3d3301ede6ed689e1c15b6ba92` |
| `safety_singleturn` | `dd537f62a9e67c37b5e9b4da3a0c00dd4404a2f787e83f34e17a82ebde1c9bac` |

## The configurations

| Config | Judge | Corpus | What it varies | Where it appears |
|---|---|---|---|---|
| `sep01` | floating alias `gpt-4o-mini` | 108 conversations | reference point — the 1 September run | carried figures |
| **C1** | dated snapshot | 108 conversations | declared configuration, re-scored on a pinned snapshot | Results, Appendix B |
| **C1'** | dated snapshot | 108 conversations | repeat of C1 — isolates judge-only variance | the floor |
| **C2** | dated snapshot | 108 conversations | widened context scope for conversation-scoped dimensions | §4.3 null |
| **C3** | second vendor | S006 only | different judge vendor | Appendix G, as a pilot |

C1, C1' and C2 all scored through the dated snapshot `gpt-4o-mini-2024-07-18`. `sep01`
scored through the floating alias. That difference is why pinning can be ruled out as the
explanation for the instability figure rather than merely left unsupported.

## Why C3 is in its own directory

The paper reports the cross-vendor comparison as a pilot and draws no conclusion from it.
It covers one scenario, agreement is 28.4% on 74 comparable cells, and 16 of 90 verdicts
failed to parse against byte-identical prompts. Keeping it beside the full-corpus
configurations would invite it to be read as a robustness check on them. It is not one.

## Reproducibility status

**Closed for this directory, open for the run it scores.** C1/C1'/C2 ran on a dated
snapshot with hashed prompts, a frozen corpus, a code ref and a recorded call count. The
generating run they score did not: it used a floating alias with no response fingerprint,
so those conversations cannot be regenerated exactly. The re-scoring stage is pinned; the
generating stage is not.

## Known limitations introduced by this directory

1. The C1' floor is **one replicate per cell**. "Stable under C1'" is weak evidence for any
   individual cell. Only `escalation_multiturn`, whose floor is 27/27, supports a per-cell
   claim.
2. The cross-vendor run has **16 of 90 unparsed verdicts**; four dimensions cannot carry a
   mean.
3. `usd_measured` in the cross-vendor runlog is a **floor, not the bill** — failed calls
   record no usage.

## Redaction status

**NOT ip-scanned.** This directory has been checked by string search for guardrail rule
identifiers, classifier reasoning, suppressed pre-rewrite drafts, client identifiers,
credentials and storage URLs, and none were found. That is necessary and not sufficient.
`ip-scan` must run against this directory before it is committed. See
[`../RELEASE_CHECKLIST.md`](../RELEASE_CHECKLIST.md).
