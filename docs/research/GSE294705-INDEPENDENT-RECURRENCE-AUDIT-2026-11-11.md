# BIO-MIMIC X — GSE294705 third cohort / recurrence benchmark (11 Nov 2026)

**Status: reproducible computational PASS; fixed immune-proxy association FAIL.**

## What this cohort can and cannot test

Public NCBI GEO accession [GSE294705](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE294705) is a separate 94-patient NMIBC *recurrence* validation cohort from Baek et al. (*BMC Medicine*, 2026, doi:10.1186/s12916-026-04745-8). The pre-declared public label is **"recurrence(2>=): Yes/No"**, not durable BCG response and not cretostimogene efficacy.

**Do not interpret this as directly replicating the earlier GSE176178 or GSE244895 estimands.** It is an external, non-identical clinical endpoint test of the same previously selected three fixed RNA-expression proxy pairs.

## Actual data and execution

- NCBI series raw count file `GSE294705_CBNUH_n94_NMIBC_counts.txt.gz`: **5,371,960 compressed bytes**, SHA-256 `f5ca68e03d0547cc9faad8940f75181640f1d99dbdbc6119faf85da8c49729ce`.
- GEO sample series matrix gzip SHA-256: `15c06e2554466f65f43cbf38238eeaaf089cd650440b9b2f18dcf76c958e8212`.
- **94 exactly matched unique samples; 63,241 gene-count rows** (94 count columns + Ensembl ID).
- **16** patients with at least two recurrences; **78** without; labels not reinterpreted as no recurrence vs one recurrence or exact duration.
- Metadata: **76 male, 18 female**; 78 T1, 15 Ta, 1 CIS; 82 high, 11 low, 1 NA grade. Full covariate adjustment not established.
- Exact sample-ID mapping: source count table `807_URO_RNA_1` versus GEO title `NMIBC_807_URO_RNA_1`, single documented prefix removal, complete 94/94 unique alignment.
- Exact HGNC/Ensembl mapping for six genes independently checked via public MyGene.info gene query:
`CD8A ENSG00000153563`; `CD8B ENSG00000172116`; `CXCL9 ENSG00000138755`; `CXCL10 ENSG00000169245`; `CD68 ENSG00000129226`; `CD163 ENSG00000177575`. These rows are present in the matrix.
- Existing authorized DUALITY X V0.3 ECO project VM (Floot) executed a standalone Node.js pipeline with built-in libraries only: **6/6 deterministic local self-tests PASS**. **No billing, new server, cron, intervention or GitHub Actions launched**.
- Code SHA-256: `87242b71330aeda73700c5de88ab6552fbe53605c7566fe7e2288b9053ba9c51`; 20,000 global and **sex+stage-stratified permutations** per signature, 2,000 bootstrap draws, fixed seed 20261111. Exact numerical results from a second full execution were saved.

## Falsifiable results

Effects are group means for recurrence≥2 **Yes minus No**, log2(1+CPM) from total gene counts per specimen; signature = unweighted mean of two genes. Descriptive in-sample AUCs do not prove prospective prediction.

| Immune proxy | Δ mean | In-sample AUC | Sex+stage-stratified permutation p | BH q (three proxies) |
|---|---:|---:|---:|---:|
| CD8A + CD8B | -0.325009 | 0.36538 | 0.08660 | **0.25979** |
| CD68 + CD163 | -0.288928 | 0.41106 | 0.20454 | **0.30681** |
| CXCL9 + CXCL10 | -0.278574 | 0.44511 | 0.50342 | **0.50342** |

**None passes FDR 5%.** All unadjusted 95% bootstrap confidence intervals include zero. The direction of the CD8 effect is not proof of a protective mechanism or validated predictor. An EORTC recurrence score's *descriptive* AUC in this sample is 0.385 (higher-risk direction as supplied in the metadata); it is not a fair independent clinical benchmark, because definitions, follow-up and risk calibration differ. Do not claim a new clinical product.

## Reproducibility and scope

- Machine report: [gse294705_recurrence_2026-11-11.json](../../reports/cretostimogene/gse294705_recurrence_2026-11-11.json).
- Reusable source: [gse294705_nmibc_recurrence_external_benchmark.mjs](../../validation/gse294705_nmibc_recurrence_external_benchmark.mjs).
- Related separate analysis: [GSE176178](GSE176178-EXTERNAL-RESPONSE-VALIDATION-2026-11-11.md).
- Literature: [Baek et al., BMC Med (2026)](https://doi.org/10.1186/s12916-026-04745-8).

**PASS:** data acquisition; all source SHA-256, row and sample gates; correct gene identifiers; code self-tests; actual 94-sample computation and report persistence.

**FAIL (candidate biomarker):** clinical recurrence association q<0.05 for any fixed two-gene proxy.

**UNVERIFIED:** original published 75-gene HfRI model replication (needs exact 75 published weights and normalization), external clinical validation of any newly proposed marker, applicability to BCG durable response or cretostimogene outcomes.

Preserve this null result and dataset mismatch; do not optimize on these 94 outcomes and then report those same 94 patients as independent validation.
