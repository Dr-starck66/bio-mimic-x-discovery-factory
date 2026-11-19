# BIO-MIMIC X — first independent human GEO clock comparison, 2026-11-11

Source: [GSE142439](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE142439) NCBI public series matrix (HTTP 200). Independent from GSE165179/GSE165177. 16 samples, 8 normal/treated pairs: 4 skin fibroblast donors, 4 vein endothelial donors. GEO metadata provide two previously calculated clock age fields, `dnamage` and `dnamageskinbloodclock`. **These are GEO-provided age values, not recalculated by ASTRA from IDAT files.**

| Donor | Cell | Horvath delta years | Skin & Blood delta years |
|---|---|---:|---:|
| 1 | fibroblast | +0.1448 | -1.2515 |
| 2 | fibroblast | +0.3204 | -3.1593 |
| 3 | fibroblast | -1.8946 | +0.3768 |
| 4 | fibroblast | -5.9420 | -0.2405 |
| 5 | endothelial | -5.3156 | -3.7529 |
| 6 | endothelial | -0.4715 | -2.8908 |
| 7 | endothelial | -8.2854 | +1.7434 |
| 8 | endothelial | -5.7276 | -1.6053 |

Means (unweighted across 8 donors): Horvath -3.3964 years, Skin & Blood -1.3475 years. Negative direction: 6/8 donors on each clock; concordant decrease: 4/8 donors (4,5,6,8). **Pre-registered 80% Skin & Blood donor-decrease requirement fails (6/8 = 75%)** even before confidence interval; therefore this dataset does NOT pass the primary replication criterion. Distinct intervention and cell types limit direct comparability. The protocol also requires complete observed Skin & Blood CpGs; these were not independently verified, so dataset eligibility for definitive replication remains UNVERIFIED. No RNA matched samples or functional/safety measures established in this audit.

Acquisition code logic: download https://ftp.ncbi.nlm.nih.gov/geo/series/GSE142nnn/GSE142439/matrix/GSE142439_series_matrix.txt.gz, gunzip, parse !Sample_title, !Sample_geo_accession, !Sample_characteristics_ch1; group by `individual|cell type`; compare Treated minus Normal on `dnamage` and `dnamageskinbloodclock`. 8 pairs, 0 unpaired. No simulation.

PASS: NCBI metadata acquisition and donor-level arithmetic. PARTIAL: independent human cohort evidence. FAIL: 80% decrease threshold on reported Skin & Blood values. UNVERIFIED: original-data clock recalculation, matched RNA, passage, causality, safety, clinical efficacy. Preserve contradictory donors and negative controls.
