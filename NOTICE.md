# Public-Release Boundary and Ownership

SAFE-CARE Bench publishes a **reusable evaluation methodology**. It deliberately does not publish
the implementation or the operational configuration of any production system.

## Ownership

All methodology, evaluation design, capability declarations, judge prompts, scoring anchors,
schemas, filtering procedures, and documentation in this repository are the intellectual property of
**Conefia LLC** (d/b/a Conefia Technologies), and are published here by Conefia under the licences
stated in the [README](README.md#license).

Conefia's [Intellectual Property Policy](https://conefia.com/ip-policy) reserves to Conefia all
right, title, and interest in its evaluation systems and testing approaches, agent architectures and
orchestration systems, methodologies and playbooks, prompts and prompt libraries, and the inventions
and know-how arising from them — including where these were developed, improved, or reduced to
practice in connection with a client engagement. Publication of this benchmark is an exercise of
that ownership, not a waiver of it.

Author listing in [`CITATION.cff`](CITATION.cff) and [`CONTRIBUTORS.md`](CONTRIBUTORS.md) denotes
**scholarly contribution only**. It does not convey, divide, or imply any ownership interest. All
intellectual property rights vest in Conefia LLC.

Publication here does not grant any right to use Conefia intellectual property beyond the terms of
the stated licences.

## What this repository contains

- Implementation-neutral capability declarations for five ablation tiers
- LLM-judge prompts and full scoring anchor definitions
- Machine-readable scenario schema and multi-turn scenario set
- The dataset build pipeline, filtering method, and dataset card
- Synthetic persona schema and generation methodology
- Derived, domain-filtered public question sets

## What this repository does not contain, by design

- Client or partner names, or any identification of a specific deployment
- Production system prompts, or the logic used to assemble them
- Internal component, class, service, or module names
- Database schemas, table names, field names, or storage structures of any deployed system
- Environment variable names, endpoints, index names, or deployment configuration
- Model deployment identifiers or vendor-specific runtime detail
- The specific decision rule used by any deployed system to infer clinical life stage
- Real user data, production telemetry, screenshots, or credentials
- Defect records, known issues, or internal engineering notes for any live system

Two distinctions are load-bearing here.

**Capability versus implementation.** The tier configurations declare *which capabilities are active
at each rung of the ladder*, not how any given team implements them. Life-stage inference, for
example, is declared as a capability with a stated behavioural contract at tier A4; the decision rule
that satisfies that contract is left to the implementer. This makes the benchmark reproducible
against any runtime, and it keeps both client architecture and Conefia's own patentable subject
matter out of the public record.

**Methodology versus operational configuration.** The evaluation methodology is Conefia IP and is
published deliberately. The operational configuration of a client's deployed environment — its
storage model, field names, and integration detail — is not published, consistent with the
confidentiality proviso in Conefia's IP Policy §5 and §7.

## Synthetic data only

Every persona is synthetic. No real patient data, no production conversation logs, and no protected
health information appears anywhere in this repository or its history.

## Derived datasets

The filtered CSVs are derivative works of MedQA, MedMCQA, and MENST. They remain subject to the
licences and terms of their original publishers. The licences in this repository cover only the
original contributions made here. See [`datasets/DATASET_CARD.md`](datasets/DATASET_CARD.md).

## Reporting

If you believe any file in this repository discloses information that should not be public, contact
**dev@conefia.com** before opening a public issue.

---

This boundary is consistent with the public-release commitment in the
[SAFE-CARE framework](https://github.com/Conefia/SAFE-CARE).

© 2026 Conefia LLC. SAFE-CARE™ is a claimed unregistered trademark used by Conefia LLC.
