# Locks

**Pre-registration record for SAFE-CARE Bench Study 1.**

Each lock freezes a set of documents before the data they govern exists. The documents are hashed with
SHA-256 and the hashes recorded here. **The commit timestamp on this file is the evidence of ordering**,
which is the only thing the lock is for.

The documents themselves are not published here. They are released with the paper.

---

## Lock A — the analysis plan and its packet

**Frozen before the first Run 3 model call.** At the time of this commit no Run 3 conversation had been
generated and no clinician rating existed.

**Freezes:** every methodological choice in the analysis plan. Models, estimands, mappings, crosswalks,
aggregation rules, exclusions, inferential procedures, multiplicity correction, missingness handling,
software and output shells, for both the automated and the clinician side.

| File | Version | SHA-256 |
|---|---|---|
| `Study1_Analysis_Plan.md` | v0.9 | `988ce8867c3c770ccadda9f3b3ded61cd419d7fed44fdd037bcce0752870d3cc` |
| `RUN_3_INSTRUCTIONS.md` | v0.9 | `8902e3865c7da5919d0d34c844ab15e617b0d2f1bc966e2335195d44642ce98d` |
| `RUN_3_OUTPUT_SPEC.md` | v8 | `fa971aa485881baedaa4d4d80eecf11b9ddd2dd14991eb4ca7d372b013140573` |
| `Study1_Protocol.md` | v0.7 | `594bae8d94ab18200270e744010fd1034ad3331892e5f7c563ba73c83173a897` |

**Combined, concatenated in the order above:**

```
981724bdde0b644977e3f8925e8dfda14b7d2187576522195294d878c080603f
```

**After this commit the analysis plan does not change.** Any subsequent amendment is a deviation,
recorded with its date and reason and published with the paper. Roles and scheduling are not
methodological choices and are not frozen by this lock.

---

## Lock B — the realised design annex

**Not yet set.** Records the realised rater-conversation design before any returned rating is opened.
Adds no methodology.

## Clinician answer key

**Not yet set.** The split schema `clinical_escalation_expected` and `agent_handoff_expected`, frozen
and hashed **before the first rating packet is sent.** A key hashed after raters hold the cases proves
nothing.

---

## How to verify

```bash
sha256sum Study1_Analysis_Plan.md RUN_3_INSTRUCTIONS.md RUN_3_OUTPUT_SPEC.md Study1_Protocol.md
cat Study1_Analysis_Plan.md RUN_3_INSTRUCTIONS.md RUN_3_OUTPUT_SPEC.md Study1_Protocol.md | sha256sum
```
