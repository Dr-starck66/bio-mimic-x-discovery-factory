# BIO-MIMIC X — Direct BSH/recA replication in Sardinian metagenomes (22 Nov 2026)

## Verified access and cohort mapping (PASS)

- Independent published human cohort: Wu et al., *mSystems* (2019), DOI [10.1128/msystems.00325-19](https://doi.org/10.1128/msystems.00325-19), ENA **PRJEB25514**.
- ENA read metadata was actually queried using [ENA filereport](https://www.ebi.ac.uk/ena/portal/api/filereport?accession=PRJEB25514&result=read_run&fields=run_accession,sample_alias,sample_accession,fastq_ftp,fastq_bytes,fastq_md5,library_layout,instrument_platform&format=tsv).
- File `data/sardinia_2019_ENA_FASTQ_manifest_59.tsv` contains **59 unequivocal run-to-published-sample matches**, **118 FASTQ links and MD5 checksums**, exactly 19 centenarians, 23 elderly, 17 young, no duplicated IDs. ENA sample aliases were normalized by dropping the trailing `_test` only; every alias matched a published dataset S1 sample ID.
- ENA archives these 118 compressed FASTQ objects at **220,446,171,975 bytes (220.45 GB)**, which differs from the SRA estimated storage size (~0.16 TB) due to encoding and compression differences.
- The 2019 published supplemental sheet (Data Set S1) has MetaCyc gene pathways **not** direct KEGG gene-family K01442/recA. Independent 2021 work examined bai operon homologues in Sardinia, but those are **not** direct BSH measurements.
- MGnify v2 `/studies?search=PRJEB25514` returned no matching pre-analyzed study at verification time.

## Molecular targets and primary test — registered before direct-gene analysis

- `K01442`: `cbh`, bile salt hydrolase (BSH), primary target.
- `K03553`: `recA`, reference gene.
- `K03043`: `rpoB`, **unrelated-to-bile-metabolism housekeeping comparator**, not an automatically validated invariant molecular negative control.
- Primary human contrast: centenarians vs elderly; young participants secondary only.
- Primary score: natural log of `(K01442_RPK + 0.01) / (K03553_RPK + 0.01)`, with a predeclared RPK epsilon and sensitivity scan (0.001, 0.01, 0.1, 1.0). RPK is a gene-family abundance unit, **not sequencing counts**. Independently test `K03043/K03553`.
- AUC and two-sided permutation conditioned on sequencing run prefix; report all 59 and **ERR350-only** comparisons. Batch is severely imbalanced: ERR239 (7 C, 1 E, 7 Y), ERR350 (11 C, 22 E, 10 Y), ERR347 (1 C, 0 E, 0 Y).
- This is cross-sectional discrimination only: a statistically significant AUC would **not** establish metabolic prediction, enzymatic activity, or causality.

## Fastest zero-cost evidence route

Request **precomputed per-sample, unstratified KO abundance values** from the two corresponding authors of Wu et al., David J. Kelvin and Ciriaco Carru (contacts verified in article). Specifically require 59 sample IDs, unstratified K01442, K03553 and K03043 in consistent units, method/pipeline versions, KO mapping table version, original run QC and sample covariates. This avoids 220.45 GB of FASTQ download.

If researchers have only HUMAnN2 UniRef90 `genefamilies.tsv`, use an independently documented UniRef90→KO grouping. HUMAnN3/4 KO mappings may be incomplete or differ from the 2026 paper, so **do not** equate them to exactly replicated annotation chemistry. If reprocessing is required, download entire paired FASTQs to a permitted workstation/server with free storage and sufficient compute, verify both MD5 checksums of each run, decontaminate host reads, compute all 59 profiles with one pinned version and functional database, then retain all individual QC logs. **No such compute was performed in this session.**

For HUMAnN3-compatible unstratified KO tables (one `# Gene Family<TAB>sample_RPK` header, then KO ID and RPK values, e.g. after `humann_regroup_table --groups uniref90_ko`), place one file `<run_accession>_ko.tsv` per run. Do not manually replace missing KO rows with zero without an independent completeness and detection-limit check. The program refuses missing rows and nonpositive reference.

```bash
python -m unittest -v tests.test_sardinia_direct_KO_audit
python validation/sardinia_direct_KO_audit.py \
  --manifest data/sardinia_2019_ENA_FASTQ_manifest_59.tsv \
  --ko-dir /path/to/59_real_unstratified_KO_tables \
  --out reports/sardinia_direct_ko_real.json
```

This program deliberately refuses partial sets, implausible numeric measurements, duplicate subjects and low-overlap batch contrasts. You must first obtain the actual KO measurements for these commands to produce a biological association result.

## Negative and failure controls

- Within-run-prefix label permutations; report `ERR350` only separately.
- Unrelated `rpoB` molecular control. If `rpoB/recA` also separates groups strongly, a BSH-specific claim fails.
- Pseudocount sensitivity test, no use of pseudo-replicate age groups as independent subjects.
- An independent **orthogonal** Sardinian cholate degradation pathway signal already had AUC ~0.564 and permutation p ~0.275, non-convincing. This is not a direct K01442 negative control.
- Cross-cohort comparability caveat: 2026 BSH measurements were obtained with the authors' own annotation method. HUMAnN-based KO RPK is a new measurement protocol; direct comparison of AUCs is descriptive until both cohorts are processed identically.

## Status / boundary

- **PASS**: 59/59 source sample mappings and 118 URLs/MD5 from ENA; downloaded-source-derived manifest in isolated PR; direct gene audit code.
- **PASS (synthetic unit tests only)**: locally exercised 59-subject function with normal and fail-closed inputs; no real biological values.
- **UNVERIFIED**: any `K01442`, `K03553`, `K03043` abundance in these 59 Sardinian microbiomes; their AUC/p-value; author-provided KO matrix; full FASTQ reprocessing.
- **UNVERIFIED**: biomarker prediction and validation of BSH gene association in this independent population.
