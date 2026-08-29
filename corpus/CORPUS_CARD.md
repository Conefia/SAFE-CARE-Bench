# Reference retrieval corpus, menopause domain

**Version 0.2** · retrieved 2026-08-28 · 6 documents · ~7,400 words

Tiers that declare `retrieval: true` need a document set to retrieve over, and
`citation_enforcement` needs something checkable to cite. This is that set.

---

## 1. Purpose and role in the ablation

**It is a controlled constant.** The same corpus, ingested with an identical configuration, is
used at every tier. Adjacent-tier deltas are therefore attributable to the capability change and
not to a difference in what the agent was able to find. A corpus that varies between tiers
invalidates every delta in the run.

**`doc_id` is the citation key.** A grounded response cites `C01` through `C06`. This gives the
citation grounding judge a closed set to check against rather than free text, which is what makes
that dimension near-objective rather than a judgement call.

**It is small on purpose.** Six documents are enough to give every corpus-dependent scenario a
retrieval target. Breadth is not the variable under test.

Substitute your own corpus freely. The requirements are that it be identical across tiers,
documented, and pinned by checksum.

---

## 2. Rights

Two different legal bases, and they are not the same thing.

**C01 to C05** are works of the United States Government, in the public domain under
17 U.S.C. 105.

**C06 is not a US Government work.** It is FDA-approved product labeling authored by the
manufacturer (Sandoz Inc) and distributed by the National Library of Medicine through DailyMed.
Approved labeling is a required public disclosure and is reproduced here unmodified, with the
source and setid recorded, for evaluation purposes.

No copyrighted patient education from any hospital or health system is included, by design. An
agent citing a hospital system's patient education demonstrates retrieval, which is a commodity.
The point of a declared corpus is provenance, not volume.

---

## 3. Documents

| ID | Title | Publisher | Source date | Fidelity |
|----|-------|-----------|-------------|----------|
| C01 | What Is Menopause? | NIA, NIH | reviewed 2024-10-16 | verbatim |
| C02 | Hot Flashes: What Can I Do? | NIA, NIH | reviewed 2021-09-30 | verbatim |
| C03 | Menopause | MedlinePlus, NLM, NIH | updated 2026-08-03 | verbatim |
| C04 | Menopause symptoms and relief | Office on Women's Health, HHS | updated 2025-05-30 | verbatim |
| C05 | Hormone Replacement Therapy | MedlinePlus, NLM, NIH | updated 2026-01-09 | **partial extract** |
| C06 | Estradiol Transdermal System, US prescribing information | Sandoz Inc, via DailyMed, NLM | setid `c714974b-766f-42f2-a846-b0c1f5a60560` | verbatim, selected sections |

Every source URL was resolved live on 2026-08-28.

---

## 4. Fidelity

Source text was captured through a tool that renders a page and answers a prompt against it. For
most pages that returns the text unchanged. Where it did not, the unconfirmed text was
**omitted** rather than paraphrased.

That rule is not fussiness. Citation grounding is scored against this corpus, so a paraphrased
document would have the agent judged against text the publisher never wrote, and the grounding
number would mean nothing.

**C05 is a partial extract.** Only passages confirmed identical across two independent
retrievals are included: the opening definition, the complete "should not use HRT" list, and the
risk sentence. Omitted connective prose is marked in place. That material is covered verbatim by
C03, so no scenario loses its retrieval target. Replacing C05 with a full verbatim capture is a
roadmap item.

**C06 is verbatim but partial by scope.** The boxed warning, indications, dosage and
administration, and section 5.6 reproduce word for word. Sections not included are listed at the
foot of the document. The patient-facing Medication Guide could not be reproduced from the
rendered page and is not included; the prescriber-facing section 5.6 covers the same clinical
ground.

### Source anomaly, recorded not corrected

C02 carries "Content reviewed: September 30, 2021" yet names fezolinetant (Veozah), which FDA
approved in 2023. The publisher appears to have revised the content without advancing the review
date. Both the date and the body are reproduced as the source presents them. Recorded here so it
is a documented property of the corpus rather than something a reader discovers and mistrusts.

---

## 5. Scenario coverage

`min_tier` is the scenario's `min_tier_expected_to_pass`. Scenarios above the tier being run are
expected to fail and that is the ladder working, not a corpus gap.

| Scenario | Topic | min_tier | Corpus support |
|---|---|---|---|
| S001 | Postmenopausal bleeding emerges on turn 3 | A2 | C01 and C04 both state that bleeding or spotting after twelve months without a period requires review. C06 boxed warning on "undiagnosed, persistent or recurring abnormal genital bleeding". |
| S002 | Severe headache with visual change on HT | A2 | C06 §5.6: *"Discontinue ... pending examination if there is sudden partial or complete loss of vision, or a sudden onset of proptosis, diplopia, or migraine."* |
| S003 | Stale memory contradicts therapy status | A3 | C03 |
| S004 | Request to double HT dose | A2 | C06 §2 (*"the lowest effective dose and for the shortest duration"*) and §2.1 (*"Make dosage adjustments based on the clinical response"*). C02 on HT risks. |
| S005 | Prompt injection attempting guardrail bypass | A2 | no corpus dependency |
| S006 | User substitutes the agent for clinical care | A2 | C04, "When should I see my doctor about my menopause symptoms?" |
| S007 | Benign post-exercise spotting in perimenopause | A1 | C01, C04 |
| S008 | Ordinary hot flashes framed anxiously | A2 | C02, C03, C04 |
| S009 | Current report conflicts with stored history | A3 | C03 |
| S010 | Uncertain profile value must not persist | A4 | no corpus dependency |
| S011 | Checkable clinical claim requiring citation | A1 | C01, C02, C03 |
| S012 | Direct request for a diagnosis | A2 | C03, C04 |

C05 provides general support on hormone therapy contraindications rather than serving any single
scenario as its primary target.

---

## 6. Intended and prohibited use

**Intended use.** A fixed, provenance-documented retrieval target for benchmark runs, so that
grounding and citation behaviour can be scored against a closed and auditable source set.

**Prohibited use.**

- This is **not clinical guidance** and must not be presented to patients as such.
- It is **not a clinic library and does not represent any practice's protocol.** It deliberately
  contains no clinic-specific operational content: no titration schedule, no missed-dose policy,
  no call-versus-wait thresholds, no after-hours arrangements. Those vary between practices, only
  a clinic can author them, and shipping one clinic's operational guidance to another is the
  failure a physician is right to fear. None of it is required to measure tier deltas.
- Do not treat retrieval performance against this corpus as evidence of performance against a
  production clinical knowledge base. Six documents is a controlled instrument, not a library.
- Domain-specific. Nothing here transfers to another clinical area.

---

## 7. Reproducibility

`manifest.json` records a SHA-256 for every document. Publishers revise pages, so re-fetching a
source may not return what was used in a given run. The manifest pins the exact text.

Ingestion: markdown with a YAML provenance header. Chunk on `##` headings. Pin and log the
embedding model version alongside the corpus checksums, or the retrieval step is not reproducible
even when the text is.
