# BIO-MIMIC X × CG Oncology — real GSE244895 RNA expression execution audit
**Execution date:** 2026-11-11 · **Scientific status:** PARTIAL / EXPLORATORY · **Code/data execution:** PASS · **No CG Oncology collaboration or cretostimogene-response data.**

## Authorized execution and real source

Executed the original `validation/cretostimogene_bcg_tpm.py` from [PR #45](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/45) on **Floot's already connected DUALITY X V0.3 ECO project VM** (project `a80a6a97-ccdd-419f-8ce3-cc7ec73adcac`) with `python3` 3.11.2, NumPy 2.3.5 installed into **ephemeral** `/tmp` from a SHA-256-verified PyPI wheel (no subscription purchased, no new deployment). Python's `urllib.request` fetched the GEO gzip directly, and the run reported `acquisition: downloaded`, not a synthetic or local-unverified input.

- Source: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE244nnn/GSE244895/suppl/GSE244895_Bladder_BCG_STAR_RSEM_TPM_raw_.txt.gz
- **HTTP 200**, gzip compressed length **623705 bytes**; decompressed UTF-8 length **1830368 bytes**.
- **Source SHA-256:** `712480491eb29d56e645650893692f9db2fa3e7ebc30bb41c08e5f9ccc30bac8`
- Python script SHA-256: `af3de769ea72b0ee3c02e51bc2192ea7bedd7b1fdda7679c026e80068885f255`
- **11/11 existing + new regression tests PASS in the remote VM**, independently also 11/11 PASS locally on synthetic fixtures and metadata.
- **Run PASS:** `EXPLORATORY_GEO_DOWNLOADED`, 35 observed specimen columns, 14 unique IDs, **12 patient-level pre/post pairs** (13 before, 22 after), 4639 intact feature rows, eight of 22 predeclared gene symbols matched exactly, seed 20261108.
- Original, full machine-readable result: [gse244895_paired_exploratory_2026-11-11.json](../../reports/cretostimogene/gse244895_paired_exploratory_2026-11-11.json).

## Real raw-file anomaly and fail-closed correction

First real execution **FAIL**: `ValueError: Inconsistent row width`. Independent Node inspection of the downloaded file confirmed **one malformed terminal record**, source line **4641**, `DEFB110`, **7 fields** instead of the 36-field matrix width (gene ID + 35 samples). All preceding **4640 lines (header + 4639 complete gene rows)** had 36 fields. Gzip CRC passed; the source content itself contains this incomplete row.

**Correction:** updated the original Python validator to allow exactly this single terminal `DEFB110` record to be quarantined **only** when all SHA-256 and structural invariants match the audited source. Other malformed records, modified fingerprints, source-position changes, multiple errors, affected predeclared genes, or unexpected column counts **FAIL closed**. Two new regression tests cover this exception and rejection of arbitrary/mid-file corruption. This is a transparent one-row exclusion, not imputation, data fabrication, or a general-purpose parser permissiveness change.

## Paired gene estimates (12 independent patient pairs)

Effects are mean **post-minus-pre log2(TPM+1)** after averaging repeated post samples *within* each patient. Two-sided **exact sign-flip p-values** enumerate 4096 paired sign configurations; Benjamini-Hochberg correction is calculated across the eight predeclared markers actually present in this file.

| HGNC gene | mean Δ log2(TPM+1) | exact p | BH-adjusted q |
|---|---:|---:|---:|
| CXCL9 | +0.353408 | 0.09863281 | 0.29785156 |
| CD8A | +0.258220 | 0.14892578 | 0.29785156 |
| CXCL10 | +0.227664 | 0.21435547 | 0.34296875 |
| CTLA4 | +0.204588 | 0.26416016 | 0.35221354 |
| CD8B | +0.178855 | 0.12890625 | 0.29785156 |
| CD68 | +0.067726 | 0.09619141 | 0.29785156 |
| CD163 | +0.057506 | 0.50097656 | 0.50097656 |
| CXADR | −0.053662 | 0.45361328 | 0.50097656 |

**Negative scientific finding: all eight q-values > 0.05. No marker is statistically significant at FDR 5%; no predictive BCG biomarker demonstrated.** Bootstrap confidence intervals and a single randomized sign-flip negative-control contrast are retained in JSON. **CXCL9** has a positive bootstrap interval in this small sample but does **not** pass the preregistered multiple-testing threshold; do **not** report it as confirmed.

**Not found in this matrix** (and never assessed): `RB1`, `E2F1`, `FOXP3`, `IFNG`, `STAT1`, `IL17A`, `IL21`, `IL26`, `PDCD1`, `HAVCR2`, `LAG3`, `MKI67`, `HLA-A`, `HLA-B`. Missing gene rows are **not** evidence of absent biological expression.

## Second independent implementation check

A separate Node.js implementation running in the same Floot VM independently fetched the **same sha256-pinned gzip**, decompressed and parsed all rows, computed all eight patient-averaged log2 changes, independently enumerated all exact sign-flip distributions, and independently implemented Benjamini-Hochberg adjustment.

**PASS:** eight effect estimates, eight p values, and eight BH q-values matched the Python report within **1e-7** tolerance (for `CTLA4`, the displayed q differed by 1e-8 due to floating point/rounding). This is an independent computational implementation check **but not an external biological cohort or laboratory validation**.

## Evidence tiers and limitations

- **PASS / COMPUTATIONAL:** NCBI real data transferred via remote authenticated VM; fingerprint recorded; corrected parser exercised; 11/11 remote tests; reproducible 8-marker analysis saved to GitHub; separate Node calculations matched.
- **PARTIAL / BIOLOGICAL:** small pre/post observational cohort, heterogeneous repeated post timepoints; not randomized; no untreated comparator; confounding by sampling, time and recurrence unresolved. All 8 FDR results negative.
- **UNVERIFIED / EXTERNAL:** clinical BCG response labels, independent cohort replication, cretostimogene-treated patients or validated predictors, laboratory experiments, CG Oncology scientific partnership, clinical impact, commercial value.
- **NO CLAIM:** cancer treatment efficacy, patient-specific treatment guidance, biomarker validation, causal effects or superior results over CG Oncology's research.

These data **cannot** decide whether cretostimogene works. The next scientifically necessary action is **independent BCG cohort replication with verified response labels and covariate metadata**, followed by a separate validation in oncolytic-virus-treated samples only if legitimately accessible.

*No production site, domain, scheduled automation, GitHub Actions run, or new paid cloud project was created for this execution.*
