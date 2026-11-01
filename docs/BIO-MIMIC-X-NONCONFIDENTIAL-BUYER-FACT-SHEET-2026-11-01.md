# BIO-MIMIC X — Non-confidential buyer fact sheet (November 1, 2026)

**For:** Corporate development, innovation scouting, computational biology and preclinical R&D teams  
**Transaction context:** Potential research-software evaluation, paid pilot or negotiated licence / acquisition. **No verified buyer offer, budget allocation, signed LOI or payment.** A seven-figure-euro transaction is an **owner negotiating objective**, not an independent valuation.

## Product: what exists

BIO-MIMIC X is an evidence-linked computational research pipeline for cross-species hypothesis screening, public transcriptome provenance, orthology checks, negative controls, science acceptance tests, and explicit rejection of unsupported clinical claims.

[Source code](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory) is public. Ownership, third-party code/data licensing, confidential know-how, patent novelty and freedom-to-operate have **not** been independently established. Do not promise that public materials are proprietary.

## Reproducible case study: preventing a misleading HAND2 assignment

1. AmexT_v47 / AmexG_v6 historical locus `AMEX60DD030069` has conflicting labels `HAND1 [nr]|HAND2 [hs]`.
2. An initial exploratory cross-species report assigned a number to **HAND2** based on the human-tagged annotation. The attribution was wrong or at least unsupported.
3. A public, sequence-based computational audit subsequently fetched the old chromosome `CM010932.2` and the modern NCBI HAND1 (`NC_090926.1`) and HAND2 (`NC_090937.1`) locus windows.
4. Strand-aware **unique 31-mers shared with the old locus**: HAND1 **26,858**, HAND2 **8**. This **strongly favors HAND1** in a local comparison; it is **not** a whole-genome reciprocal alignment, identity certificate or clinical discovery.
5. The original finding is **preserved**, a [public correction is published](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/blob/main/reports/factory/HAND2-HAND1-SEQUENCE-CORRIGENDUM-2026-11-01.md), and the upgraded parser excludes ambiguous HAND1/HAND2 identifiers.

**Independent verification:** Requested from AxoBase and the study author L. Otsuki on 1 November 2026; no expert response verified at the time of this note.

[Machine-readable source receipt and SHA-256](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/blob/main/reports/factory/HAND2-ASSEMBLY-SEQUENCE-PROBE-LATEST.json) · [Software CI acceptance run 41320421647](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/41320421647).

## Other evidence and important limits

- Exploratory RNA-seq count dataset **GSE284768** (axolotl, 25 sample columns) and processed human microarray **GSE28914** (25 human biopsies, six matched patient pairs in analysis) were ingested with provenance. Their biological contrasts are **not directly comparable**; the cross-species concordance claim remains blocked.
- Earlier preregistered GSE74387 replication **FAILED**; GSE113081 passed a single-cohort rule only.
- Software/unit tests validate computations and failure behavior; they **do not** demonstrate drug efficacy, axolotl-to-human regeneration, or meaningful economic ROI.
- Independent biological validation, exclusive intellectual-property rights, experimental replication and market willingness-to-pay are **UNVERIFIED**.
- The local commercial registry has **zero authenticated offers / contracts / paid pilots**. Metadata, PDF hashes or outgoing Gmail message IDs do not prove purchase intent.

## Proposed industrial evaluation

**Scope (decision requested, not yet contracted):** A structured technical evaluation on an independently selected public research dataset or a permitted partner dataset, with a prespecified baseline and blinded failure cases. Measure correct gene-identity attribution, provenance coverage, false-positive claims, analyst review effort and reproducibility. Include negative cases, scientific exclusion criteria and dataset licensing.

**Commercial decision requested:** Which person has authority for a paid software pilot and/or technology licence; whether a defined evaluation budget and procurement/technology-scouting process exists; whether an initial non-confidential demonstration is acceptable. An NDA can be discussed before any nonpublic information. No fabricated exclusivity or contractual rights.

**Status summary:** Source reproducibility **PASS for verified recorded software run**; independent locus identity **PARTIAL**; independent medical efficacy **UNVERIFIED**; commercial sale and €1M buyer commitment **UNVERIFIED**.

**Sensitive information:** Do not attach private correspondence, secrets or unpublished partner data to this public fact sheet.
