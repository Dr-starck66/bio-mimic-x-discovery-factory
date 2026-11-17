# BIO-MIMIC X — published 75-gene HfRI replay on GSE294705

**Executed 11 November 2026. Computational execution: PASS. Faithful publication reproduction: PARTIAL. Clinical biomarker validation: UNVERIFIED.** The source was published by Baek et al., *BMC Medicine* 24, 196 (2026), DOI https://doi.org/10.1186/s12916-026-04745-8. Reproducing a published score is **not** discovering a new biomarker.

## Actual public sources and traceability

- Authoritative molecular count file: NCBI GEO GSE294705, **94 samples, 63,241 gene rows**. SHA-256 gzip `f5ca68e03d0547cc9faad8940f75181640f1d99dbdbc6119faf85da8c49729ce`.
- GEO sample metadata sha256: `15c06e2554466f65f43cbf38238eeaaf089cd650440b9b2f18dcf76c958e8212`.
- 94 matched sample IDs; label **recurrence(2>=): Yes 16, No 78**.
- Authors' Supplementary Table S2, *Additional file 1*, original DOCX: https://static-content.springer.com/esm/art%3A10.1186%2Fs12916-026-04745-8/MediaObjects/12916_2026_4745_MOESM1_ESM.docx . SHA-256: `7a2f33a66ca2f024be6e15019682a2f697d3dbb91715fc4c63d9946b1077a7a4`.
- **75 unique published genes and 75 exact reported coefficients** extracted, 34 positive and 41 negative. Mapping checked against HGNC gene-symbol service: **75/75 authoritative Ensembl IDs**, including historical `CENPJ` now official `CPAP` (`ENSG00000151849`). Six formerly ambiguous MyGene suggestions resolved with HGNC canonical identifiers.
- All 75 canonical Ensembl IDs exist in the GSE294705 full count table.

## Transparent implementation and discrepancy

- Python 3.11/NumPy 2.3.5, existing authorized **Floot DUALITY X V0.3 ECO remote VM**, ephemeral dependency installation with binary wheel digest verification, **5/5 unit checks PASS**, genuine direct NCBI acquisition. No new infrastructure fee or production deployment.
- Complete sample library-size CPM followed by `log2(1+CPM)`, approximate between-sample quantile normalization preserving ties, per-gene across-cohort z-scoring, fixed weighted sum of the author's 75 Cox coefficients. No outcome-trained parameters, cutoff optimization, retrospective selection of a positive direction, or AI claim.
- **Processing discrepancy** explicitly preserved: `FOXI2` (`ENSG00000186766`) is measured in 56 of 94 samples but has mean CPM below the article's described feature-filter threshold. Dropping it would make the score 74-gene, so this replay retains this **one source-defined model feature**, even while excluding other low-CPM genes during quantile normalization. This deviates from a strictly applied global CPM filter and may alter normalization. The published z-score reference cohort, high/low HfRI threshold and validation classifier are not fully reproduced.

## Numerical findings on the actual 94-sample cohort

| Approximate fixed score | In-sample AUC for ≥2 recurrences | Yes minus No mean weighted score | Permutation p (sex / stage / 807 vs 888 site group) |
|---|---:|---:|---:|
| Author-weighted, quantile-normalized | **0.58653846** | +8.98592670 | **0.55134487** |
| Author-weighted, logCPM without quantile normalization (sensitivity) | **0.58653846** | +9.43581408 | **0.51534847** |

Scores were kept in their original higher-is-riskier direction. **Neither implementation provides a statistically significant association** in our stratified permutation check. These are *in-sample descriptive* AUC measurements on the authors' own validation cohort, not an independent clinical performance estimate. A published AUC for a different original cohort or classification experiment **must not** be directly compared as evidence that the original authors are wrong.

This analysis did not validate a new biomarker, does not test cretostimogene, ANKTIVA or UGN-501 responses, and cannot determine a patient treatment decision.

## Replayable and negative evidence

- [Published 75-gene weights and HGNC Ensembl mapping](../../research/cretostimogene/hfri_published_75_gene_weights_hgnc_2026-11-11.json)
- [Executable Python protocol](../../validation/gse294705_hfri_published_weights_replay.py)
- [Real-data output](../../reports/cretostimogene/gse294705_hfri_75_gene_published_model_replay_2026-11-11.json)
- [Independent three-signature recurrence audit](GSE294705-INDEPENDENT-RECURRENCE-AUDIT-2026-11-11.md)

**PASS:** direct data and supplementary material acquisition; SHA-256; 75 unique weights; authoritative 75/75 Ensembl ID mapping; 94-count-column alignment; local computation and checks; GitHub saved report.

**PARTIAL:** approximate preprocessing and lack of published exact normalization/cutoff information; 16 recurrence events, stratified permutation has restricted label exchangeability and low power; clinical endpoint is ≥2 recurrences and not BCG durable response.

**FAIL as a positive discovery claim:** AUC 0.5865 is not evidence of an externally validated biomarker or an improvement on the authors' HfRI. Formal performance validation is **UNVERIFIED**.

A written methods clarification was requested from the corresponding research contact in order to determine if a strictly matched replay is feasible. Any response should be recorded, not presumed.
