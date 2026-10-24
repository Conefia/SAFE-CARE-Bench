# Human label card: Label Set A

**Version 0.1 · 2 September 2026**

Blinded clinician labels, from a paid clinical contributor, for the twelve SAFE-CARE Bench scenarios. This is the
first human review of the benchmark's own reference standard. It is not a calibration set and
must not be described as one.

---

## What this is

One board-certified family physician, licensed in the United States, labeled all twelve
scenarios without access to `hidden_ground_truth`, scenario titles, `risk_level`, `stresses`,
`min_tier_expected_to_pass`, or any expected-behaviour field. The rater saw the patient profile
and the user turns only, presented in a fixed shuffled order that does not follow scenario id.

The rater was engaged under a paid agreement and was blinded on an honour basis. The scenario
files in this repository are public and carry their ground truth, so blinding could not be
enforced technically. This is stated as a limitation rather than claimed as a control.

## What it is not

- **Not a calibration set.** n = 1 rater and 12 scenarios. No inter-rater reliability can be
  computed from a single rater.
- **Not a validation of the judge.** These labels are compared against the declared ground
  truth, not against judge output.
- **Not a gold standard that supersedes `hidden_ground_truth`.** Where the two disagree, both
  are published and the disagreement is the finding.

## Files

| File | Contents |
|---|---|
| `label_set_a_rater_r01.csv` | One row per scenario. Rater labels, declared ground truth, and per-row agreement flags |
| `manifest.json` | Checksums and provenance |

## Schema

| Column | Values | Meaning |
|---|---|---|
| `scenario_id` | S001–S012 | Scenario identifier |
| `rater_id` | R01 | Anonymised rater |
| `presentation_order` | 1–12 | Position in the blinded packet. Included so order effects can be checked |
| `escalation_warranted` | yes / no | Rater: should this be escalated to a clinician |
| `expected_urgency` | none / routine / prompt / emergency | Rater urgency, plain-English anchors given in the packet |
| `earliest_escalation_turn` | integer or empty | Rater: earliest patient message at which a clinician should have been involved |
| `red_flag` | yes / no | Rater: clinical red flag present |
| `decline_and_route` | yes / no | Rater: should the assistant decline and route to a person |
| `rater_rationale` | free text | One line, the rater's own words |
| `gt_*` | | The corresponding declared values from `hidden_ground_truth` |
| `agreement_escalation`, `agreement_red_flag` | true / false | Convenience flags, derivable from the columns above |

## Agreement against declared ground truth

| Dimension | Exact agreement |
|---|---|
| Red flag | 12 / 12 |
| Urgency, exact | 7 / 12 |
| Urgency, within one step | 12 / 12 |
| Escalation warranted | 7 / 12 |
| Earliest escalation turn | 7 / 12 |
| Decline and route | 5 / 12 |

Quadratic weighted kappa on urgency is 0.762. No urgency disagreement exceeded one step. Both
red-flag scenarios, S001 and S002, were identified with the exact expected escalation turn.

Cohen's kappa is unstable at this n with near-balanced marginals and is not reported for the
binary dimensions.

## What the disagreements showed

**The escalation field merges two constructs.** `escalation_expected` currently answers both
*does this patient need a clinician, and how fast* and *should the agent decline and hand off*.
Those are different questions and a clinician answers only the first.

Every disagreement falls into one of two directions.

**The rater escalated where the declared label did not**, on S003, S008 and S009. In all three
she recorded red flag `no` and urgency `routine`, agreeing that nothing was dangerous or fast,
while holding that a symptomatic untreated patient should be connected to a clinician about
starting treatment. The schema has no state for clinician involvement warranted but not urgent.

**The rater did not escalate where the declared label did**, on S006 and S012. Both are
agent-scope tests with no clinical urgency. The declared label marks them escalation-expected
because the agent should decline, not because the patient needs care.

**`decline_and_route` collected no independent information.** The rater's answers to it were
identical to her escalation answers on all twelve scenarios, while the declared ground truth
treats the two as distinct on four. As worded, the question does not separate the constructs for
a clinician.

## Consequences for the schema

Planned for the next schema revision, recorded here so the change is traceable:

1. Split `escalation_expected` into a clinical dimension and an agent-handoff dimension.
2. Add a state for clinician involvement warranted without urgency.
3. Rewrite the handoff question so it cannot collapse into the clinical one.
4. Route agent-scope scenarios, currently S005, S006 and S012, to agent-policy review rather
   than clinician labeling.

## Limitations

- One rater, twelve scenarios, one clinical domain.
- Blinding was honour-based against a public repository.
- The rater is a family physician, not a menopause subspecialist.
- The instrument merged two constructs in the field with the most disagreement, so the
  escalation agreement figure measures instrument design as much as clinical judgment.
- Rater identity is withheld pending consent. Attribution may be added in a later release.

## Licence

Released under the repository's documentation licence, CC BY 4.0. See
`LICENSE-DOCUMENTATION-CC-BY-4.0.txt`.
