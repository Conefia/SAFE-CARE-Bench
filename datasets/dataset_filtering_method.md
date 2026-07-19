# Dataset Filtering Method — MENST

## Overview

The MENST dataset was filtered to retain only rows relevant to perimenopause and menopause. Filtering was applied programmatically using a keyword-matching procedure against all available text fields in the dataset.

---

## Keyword List

The following 13 domain-specific terms were used as the filtering vocabulary:

| # | Keyword |
|---|---------|
| 1 | menopause |
| 2 | perimenopause |
| 3 | postmenopausal |
| 4 | estrogen |
| 5 | estradiol |
| 6 | progestogen |
| 7 | hormone replacement |
| 8 | vasomotor |
| 9 | hot flashes |
| 10 | atrophic vaginitis |
| 11 | osteoporosis |
| 12 | amenorrhea |
| 13 | endometrial cancer |

---

## Filtering Procedure

1. **Case normalization.** All text fields were converted to lowercase prior to matching to ensure case-insensitive comparisons.

2. **Multi-field matching.** Each row was evaluated across all available text columns. The dataset supports two schema versions:
   - *Original schema:* `Questions`, `Human`, `Topic`
   - *Updated schema:* `Question`, `Answer`, `Keywords`, `Topic`

   Column resolution was performed dynamically at runtime to accommodate both versions.

3. **Inclusion criterion.** A row was retained if at least one keyword appeared as a substring in any of the resolved text columns. Matching was performed using exact substring search (no stemming or fuzzy matching).

4. **Output.** Retained rows were written to a filtered CSV file preserving the original column structure.

---

## Rationale

Substring matching without stemming was chosen for precision — to avoid false positives from morphologically related but clinically distinct terms. The keyword list was curated to cover the core clinical vocabulary of perimenopause and menopause, including hormonal markers (*estrogen*, *estradiol*, *progestogen*), symptom descriptors (*vasomotor*, *hot flashes*, *atrophic vaginitis*), and associated conditions (*osteoporosis*, *endometrial cancer*, *amenorrhea*).

---

*This filtering step was implemented as Task D1 of the SAFE-CARE Bench dataset preparation pipeline.*
