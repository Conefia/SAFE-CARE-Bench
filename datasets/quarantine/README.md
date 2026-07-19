# Quarantine

Files here are **withdrawn from the benchmark** and retained only so that the provenance of a
correction remains auditable. Do not use them for evaluation.

| File | Withdrawn | Reason |
|---|---|---|
| `menopause_medmcqa.WITHDRAWN.csv` | v0.1.1 | Built from the MedMCQA test split: all 537 records carry `cop = -1` and empty `exp`, so the file has no answer labels. Separately, rows were selected by subject metadata rather than the documented term vocabulary — only 8.8% match any stated term. |

See [`../DATASET_CARD.md`](../DATASET_CARD.md) for the full account and the remediation path.
