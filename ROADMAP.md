# Roadmap

SAFE-CARE Bench is an active work in progress. This file states honestly what exists, what is
coming, and what is deliberately out of scope.

## Available now — v0.4

- [x] **Worked example.** The two reference runs reported in the accompanying paper, tiers A0–A2,
      each with its run card, in `results/`, so the delta method is demonstrated rather than described
- [x] **Evaluations on request.** The reference runner stays internal and drives hosted
      evaluations; the configurations here stay implementation-neutral

## Available since v0.1.1

- [x] A0–A4 tier definitions with explicit 10-flag capability vectors, implementation-neutral
- [x] `delta_from_previous` block on every tier naming exactly which flags the rung enables
- [x] Ten LLM-judge prompts with strict JSON output contracts, including separate single-turn and
      multi-turn safety and escalation judges
- [x] Full scoring anchors for 7 Likert and 3 binary dimensions (safety and escalation each scored
      single-turn and multi-turn)
- [x] Machine-readable scenario schema with declared `hidden_ground_truth`
- [x] Twelve multi-turn scenarios covering gradual risk emergence, stale memory, medication
      boundaries, prompt injection, overreliance, and over-escalation controls
- [x] Escalation judges scored against declared ground truth rather than judge opinion
- [x] Reproducible dataset build pipeline with checksums and a manifest
- [x] Dataset card with true logical record counts, provenance, and prohibited uses
- [x] Synthetic persona schema and six seed personas, each designed to separate specific tiers
- [x] Hard-fail override rule on missed escalation
- [x] Zenodo DOI and versioned archival release
- [x] Public-domain reference retrieval corpus with per-document provenance, declared
      fidelity, scenario coverage map, and checksummed manifest (`corpus/`)

## Next

- [ ] **Judge calibration set.** A human-scored subset with reported judge–human agreement. A
      12-clinician calibration study is under way, with results to follow the paper. Until it
      reports, all judge output is uncalibrated.
- [ ] **MedMCQA rebuild.** Regenerate from the train split via `datasets/build.py`, complete manual
      review, and restore the file from quarantine. See [`datasets/DATASET_CARD.md`](datasets/DATASET_CARD.md).
- [ ] **Manual dataset review.** Adjudicate rows admitted as `context_term_with_support` and record
      outcomes in the `_manual_review` column.
- [ ] **Persona expansion** to the 20-persona target described in the generation guide.
- [ ] **Transcript schema** and score-aggregation reference implementation.

## Later

- [ ] Decompose the capability bundles into single-flag rungs, so that A1, A3, and A4 deltas become
      one-variable ablations rather than bundle effects
- [ ] Inter-rater reliability across multiple judge models, to test how far results depend on judge
      choice
- [ ] Clinician-reviewed gold answers for the filtered question sets
- [ ] Expansion beyond menopause to a second clinical domain — GLP-1 and metabolic care is the
      intended next domain — testing whether the tier ladder generalizes
- [ ] Cost and latency instrumentation per tier: the safety gain of a layer is only actionable
      alongside what it costs
- [ ] Semantic or embedding-based dataset filtering as a complement to the keyword gate
- [ ] A public reference runner, if researchers need one to reproduce results independently

## Out of scope

- Clinical efficacy evaluation. That requires prospective study design, not a benchmark.
- Certification or accreditation of any system as safe to deploy.
- Any production implementation detail. See [`NOTICE.md`](NOTICE.md).

## Known limitations

These are stated openly because a benchmark that hides its limitations is worse than no benchmark.

1. **Only A0–A2 run records are published** ([`results/`](results/)), as one worked example, and
   their headline finding is negative. They demonstrate the delta method on twelve scenarios under
   the conditions in each run card. Nothing in this repository demonstrates that any architectural
   layer improves safety.
2. **The reference runner is not published.** Evaluations are run on request on the internal
   harness. Two teams implementing these declarations against different runtimes may produce
   materially different agents. Treat the configurations as an implementation-neutral
   specification, not a turnkey benchmark.
3. **The judge is uncalibrated.** No judge–human agreement and no clinician inter-rater reliability
   have been measured; the 12-clinician calibration study has not yet reported. Scores, including
   the worked example's, are indicative and must not be reported as validated measurement.
4. **Adjacent tiers differ by capability bundles, not single flags.** Only A1→A2 is a one-variable
   delta. Do not attribute a bundle effect to any single member.
5. **Single clinical domain.** All current scenarios are menopause and perimenopause. Generalization
   is untested.
6. **Synthetic personas only.** They are constructed to be realistic, but they are not real users
   and do not capture the full distribution of real conversational behaviour.
7. **Gold answers are derived from source datasets**, not independently clinician-reviewed. The
   MENST-derived answers were model-generated at source and share 141 distinct answers across 1,816
   questions — they support consistency scoring, not clinical ground truth.
8. **Scenario and persona coverage is finite.** Twelve scenarios and six personas. Passing here does
   not mean an agent is safe; it means it did not fail these cases.
9. **`datasets/raw/` is not published.** The unfiltered upstream MENST dump is a near-complete copy
   of another publisher's dataset; redistributing it is their call, not ours. Only domain-filtered
   derivatives ship here.

## Contributing

The most valuable contributions right now are judge calibration data, additional red-flag and
over-escalation scenarios, and persona expansion. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
