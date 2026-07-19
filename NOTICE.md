# Public-Release Boundary

SAFE-CARE Bench publishes a **reusable evaluation methodology**. It deliberately does not publish the implementation of any production system.

## What this repository contains

- Implementation-neutral capability declarations for five ablation tiers
- LLM-judge prompts and full scoring anchor definitions
- The dataset filtering method and its rationale
- Synthetic persona generation methodology
- Derived, domain-filtered public question sets

## What this repository does not contain, by design

- Client or partner names, or any identification of a specific deployment
- Production system prompts, or the logic used to assemble them
- Internal component, class, service, or module names
- Database schemas, field names, or storage structures
- Environment variable names, endpoints, index names, or deployment configuration
- Model deployment identifiers or vendor-specific runtime detail
- Life-stage or clinical inference logic
- Real user data, production telemetry, screenshots, or credentials
- Defect records, known issues, or internal engineering notes for any live system

The ablation tiers describe **which capabilities are active at each level of the ladder**, not how any given team implements them. This is intentional: it makes the benchmark reproducible against any runtime, and it keeps client architecture private.

## Synthetic data only

Every persona is synthetic. No real patient data, no production conversation logs, and no protected health information appears anywhere in this repository or its history.

## Derived datasets

The filtered CSVs are derivative works of MedQA, MedMCQA, and MENST. They remain subject to the licenses and terms of their original publishers. The licenses in this repository cover only the original contributions made here.

## Reporting

If you believe any file in this repository discloses information that should not be public, contact **dev@conefia.com** before opening a public issue.

---

This boundary is consistent with the public-release commitment in the [SAFE-CARE framework](https://github.com/Conefia/SAFE-CARE).

© 2026 Conefia.
