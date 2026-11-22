# BIO-MIMIC X — BSH K01442, centenarian cohort (exploratory audit)

**Scope:** test whether measured `cbh`/BSH (KEGG `K01442`) DNA abundance, normalized by `recA`, discriminates centenarians from elderly controls in PRJNA675598. It **cannot** validate future metabolic prediction, direct enzyme activity, longer lifespan or treatment efficacy.

## Verified sources

- Dantas Machado et al., *Cell Metabolism*, 16 Nov 2026, DOI: 10.1016/j.cmet.2026.10.016, PMID 43038987; Figure 2D compares normalized `cbh` vs `recA` in the cohort.
- NCBI PRJNA675598: 330 metagenomic experiments; ~0.20 TB of raw sequencing.
- Human bile-acid/metabolomic analysis: 48 young, 107 elderly, 125 centenarians — different analysis denominator than 330 metagenomes.
- Metadata curation lists 44 young, 110 elderly, 176 centenarian sequence samples and some repeated subjects. **These are sample groups, not a longitudinal metabolic outcome study.**

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

**Current reproducibility status (2026-11-22):** 7 local unit tests PASS with synthetic values; real abundance TSV not available in the local environment; no biological AUC/p-value measured. Main claim: UNVERIFIED.
