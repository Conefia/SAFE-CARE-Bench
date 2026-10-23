# P2 Task 1 — reconciling the two instability numbers

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

**Answer: branch (a).** C1 comes back at **15.9 %**, not 4 %. Pinning did not do it.

**The recomputation is calibrated, which is what licenses it.** Phase 1's extractor was
never committed, so "same code path" was not literally available. Instead the new code was
run on the sep01 data first: it returns **44/270 = 16.3 %** and every tier figure —
A0 11.1 %, A1 24.4 %, A2 13.3 % — matching Phase 1 to the decimal. M1, M3 and M5 all
reproduce their carried values exactly. The definition is therefore the same one.

**Pinning is independently ruled out, not merely unsupported.** sep01 scored through the
floating alias `gpt-4o-mini`; C1, C1' and C2 all scored through the dated snapshot
`gpt-4o-mini-2024-07-18`. Cell-level instability across those three pinned configs is
15.9 %, 14.8 % and 15.6 %. Pinning the snapshot moved this statistic by less than half a
point. D3 stands, but for its own reasons — not because it bought stability.

**A1 is still the noisiest rung**, at 23.3 % against 24.4 %. That ordering survives.

### The reconciliation is not only unit of analysis — please read this before writing it up

Your template sentence says the two Phase 2 figures "differ from Phase 1 only in unit of
analysis". They differ in **two** respects, and the second is the larger one.

A *repeat* in Phase 1 is not a judge redraw. `source_map.json` resolves R1/R2/R3 to
`seed1`, `seed2` and `seed3` — **three different agent conversations**. So the 16.3 %
counts the agent answering differently *and* the judge scoring differently. C1 versus C1'
re-scores the identical nine transcripts, so it isolates the judge alone.

M4 is what separates them. All three figures below are on the same 270 cells:

| | variance source | cell disagreement |
|---|---|---|
| M2 — within C1, across 3 repeats | agent **and** judge | **15.9 %** |
| M4 — C1 vs C1', cell level | judge only | **5.9 %** |
| M3 — C1 vs C1', row level | judge only | 2.8 % |

Roughly two thirds of Phase 1's 16.3 % is the agent, not the instrument. That matters for
the paper's claim: 16.3 % read as "the judge disagrees with itself six times in forty" is
an overstatement of instrument noise by about a factor of three.

### The sentence, completed — with the one word I cannot sign

> Recomputed on the C1 data on the identical 270-cell denominator, cell-level instability
> is **15.9 %**, against 16.3 % on 1 September. The two Phase 2 figures differ from Phase 1
> only in unit of analysis; reported together, the row-level figure is **97.2 %** and the
> cell-level figure is **94.1 %**.

The numbers are right and the word **"only"** is not. Suggested replacement for that clause:

> The two Phase 2 figures differ from Phase 1 in unit of analysis **and in variance
> source** — Phase 1's repeats are three separate agent conversations, where C1 versus C1'
> re-scores identical transcripts. Reported together, the row-level figure is **97.2 %**,
> the cell-level figure is **94.1 %**, and the like-for-like cell-level comparison against
> Phase 1's within-run statistic is **15.9 % against 16.3 %**.

### Files

`P2_T1_agreement_matrix.csv` — M1–M5. `status` marks M1/M3/M5 `carried_from_phase1`
as specified; all three were also recomputed here and matched.
`P2_T1_instability_by_tier.csv` — sep01 and C1 as asked, plus C1' and C2, which are what
rule out the reading that C1 happened to be a quiet run.

