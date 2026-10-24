# Paper map — which artifact backs which claim

Maps every figure this directory supplies to the place it is used in the ML4H 2026
Proceedings submission, *Blind by Construction: Four Instrument Defects in a Controlled
Healthcare Agent Ablation*, submitted 11 September 2026.

Phase 1 figures are backed by [`../run_2026-09-01/analysis/`](../run_2026-09-01/analysis/)
and are not repeated here.

## Results

| Paper location | Claim | Backing artifact |
|---|---|---|
| §4.2 | Repeat instability was 16.3% in the original run and 15.9% on the re-scored run | `rescoring_C1_C1prime_C2/P2_T1_agreement_matrix.csv` (M1, M2) |
| §4.2 | Judge-only repeat instability is 5.9% of cells and 2.8% of rows | same file (M4, M3) |
| §4.2 | Instability is uneven across the ladder — A0 11.1%, A1 24.4%, A2 13.3% — and the ordering reproduces across all four full-corpus scoring configurations | `rescoring_C1_C1prime_C2/P2_T1_instability_by_tier.csv` |
| §4.3 | Widening context gives 3.2% of rows against the 2.8% floor, and on seven of ten dimensions no effect distinguishable from that dimension's own floor | `rescoring_C1_C1prime_C2/P2_T2_window_result.csv` |
| §4.3 | Multi-turn escalation scores turn 1; the S006 A2 agent's retraction and appointment instruction occur in turn 2 | `rescoring_C1_C1prime_C2/P2_T2_headline_cell.csv` (verbatim rationales, 3 tiers x 2 configs x 3 repeats) |
| §4.4 | Eight of nine care-substitution cells returned opposite verdicts in the original run and eight again under re-scoring; seven disagreed in both passes, one resolved, one newly disagreed | `cross_vendor_pilot_C3/P2_T3_contradiction.csv` |
| §4.4 | Multi-turn escalation varied in 0 of 27 cells across replicates; its prompt-pair partner varied in three | `rescoring_C1_C1prime_C2/P2_T2_window_result.csv`, `P2_T1_agreement_matrix.csv` |
| §4.4 | Single-turn escalation agrees with its own repeat on 97.5% of rows yet returns kappa = 0.654, bootstrap 95% CI −0.017 to 1.000 | `rescoring_C1_C1prime_C2/P2_T2_kappa.csv` |
| §4.6 | Single-turn safety used two levels across all 107 conversations and returns kappa = 1.000 against its own repeat | `rescoring_C1_C1prime_C2/P2_T2_kappa.csv` (`declared_type` vs `levels_used`) |

## Discussion and Limitations

| Paper location | Claim | Backing artifact |
|---|---|---|
| §5 | High repeat agreement does not establish judge validity — the kappa interval still includes chance because the marginals are near-degenerate | `rescoring_C1_C1prime_C2/P2_T2_kappa.csv` |
| §6 | The re-scoring passes ran on a dated snapshot with hashed prompts and a frozen corpus, so the re-scoring stage is pinned even though the generating run is not | `RUN_CARD.md` provenance block |
| §6 | The judge-only floor rests on one replicate | `RUN_CARD.md` limitation 1 |

## Appendices

| Paper location | Claim | Backing artifact |
|---|---|---|
| App. B — Re-scoring provenance, agreement and replicate stability | The full M1–M5 agreement matrix and the provenance header | `rescoring_C1_C1prime_C2/P2_T1_agreement_matrix.csv`, `RUN_CARD.md` |
| App. G — A cross-vendor pilot, reported as a pilot | The vendor exposed no dated snapshot of its then-current frontier generation, so a pinned arm and a frontier arm were not simultaneously available | `cross_vendor_pilot_C3/P2_T3_runlog.csv` (`model_id_dated`, `temperature_supported`) |
| App. G | Cross-judge scores with both rationales side by side | `cross_vendor_pilot_C3/P2_T3_S006_cross_judge.csv` |

## Scenario-level means

`rescoring_C1_C1prime_C2/P2_T2_scenario_level.csv` carries a `distribution_warning` column
flagging the dimensions whose scenario means are degenerate, where a normal interval would
be unfair. The paper's descriptive intervals are reported with that caveat.

## Cost

`rescoring_C1_C1prime_C2/P2_T2_cost.csv` carries a `judges_counted` column so a total is
never implied to be complete. USD is measured tokens at published list price. Agent turns
were generated once on 1 September and are identical across configs; they are not re-spent
per config.

## Not used in the paper

The cross-vendor pilot's central commissioned claim does not appear as a result. The second
judge scored 1.0 on both escalation prompts in all nine cells and never scored either
prompt 0.0 on S006, so it cannot contradict itself and a "0 of 8" figure would be close to
vacuous. The pilot is reported in Appendix G for the pinning obstacle and the parse-failure
rate, not as a rebuttal to any objection about judge quality.
