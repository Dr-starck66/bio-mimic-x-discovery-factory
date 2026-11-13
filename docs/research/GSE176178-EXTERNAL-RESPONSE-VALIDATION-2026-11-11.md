# BIO-MIMIC X × CG Oncology — external public BCG response-cohort audit
**Executed 2026-11-11 · Reproducible computational PASS · clinical biomarker FAIL (non-significant) · exploratory only.**

## Purpose and limits

A prior, real GSE244895 analysis found non-significant before/after BCG RNA changes for eight genes and three exploratory two-gene immune proxies. It cannot estimate responder versus nonresponder differences. We now *independently test the same pre-defined two-gene proxies* on **GSE176178**, a distinct cohort that *does* label durable BCG response (Yes/No). **These are different clinical estimands**, therefore this is not direct replication of the first cohort's pre/post contrast. There are **no cretostimogene-treated patient labels** in either dataset.

## Source and integrity proof

- NCBI GEO accession: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE176178
- Primary count matrix: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE176nnn/GSE176178/suppl/GSE176178_RNA.featurecounts.txt.gz
- Count-matrix compressed bytes: **6,942,301**; source **SHA-256** `f785ffeae2ef4f6b5f673fd46e1c7bc3b121fae91c49d22001b75e2daba75c4c`.
- GEO series metadata: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE176nnn/GSE176178/matrix/GSE176178_series_matrix.txt.gz
- Metadata compressed bytes: **3,948**; metadata **SHA-256** `ef5232392e1da3b91c995cd750098bb5a51aacdf4eda6d471101b8832421c565`.
- **40 unique sample IDs** (matched exactly between counts and GEO clinical metadata); **59,412 gene rows**; **17** durable response Yes, **23** No. 31 male / 9 female; **7 female among Yes** but **2 female among No**.
- Live execution and repeated re-execution on the existing authorized Floot DUALITY X V0.3 ECO VM; source Node script exact SHA-256: `3e40cc03b694614d2d11bc2329a20a88b82659469dcbc6c9df82849dc394adb0`; 6 offline code self-checks PASS, including correct AUC, Benjamini–Hochberg, label permutation within sex and metadata integrity failure.

## Method (predefined 3 signatures, no training)

1. Strict source fingerprint and sample identity checks.
2. FeatureCounts library totals per sample; **log2(1 + CPM)** normalized values. Signature = arithmetic mean of the two gene expression values. Each tumor is one sample; no patient splits or train/test model.
3. Unadjusted difference **Yes − No**, in-sample descriptive AUC; **20,000 Monte-Carlo label permutations** (add-one p estimator), both unrestricted and **within-sex strata** (holding observed 7F/2F and 10M/21M response-group composition fixed).
4. Benjamini–Hochberg correction over three tested signatures. Additional male-only sensitivity (10 Yes, 21 No; 10,000 permutations). Stratified-within-response group unadjusted bootstrap CI, 2,000 draws.
5. Fixed random seed 20261111; no gene selection fitted to outcomes. Three gene sets were selected from the separate earlier GSE244895 exploration; they are **not trial preregistered**.

## Results (external cohort, real molecular data)

| Predefined two-gene proxy | Genes | Yes − No, log2(1+CPM) | In-sample AUC | sex-stratified p | BH q (sex-stratified) | male-only p |
|---|---|---:|---:|---:|---:|---:|
| IFN_CHEMOKINE_PROXY | CXCL9, CXCL10 | -0.013972 | 0.49105 | 0.97790 | **0.97790** | 0.86031 |
| T_CELL_CD8_PROXY | CD8A, CD8B | -0.210619 | 0.41176 | 0.45368 | **0.97790** | 0.93101 |
| MACROPHAGE_PROXY | CD68, CD163 | -0.065638 | 0.49616 | 0.74551 | **0.97790** | 0.91711 |

**All three signals FAIL to clear FDR 5%**; AUCs close to or below chance in-sample. No biological signature predictive of durable BCG benefit was validated. Unadjusted bootstrap confidence intervals for all three include zero. Male-only sensitivity does not rescue any association. These **negative results are intentionally preserved**.

The outcome groups are sex-imbalanced; other clinical variables, grade, batch, collection timing and causality remain uncontrolled. The 40-sample in-sample AUC is descriptive, **not** an externally validated predictive performance. These 3 selected proxies are not a comprehensive transcriptomic discovery screen. Processed RNA counts and observational clinical labels do not establish direct tumor immune cell abundance.

## Deliverables and honest statuses

- **PASS — public source acquisition / checksums / sample alignment / 6 basic unit tests / CPU computation / repeatability**.
- **PASS — 20,000 unadjusted + sex-stratified label permutations per signature; results stored as full machine JSON**.
- **FAIL — pre-defined signature association threshold**: all q=0.97790, including the most lenient nominal tests.
- **PARTIAL — clinical scientific generalization**: distinct cohorts measure different outcomes; no causal or prospective replication.
- **UNVERIFIED — cretostimogene response, treatment utility, clinical validation, external partnership, industrial benefit**.

Reproducible source: [validation/gse176178_external_bcg_validation.mjs](../../validation/gse176178_external_bcg_validation.mjs) (standalone, built-in Node APIs, no package install). Full machine result: [reports/cretostimogene/gse176178_outcome_validation_2026-11-11.json](../../reports/cretostimogene/gse176178_outcome_validation_2026-11-11.json). Initial GSE244895 audit: [GSE244895-REAL-EXECUTION-AUDIT-2026-11-11.md](GSE244895-REAL-EXECUTION-AUDIT-2026-11-11.md).

*Not a clinical recommendation or a claim to improve oncolytic therapy.*
