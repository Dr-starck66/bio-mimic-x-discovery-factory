# BIO-MIMIC X — BSH K01442, centenarian cohort (exploratory audit)

**Scope:** test whether measured `cbh`/BSH (KEGG `K01442`) DNA abundance, normalized by `recA`, discriminates centenarians from elderly controls in PRJNA675598. It **cannot** validate future metabolic prediction, direct enzyme activity, longer lifespan or treatment efficacy.

## Verified sources

- Dantas Machado et al., *Cell Metabolism*, 16 Nov 2026, DOI: 10.1016/j.cmet.2026.10.016, PMID 43038987; Figure 2D compares normalized `cbh` vs `recA` in the cohort.
- NCBI PRJNA675598: 330 metagenomic experiments; ~0.20 TB of raw sequencing.
- Human bile-acid/metabolomic analysis: 48 young, 107 elderly, 125 centenarians — different analysis denominator than 330 metagenomes.
- Metadata curation lists 44 young, 110 elderly, 176 centenarian sequence samples and some repeated subjects. **These are sample groups, not a longitudinal metabolic outcome study.**

## Real-data extension completed 22 November 2026

**Verified source data and standalone reproducible audit are now in the same branch.**
- Original *Cell Metabolism* Data S1 Fig 2D: 308 published individual log(cbh_K01442/recA) observations, young 44, elderly 110, centenarians 154, in `data/centenarian_2026_Fig2D_ln_cbh_recA.csv`. **These are ratios, NOT separate raw cbh and recA count tables.** The supplementary figure contains no subject IDs.
- Fig S2D: 1,232 genuine ratios for `hdhA`, `baiA`, `baiB`, `baiH` stored in `data/centenarian_2026_FigS2D_other_bile_genes.csv`. They are **functional pathway comparators** but not unrelated molecular negative controls; do not match values across panels by row number.
- Primary unadjusted elderly-versus-centenarian AUC = **0.6207201889**, bootstrap 95% exploratory CI [0.55177, 0.68808], 2,000-label permutation p ≈ **0.0010**. Article's original reported p = 0.00083 (different test).
- Other pathway genes AUC: `hdhA` 0.70325, `baiA` 0.42155, `baiB` 0.67810, `baiH` **0.83542**. Therefore BSH is not the largest discriminator in the exploratory feature set.
- Independent Wu et al., *mSystems* (2019), DOI 10.1128/msystems.00325-19, Data Set S1 / PRJEB25514: 59 people (19 centenarians, 23 elderly, 17 young). Contains the gene pathway `7ALPHADEHYDROX-PWY`, not the direct BSH gene; independent **orthogonal pathway proxy** shows AUC = **0.56407**, exploratory 4,999-permutation p ≈ **0.2752** (not convincing), nonzero 4/19 centenarians vs 2/23 elderly. No direct K01442 replication claim.
- Run `node validation/bsh_published_data_audit.mjs .`; test `node tests/test_bsh_published_data_audit.mjs`. JSON results and source/protocol caveats: `reports/BSH-K01442-PUBLISHED-REANALYSIS-2026-11-22.json`.
- Numerical checks were rerun from the *stored GitHub CSV files*: the three AUCs 0.6207201889 / 0.8354191263 / 0.5640732265 matched the saved report. Local tests on a closely matched stdlib Node implementation passed 8/8; GitHub CI for the published script was not confirmed.

**Scientific boundary:** no separate measured K01442 + recA counts, unrelated microbial negative-control gene, paired participants IDs, adjustment for demographic confounders, or longitudinal metabolic endpoints; strict independent validation and clinical biomarker claim are **UNVERIFIED**.

## Inputs (not bundled)

A genuine measured TSV must contain these columns: `subject_id`, `group`, `cbh_K01442`, `recA`, `negative_control`, `sex`, `batch`. Group must be exactly `Centenarian` or `Elderly_control`. `negative_control` is a **predeclared, unrelated microbial gene abundance** quantified using the same pipeline. Counts must be non-negative and `recA` strictly positive. Each subject is aggregated to avoid pseudoreplication. Do not relabel a synthetic table as real data.

For reproducibility, extract the raw FASTQs from PRJNA675598 using a documented QC + host read removal + common reference annotation strategy (KEGG K01442 and recA plus a preregistered negative control), with per-run provenance/quality/versions. Metagenomics cannot measure actual enzyme catalysis. Do not mix the 280-person metabolite set with the 330 metagenome rows without verified subject-level IDs.

## Run

```bash
python validation/bsh_longevity_audit.py --input measured_abundances.tsv --output audit.json
python -m unittest -v tests.test_bsh_longevity_audit
```

The audit computes rank-based AUC for BSH and negative-control measurements; subject-level bootstrap exploratory CI of their difference, and a case-control label permutation test within sex×batch. It rejects missing molecule measurements and confounded batches with no shared groups. It does not provide adjusted regression, a causal effect or prospective prediction.

## Required independent validation

- Separate cohort with actual metabolic endpoints (e.g. fasting glucose, HOMA-IR, HbA1c) and measured matching BSH functional features; register primary outcome and covariates before analysis.
- Longitudinal samples and future outcome to claim *prediction*, with site/subject-separated training and testing, calibration and discrimination against baseline metabolic + demographic variables.
- Orthogonal measurement of BSH catalytic activity and bile acid ratios; test unrelated gene negative controls and other pathways.
- Human or microbiome intervention **not implied** by this computational code.

**Current reproducibility status (2026-11-22):** Real published log(cbh/recA) observations and four pathway gene comparators independently reanalyzed, plus a negative orthogonal pathway-level result in Sardinia. The original raw count features and direct BSH cross-cohort replication remain UNVERIFIED. See real-data extension above.
