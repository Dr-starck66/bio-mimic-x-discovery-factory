# ASTRA MEDICAL Ω — FELINE six-gene replication attempt, 2026-11-19

## Actual independent public-data execution (Vercel Hobby ephemeral session)

**Evidence status:** PASS real public RNA matrix read and exploratory analysis on day-0 tumor-cell counts; **PARTIAL** on end-to-end retest of reconstructed standalone code; **UNVERIFIED** clinical treatment selection.

- Dataset GEO **GSE211434** (FELINE randomized neoadjuvant ribociclib+letrozole vs letrozole), distinct from NATALEE survival trial.
- Downloaded metadata 14,669,728 bytes; SHA256 **7d1d0e05683ee9bb2bb79011a0bdbe03daecde4c0be9197fbaff74329367e51d**.
- Streamed real RNA matrix from NCBI, reported compressed size **561,595,767 bytes**. No patient-level records committed to GitHub.
- Complete sample: 27 validation patients, 16 ribociclib combo (11 responders), 11 letrozole only (4 responders). Day-0 cancer-cell QC >=100 retains **26 patients**: 15 combo (11 responders, 4 nonresponders), 11 letrozole (4 responders, 7 nonresponders), **57,011 tumor cells**. One excluded by baseline cell QC, not by response.
- Six pre-published NATALEE candidate genes found in GEO gene count matrix. Pseudobulk per patient on **pretreatment cancer cells only**, `log1p(1e6*gene_UMI / total_patient_RNA_UMI)`. Within-cohort gene normalization without using outcome, no supervised fitting.
- Valid RNA streaming executed in 34.74s. Sandbox session **sbx_FexMxFytXNjNyAD8cQ9iKbqLAsDO**, `astra-feline-geo-research-20261119`, 1vCPU Hobby, temporary (expired). No persistent service or new billing plan.

## Within-arm response discrimination — deliberately retained negative results

Exploratory AUROC for binary neoadjuvant tumor response, 1,000 empirical label permutations per arm (two-sided). **Not** treatment-by-biomarker effect modification.

| Candidate | Ribo AUROC | Ribo permutation p | Letrozole AUROC | Letrozole permutation p |
|---|---:|---:|---:|---:|
| CEACAM6 | 0.2045 | 0.1179 | 0.3929 | 0.6623 |
| NOD2 | 0.7045 | 0.2797 | 0.5357 | 0.9381 |
| GPX3 | 0.5909 | 0.6643 | 0.3571 | 0.5275 |
| GATA3 | 0.2955 | 0.2857 | 0.5714 | 0.7852 |
| SLC39A6 | 0.5227 | 0.9580 | 0.8571 | 0.0679 |
| MAPT | **0.9318** | **0.0120** | 0.6429 | 0.5385 |
| Directional six-gene signature | **0.4091** | **0.6374** | 0.2857 | 0.3237 |

**Multiplicity:** MAPT unadjusted p=0.012, Bonferroni six tests ~0.072; **0/6** pass corrected alpha=0.05. No cross-cohort clinical validation; six-gene score failed. MAPT sign reported as association, not as a validated biomarker or evidence of benefit versus letrozole. Directional marker roles were drawn from exploratory NATALEE ASCO 2026 findings, not fitted to FELINE outcomes.

## Reproducibility, audit and blocking conditions

- Local standalone reconstructed Python standard-library runner and unit tests: **14/14 PASS**, also **14/14 PASS** under `python -O`, but **the reconstructed code has not run end-to-end against GEO**: remote sandbox expired before exact combinatorial p-value retest (HTTP **410 sandbox_stopped**). Do not claim exact permutations were completed. Its executable code, unit tests, aggregate outputs and prior FELINE analysis are packaged in the conversation artifact **ASTRA_MEDICAL_FELINE_GENE_PANEL_REAL_20261119.zip**, integrity SHA256 **24039e933304771430b1f7dfeb51edc8e000a7c9eb680da3d0f74dc772e4c18a**.
- No patient-level matrix, IDs, or health records are included in this report or conversation ZIP.
- A biomarker that discriminates responders *within a treated arm* is **not** evidence of a causal patient-level incremental response to ribociclib. Need randomized treatment×marker contrast and independent holdout, especially for small selected transcriptomic cohorts. FELINE response endpoint is not NATALEE 6-year survival.
- Full corrected standalone code is distributed in verified conversation ZIP, but not independently byte-for-byte reproduced from the ephemeral Vercel command source. No source-code merge or deployment performed.

**Primary source:** https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE211434 ; FELINE paper https://pmc.ncbi.nlm.nih.gov/articles/PMC11876604/ ; NATALEE exploratory candidates DOI https://doi.org/10.1200/JCO.2026.44.16_suppl.501 .
