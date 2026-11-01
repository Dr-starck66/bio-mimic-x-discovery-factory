# BIO-MIMIC X — Real NCBI HAND1/HAND2 nucleotide alignment

**Measured:** 2026-11-01 | **Software execution:** PASS | **Historical locus identity:** PARTIAL | **Independent annotation:** UNVERIFIED

## Reproducible execution

- [Public GitHub Actions #41359105768](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/41359105768) — scientific and Chromium acceptance jobs **SUCCESS**.
- 188 project unit tests PASS; after binary Edlib 1.3.9.post1 installation, 8 alignment-specific tests PASS.
- [Machine-readable receipt](HAND1-HAND2-ALIGNMENT-LATEST.json), canonical SHA-256 `6a6e4f7e2d4c951bbe7c8327767b174a3f603bbd545e0c8ffd1462b881c08427`.
- [Exact reproducible code](../../validation/hand1_hand2_global_alignment.py), [negative tests](../../tests/test_hand1_hand2_global_alignment.py).
- All three source FASTA sequences retrieved from NCBI EFetch using explicit 1-based genomic coordinates, strict base-count and pre-existing independent SHA-256 locks. The raw nucleotides are not republished; source URLs and hashes are included in the receipt.

## Result: old axolotl locus favors HAND1, not HAND2

Historical axolotl `AMEX60DD030069`, `CM010932.2:632140538-632169448` (28 911 nt, GenBank assembly `GCA_002915635.3`), originally annotated `HAND1 [nr]|HAND2 [hs]`.

| Alignment | Modern reference / species gene | Query length | Matching bases | Differences (Edlib) | Matching fraction of aligned columns | Strand |
|---|---|---:|---:|---:|---:|---|
| Local semiglobal HW (entire modern query to old window) | **HAND1** `NC_090926.1:348891291-348920140`, NCBI Gene `138582569` | 28 850 | **28 830** | **23** (6 substitutions, 14 insertions, 3 deletions) | **99.9203%** | + |
| Local semiglobal HW (entire modern query to old window) | **HAND2** `NC_090937.1:910028725-910032936`, NCBI Gene `138516365` | 4 212 | 2 334 | 2 098 | **52.6625%** | + |
| Supplementary global NW (query vs whole historical window) | HAND1 | 28 850 | 28 830 | 95 (6 substitutions, 89 inserted/deleted bases) | 99.6716% | + |

The local HAND1 aligner places the modern region at 0-based coordinates `63..28901` within the old locus window (inclusive). This is a **near-exact local sequence match**, and strongly corroborates a misassignment of the old gene to HAND2. Both input orientation choices were measured; their scores and CIGAR counts are retained in JSON.

**Methodology and caveats:** Local alignments compare gene windows with substantially unequal lengths for HAND1 (28.85kb) and HAND2 (4.21kb); the percentages are descriptive within each alignment, **not a calibrated probability, whole-genome hit significance or clinical prediction**. Edlib uses edit distance. Further reciprocal genome-wide search, gene family/paralog analysis, transcript/exon models and independent curator review are required for a **definitive historical accession mapping**. The modern HAND2 ↔ human HAND2 NCBI orthology does NOT justify assigning the old `AMEX60DD030069` counts to HAND2.

The earlier positive HAND2 assignment in the exploratory transcriptomics has been transparently withdrawn; original files and negative controls retained. See [historical corrigendum](HAND2-HAND1-SEQUENCE-CORRIGENDUM-2026-11-01.md). Human limb regeneration, clinical efficacy, ownership, and 1 M€ valuation remain **UNVERIFIED**.

## Commercial interpretation (without fabricated ROI)

This is one documented **gene-identity quality-control case**, not a validated multi-dataset advantage or a published industry benchmark. An independent industrial evaluation should measure false assignment rates and analyst minutes saved on a preregistered, multi-gene validation set against a competent conventional baseline. No economic saving estimate is yet validated.
