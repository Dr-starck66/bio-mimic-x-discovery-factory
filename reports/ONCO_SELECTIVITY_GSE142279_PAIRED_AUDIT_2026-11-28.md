# ASTRA ONCO-SELECTIVITY Ω — GSE142279 paired exploratory audit
Date: 2026-11-28. Status: PARTIAL for biological selectivity, PASS for mirror blob integrity and computational checks. Retrospective exploratory analysis, not a preregistered or therapeutic experiment.
## Provenance
- Primary record: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE142279 — Peking University Cancer Hospital, 20 matched tumor/adjacent non-tumor pairs.
- Mirror pinned commit: https://github.com/DevD-BIO/crc-bulk-rnaseq-deseq2/tree/b17b2524fd6d493e981fec05fe660592cb626ae0
- Matrix: data_raw/GSE142279_raw_counts_GRCh38.p13_NCBI.tsv; blob cbb132092c337d52fd33039509e57d5a4cecdf46. Standard file fetch returned empty content, blob fetch returned 5,083,836 ASCII bytes. Independently computed SHA-1 over Git header and received bytes exactly matched this blob. SHA-1 implementation checked against abc reference a9993e364706816aba3e25717850c26c9cd0d89d. This verifies mirror object, NOT agreement with original NCBI download. Direct network access failed DNS.
- Metadata: metadata/sample_metadata_backup.csv; blob d47f5378307422de8571e966f858a0c9cc062e0f; 40 GSM records aligned to 40 matrix columns; RC1–RC6, LC1–LC6, RE1–RE8, normal/tumor per donor; GEO series confirms design and sample names.
## Executed QC
39,376 unique GeneIDs, 40 unique sample IDs, 20 pairs, 1,575,040 nonnegative integer values, zero invalid rows, duplicates or dimension mismatches. Column totals 35,458,630–51,037,365.
## Executed comparison
Compute counts per million per sample using all genes. Retain CPM >=1 in >=20/40 samples, resulting in 16,078 tested genes. Within each donor compute log2(CPM_tumor+0.5) - log2(CPM_normal+0.5). Two-sided exact binomial sign test, excluding ties; Benjamini-Hochberg FDR 0.05 across tested genes; median paired log2 difference as descriptive effect. Results: 6,366 BH discoveries, 1,894 median >=1, 1,045 median <=-1; 515 positive in all 20 donors, 272 negative in all 20, 3,559 directional agreement >=18/20. These are exploratory bulk expression associations, not causal findings. CPM composition bias and tissue heterogeneity remain.
## Negative control executed
Swap tumor/normal labels in alternating pairs (10 of 20); same filter and tests: 16,078 tested, 0 BH discoveries, 0 genes with >=18/20 directional agreement. One deterministic label-swap sanity check, not an exhaustive permutation calibration.
## Gates
- Mirror recovery and content SHA verification: PASS. Independent NCBI original binary comparison: UNVERIFIED.
- Donor-matched bulk comparison: PASS as executed; scientific replication: UNVERIFIED.
- Adjacent non-tumor is not a healthy independent donor or regenerative epithelial population; cell type composition and field effects confound.
- Candidate ranking / efficacy / normal-cell preservation: UNVERIFIED. No drug or treatment claim.
- Next: acquire full unselected cell-level counts plus donor/cell labels for GSE132465 (23 tumor, 10 matched mucosa) and independent GSE144735; confirm source independence and hold out entire donors/cohort; additionally obtain non-cancer donors and paired functional response data before making claims of selectivity.
- No new paid service used.
