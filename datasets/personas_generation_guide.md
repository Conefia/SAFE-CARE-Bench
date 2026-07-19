# Persona Generation Guide

Canonical reference for constructing synthetic evaluation personas for SAFE-CARE Bench.

A persona row in `personas.csv` represents a **complete synthetic user**. The simulator uses the
row twice: once to pre-populate whatever state the agent under test reads at run time, and again
to generate in-character user messages during the conversation.

> **Implementation-neutral by design.** This guide specifies a *benchmark-side* persona schema. It
> deliberately does not describe the storage model, table names, field names, or inference rules of
> any production system. Map these fields onto your own runtime with a private adapter. Two teams
> using different storage models should both be able to run this benchmark unchanged.

**Every persona is synthetic.** No real patient data, no production conversation logs, and no
protected health information appears in this repository or its history.

---

## 1. Schema

Fields are grouped into blocks. Only Block A is required; every other block is optional and a blank
value means "not set" — the simulator will not pre-populate that state.

### Block A — Simulator identity (required)

| Column | Type | Description |
|---|---|---|
| `persona_id` | string | Stable unique ID, e.g. `P01`. Never change once committed. |
| `name` | string | First name only. |
| `personality` | enum | `anxious` / `curious` / `skeptical` / `open` |
| `opening_topic` | string | First thing the user raises. Blank = simulator selects from symptoms. |

### Block B — Profile

| Column | Type | Description |
|---|---|---|
| `profile.date_of_birth` | `YYYY-MM-DD` | Age is derived from this rather than stored directly. |
| `profile.life_stage` | enum | `perimenopause` / `menopause` / `postmenopause`. **Set this only when you want to bypass profiling** and start the conversation from a known stage. Leave blank to exercise the profiling flow. |
| `profile.hormone_therapy_status` | enum | `not_using` / `considering` / `using` / `discontinued` |
| `profile.surgical_history` | pipe-list | e.g. `hysterectomy\|oophorectomy`. Blank = none reported. |

> **On `profile.life_stage`.** Life-stage determination is a *capability under test* at tier A4, not
> a benchmark input. This field exists so that a scenario can hold stage constant when stage is not
> the thing being measured. The decision rule that maps profile signals to a stage label is an
> implementation choice — see the `life_stage_inference_contract` in
> [`agent_configs/A4_full_agentic.yaml`](../agent_configs/A4_full_agentic.yaml). Any rule satisfying
> that contract is conformant. Do not encode a specific rule here.

### Block C — Cycle history

| Column | Type | Description |
|---|---|---|
| `history.last_period_date` | `YYYY-MM-DD` | First day of the most recent period. |
| `history.periods_ceased_12m` | boolean | `true` if 12 or more months have elapsed since the last period. |
| `history.age_at_menarche` | integer | Contextual richness; not required by any scoring dimension. |
| `history.cycle_events` | JSON array | Up to 3 entries, most recent first. Each: `{"start_date": "...", "duration_days": n, "note": "..."}` |

### Block D — Symptom history

| Column | Type | Description |
|---|---|---|
| `history.symptom_events` | JSON array | Up to 5 entries, most recent first. Each: `{"text": "...", "severity": 1-10, "date": "YYYY-MM-DD", "triggers": ["..."], "note": "..."}` |

### Block E — Prior-session memory

Leave the whole block blank for a first-time user. Populate it to simulate a returning user — this
is what exercises the `cross_session_memory` capability at A3 and above.

| Column | Type | Description |
|---|---|---|
| `memory.session_summary` | string | Narrative of the previous session. The highest-impact memory field. |
| `memory.session_date` | `YYYY-MM-DD` | When the previous session occurred. Required for staleness tests. |
| `memory.reported_symptoms` | pipe-list | Symptoms raised last session. |
| `memory.contributing_factors` | pipe-list | Factors that worsened symptoms last session. |
| `memory.emotional_state` | string | Tone at the close of the previous session. |
| `memory.recommendations` | pipe-list | What the agent suggested last session. |
| `memory.action_items` | pipe-list | What the user agreed to do. |
| `memory.followup_required` | boolean | `true` if the previous session ended with an open clinical thread. |
| `memory.remembered_details` | JSON object | Free-form recalled facts, e.g. `{"sleep_pattern": "wakes 3x/night"}` |

---

## 2. Designing a useful persona

A persona is only worth adding if it can distinguish between tiers. Before committing one, state
which capability bundle it is meant to stress:

| To stress… | Build a persona that… |
|---|---|
| Grounding (A1) | Asks something with a specific, checkable clinical answer where an ungrounded model tends to confabulate. |
| Safety control (A2) | Requests something that should be refused or redirected — dosing, a medication change, a diagnosis. |
| Personalization read-side (A3) | Carries rich `memory.*` state that a competent agent should use and a naive one will ignore. |
| Agency write-side (A4) | Supplies information mid-conversation that should be confirmed before being persisted. |
| Memory staleness | Has a `memory.session_summary` that is contradicted by the current conversation. |
| Over-escalation control | Presents benign symptoms that superficially resemble red flags. |

A persona that every tier handles identically contributes nothing to a delta. Personas that
separate tiers are the valuable ones.

---

## 3. Coverage targets

The seed set ships two worked examples so the schema is concrete. The v0.2 target is **20 personas**
spanning:

- All three life stages, plus at least two with `profile.life_stage` deliberately blank.
- At least four returning users with populated `memory.*` blocks.
- At least two stale-memory cases.
- At least two surgical-menopause paths.
- At least two on hormone therapy.
- At least three over-escalation controls.
- A spread across all four `personality` values.

Expanding the persona set is one of the most useful contributions an external collaborator can make.
See [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## 4. Relationship to scenarios

A persona describes **who the user is**. A scenario describes **what happens in the conversation**
and what the agent is expected to do about it — including the hidden ground truth the judge scores
against. Multi-turn evaluation requires both.

Scenarios conform to [`schemas/scenario.schema.json`](../schemas/scenario.schema.json) and live in
[`scenarios/`](../scenarios/). A scenario references a persona by `persona_id`.
