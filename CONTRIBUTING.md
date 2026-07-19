# Contributing to SAFE-CARE Bench

Thank you for considering a contribution. This benchmark improves most through adversarial use: people trying to break it, finding cases it misses, and testing whether its results hold on other models.

## Most valuable contributions

1. **Judge calibration data** — human scores on transcripts, so judge–human agreement can be reported. This is the single biggest gap.
2. **Red-flag scenarios** — cases where a health agent must escalate, especially ones that build across turns rather than announcing themselves in a single message.
3. **Replications** — running the ablation on a different model family and reporting per-tier deltas.
4. **Domain adaptation** — applying the A0–A4 ladder to another clinical area and reporting whether it holds.
5. **Scoring anchor critique** — if an anchor is ambiguous, or two reasonable judges would score the same response differently, say so.

## Ground rules

**Synthetic data only.** Never submit real patient data, real conversation logs, screenshots of a live product, or anything containing protected health information. Contributions containing real user data will be rejected and the content purged.

**No production implementation detail.** Do not submit component names, schemas, endpoints, credentials, or configuration from any deployed system — yours or anyone else's. See [`NOTICE.md`](NOTICE.md).

**Clinical claims need sources.** If a scenario asserts something clinically, cite where it comes from. "The model should say X" is not sufficient without grounding.

## How to contribute

1. Open an issue describing what you intend to add, before doing large work. It saves both of us effort.
2. Fork, branch, and open a pull request against `main`.
3. Keep pull requests focused — one scenario set, or one judge prompt revision, not both.
4. Explain the *reasoning*, not only the change. For a scenario: what failure mode does it catch, and why would an agent plausibly fail it?

## Scenario submission format

Each scenario needs:

- The conversation turns, in order
- The hidden ground truth — what the correct behavior is
- The hard-fail condition, if any — what makes this an automatic failure
- The failure mode it targets, mapped to the SAFE-CARE risk taxonomy
- A source for any clinical assertion

## Reporting safety or disclosure concerns

Do not open a public issue. See [`SECURITY.md`](SECURITY.md).

## Licensing of contributions

By contributing you agree that your contributions are licensed under the same terms as the repository: CC BY 4.0 for documentation and methodology, Apache-2.0 for configurations, prompts, and machine-readable artifacts.

## Code of conduct

Be direct and be civil. Critique the work, not the person. Disagreement about method is the point of the project.
