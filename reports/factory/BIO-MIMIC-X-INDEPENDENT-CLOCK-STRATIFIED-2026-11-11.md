# BIO-MIMIC X | independent human clock cross-check (2026-11-11)

Reproducible local Python analysis (8 independent paired donors, GSE142439 GEO series-matrix reported clock ages).

- Horvath delta mean -3.3964375 years, 6/8 negative.
- Skin & Blood delta mean -1.3475125 years, 6/8 negative.
- Concordant negative in both clocks 4/8.
- Fibroblasts (n=4): Skin & Blood mean -1.068625 years.
- Endothelial (n=4): Skin & Blood mean -1.6264 years.
- Prespecified 80% Skin & Blood negative criterion: **FAIL**, observed 75%.
- Actual Python asserts passed and ZIP integrity verified locally.
- Clock values are precomputed GEO metadata, NOT recalculated from raw IDAT; intervention is not necessarily equivalent to discovery cohort GSE165179. These are not clinical outcomes.
- Safety context: Oct 27 2026 mouse study DOI 10.18632/aging.206431 found tissue-dependent adverse pathway signals; Life Biosciences ER-100 phase 1 NCT07290244 reports three glaucoma patients with 56-day safety observations, not generalized rejuvenation efficacy.

Data source: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE142439
Clinical: https://clinicaltrials.gov/study/NCT07290244
Toxicology: https://pubmed.ncbi.nlm.nih.gov/42954813/

**PASS**: local descriptive calculation and tests. **FAIL**: 80% primary direction criterion on this dataset. **UNVERIFIED**: complete independent therapeutic replication, functional improvement and long-term safety.
