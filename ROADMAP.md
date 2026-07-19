# Roadmap

SAFE-CARE Bench is an active work in progress. This file states honestly what exists, what is coming, and what is deliberately out of scope.

## Available now — v0.1

- [x] A0–A4 ablation tier definitions, implementation-neutral
- [x] Ten LLM-judge prompts, including separate single-turn and multi-turn safety and escalation judges
- [x] Full scoring anchors for 6 Likert and 2 binary dimensions
- [x] Dataset filtering method and rationale
- [x] Synthetic persona generation methodology and schema
- [x] Domain-filtered question sets derived from MedQA, MedMCQA, and MENST
- [x] Hard-fail override rule on missed escalation

## Next — v0.2

- [ ] **Reference runner.** A minimal, provider-agnostic harness that executes the five tiers and collects transcripts. Currently implementation-specific; being generalized.
- [ ] **Worked example.** One complete run with published per-tier results, so the delta method is demonstrated rather than described.
- [ ] **Judge calibration set.** A human-scored subset with reported judge–human agreement. Until this exists, treat all judge output as uncalibrated.
- [ ] **Zenodo DOI** and versioned release.

## Later

- [ ] Inter-rater reliability across multiple judge models, to test how far results depend on judge choice
- [ ] Adversarial and prompt-injection scenario set
- [ ] Expansion beyond menopause to a second clinical domain, testing whether the tier ladder generalizes
- [ ] Cost and latency instrumentation per tier — the safety gain of a layer is only actionable alongside what it costs
- [ ] Clinician-reviewed gold answers for the filtered question sets

## Out of scope

- Clinical efficacy evaluation. That requires prospective study design, not a benchmark.
- Certification or accreditation of any system as safe to deploy.
- Any production implementation detail. See [`NOTICE.md`](NOTICE.md).

## Known limitations

These are stated openly because a benchmark that hides its limitations is worse than no benchmark.

1. **The judge is uncalibrated.** Until the calibration set ships, scores are indicative and should not be reported as validated measurement.
2. **Single clinical domain.** All current scenarios are menopause and perimenopause. Generalization to other domains is untested.
3. **Synthetic personas only.** They are constructed to be realistic, but they are not real users and do not capture the full distribution of real conversational behavior.
4. **Gold answers are derived from source datasets**, not independently clinician-reviewed for this benchmark. The MENST-derived answers were LLM-generated at source (see the `LLM Used` column) — they support consistency scoring, not clinical ground truth.
6. **The persona seed set is two rows.** Enough to make the schema concrete; not enough to characterize a population. Expanding it is the highest-value near-term contribution.
7. **`datasets/raw/` is not published.** The unfiltered upstream MENST dump is a near-complete copy of another publisher's dataset; redistributing it is their call, not ours. Only domain-filtered derivatives ship here.
5. **Scenario coverage is finite.** Passing here does not mean an agent is safe. It means it did not fail these cases.

## Contributing

The most valuable contributions right now are judge calibration data and additional red-flag scenarios. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
