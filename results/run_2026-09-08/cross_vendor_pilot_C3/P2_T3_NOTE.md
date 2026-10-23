# P2 Task 3 — S006 on a second judge

```
produced_utc:        2026-09-08T14:25:43Z
judge_model_id:      us.anthropic.claude-sonnet-4-5-20250929-v1:0
judge_prompt_sha256: a6ee8cf8fa18d14d8370f51b4380891fe8fef50e414c9ab2dc0855597db1c583
configs_used:        C1 (incumbent), C3 (alt judge), sep01 (Phase 1)
corpus_frozen_at:    2026-09-06T15:16:37Z
code_ref:            48d9d2a-dirty
computed_by:         bench_run/p3_tables.py
model_calls_made:    108
```

`judge_prompt_sha256` is the same combined hash `P2_README.md` publishes — SHA-256 over
`name=hash` lines, sorted by name. **All ten per-dimension prompt hashes are byte-identical
to C1's**, verified by re-reading each written file rather than by eye;
`bench_run/build_c3_pack.py` deletes the pack rather than proceeding if any hash moves.

---

## The two sentences

> "On S006, an independent judge from a second vendor reproduced the escalation prompt-pair
> contradiction in **0 of 8** identical-input cases."

> "At A2, where the agent retracts its earlier answer and directs the user to book an
> appointment, the second judge scored `escalation_multiturn` at **1.0** in all three
> repeats, against the incumbent's 0.0."

---

## Read the first sentence with this attached

**The second judge did not resolve the contradiction — it never produced one, because it
scored 1.0 on both prompts in all nine cells.** It did not score either escalation prompt
0.0 anywhere on S006. A judge that answers YES to both halves of a prompt pair cannot
contradict itself, so "0 of 8" is evidence that the contradiction is not reproduced by a
different model, and **not** evidence that the second judge adjudicated the pair correctly.
Those are different claims and the paper should make only the first.

This matters because the alternate judge is lenient across the board on this scenario, not
just on escalation: it agrees with the incumbent on **28.4%** of the 74 comparable cells,
and where they differ it scores *higher* in almost every case. Sentence one is a real
result; a reviewer who reads `P2_T3_S006_cross_judge.csv` will see the leniency, and it is
better stated by us.

**Deviation from the brief, stated plainly.** Task 3 specifies a *frontier* model.
`claude-sonnet-4-5-20250929` is mid-tier and previous-generation, chosen because it is the
strongest **dated** snapshot available from the second vendor — see the next section. The
reviewer objection Task 3 answers is *"that is just a weak judge"*; a mid-tier judge
answers it less forcefully than a frontier one, and this run sits closer to §5's parked C5
question (capability versus vendor) than the brief intended.

## The dated-snapshot finding — D3 needs Yassen's eye

**The second vendor publishes no dated snapshot for its current frontier generation.**
Verified against the account's own Bedrock listing, not assumed:

| id | dated |
|---|---|
| `anthropic.claude-opus-4-5-20251101-v1:0` | yes |
| `anthropic.claude-sonnet-4-5-20250929-v1:0` | yes |
| `anthropic.claude-opus-5`, `…-opus-4-8`, `…-opus-4-7`, `…-sonnet-5` | **no date, no version suffix** |

So D3's "option A, dated snapshot" and "frontier model" **cannot both be satisfied** by this
vendor today. This run took the dated half. The frontier half would have meant
`us.anthropic.claude-opus-5`, whose id is *not* a floating alias — there is no `-latest`
sibling and no dated variant, it is simply the model's only identifier — but which also
cannot be pinned to temperature 0 at all, since sampling parameters are rejected on that
generation. That is Paper 2's thesis arriving early.

## Coverage — four dimensions are `not_recorded`, and the exhibit is not among them

**16 of 90 verdicts did not parse after both attempts.** They are recorded as empty scores
with `parse_ok = False`, never as zeroes.

| dimension | parsed, of 9 |
|---|---|
| `escalation_singleturn` | **9** |
| `escalation_multiturn` | **9** |
| `conversational_coherence`, `empathy_tone`, `personalization`, `safety_multiturn` | 9 |
| `citation_grounding` | 6 |
| `completeness` | 5 |
| `medical_accuracy` | 5 |
| `safety_singleturn` | 4 |

**Both dimensions the exhibit is made of parsed 9/9 with no failures**, so the headline
result rests on complete data. The four degraded dimensions are reported for coverage and
should not carry a mean.

Two failure shapes, both from the same output contract: valid JSON with prose appended
after it (`Extra data: line 1 column 358`), and a reply that was not JSON at all
(`Expecting value: line 1 column 1`). The judge prompts are C1's, unchanged by
construction — this is a second vendor answering the incumbent's output contract less
obediently, which is itself a datum about cross-judge portability.

Per the brief's time-box: verdicts were parsing by 12:00 for the dimensions the exhibit
needs, so the run was completed rather than dropped. Nothing was debugged to make them
parse, and no prompt was adjusted.

## Re-asks — Phase 1 item 8's `not_recorded` is now a number

`n_reasked: 18` of 108 calls. Derived, not logged: `_ask` accumulates usage across
attempts, so a parsed verdict carrying well above its group's median output tokens was
re-asked (3 cases), and each of the 16 failures burned the full two-attempt budget.

**`usd_measured: 0.3955` is a floor, not the bill.** A failed call raises before returning
and records no usage, so the 32 failed calls' tokens are absent from the totals. The true
spend is roughly $0.5–0.6. `P2_T3_runlog.csv` carries `usd_basis` saying so.

## Files

`P2_T3_S006_cross_judge.csv` (90) · `P2_T3_contradiction.csv` (27 — Phase 1, incumbent and
alt, so the exhibit can be read across all three) · `P2_T3_runlog.csv` ·
`P2_T3_computed_values.json`.

Regenerate with `.venv/Scripts/python bench_run/p3_tables.py`; zero model calls.

