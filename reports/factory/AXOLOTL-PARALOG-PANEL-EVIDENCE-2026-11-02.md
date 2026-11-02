# BIO-MIMIC X — Four-family historic-to-modern paralog panel

**Executed:** 2026-11-02 (Europe/Paris) · **Protocol:** predeclared before runtime results · **Status:** PARTIAL_SCREENED_NONREPRESENTATIVE  
**Primary execution:** [GitHub Actions #41364628804](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/41364628804)  
**Data receipt:** [AXOLOTL-PARALOG-PANEL-LATEST.json](AXOLOTL-PARALOG-PANEL-LATEST.json), SHA-256 `3e55d4d1957d53eb71300eaac5c5c6f8729198174d1737476dc461fb70d80cb3`.

## Rationale and method

The earlier HAND1/HAND2 false attribution was **one case** and could not justify general industrial accuracy or estimated ROI. This protocol preregistered eight gene-symbol targets in four paralog families **before inspecting their available references**:

- HAND1/HAND2
- PAX6/PAX7
- SOX2/SOX3
- SHH/DHH

The program used source-hashed historical **AmexT_v47/AmexG_v6 GTF**, official old chromosome-to-GenBank mapping, taxon-exact NCBI modern annotations on `GCF_040938575.1`, and NCBI FASTA nucleotide windows. Inclusion required a **unique historical gene feature**, window between **250 and 40,000 bp**, one exact modern RefSeq genomic locus, and distinct old locus identity (no counting multiple symbols on one AMEX ID as independent samples).

For any eligible pair, Edlib HW alignments in both orientations measured normalized edit counts and matching bases. The tool **did not** infer exact old-to-new gene identity, biological efficacy, industrial error rate or clinical value.

## Actual results — negative cases retained

| Predeclared target | Real result | Meaning |
|---|---|---|
| HAND1 vs HAND2 | **1 real distinct locus successfully aligned**. Strongly favors HAND1: 99.9203% of local alignment columns versus 52.6625% for HAND2. | Local sequence-based candidate screening; exact genome-wide identity remains UNVERIFIED |
| HAND2 historical tag | Same `AMEX60DD030069` record contains both HAND1 [nr] and HAND2 [hs] | **Excluded as duplicate**; not a second independent success |
| PAX6 | Historical gene `AMEX60DD007993` is 46,586 bp | **Excluded** by the prespecified 40,000-bp cap; no opportunistic threshold adjustment |
| PAX7 | Multiple or no unique historical models | **Excluded**; no verified unique locus |
| SOX2 | Multiple or no unique historical models | **Excluded** |
| SOX3 | Historical model `AMEX60DD037395` 2,076 bp present, but no unique exact-modern NCBI SOX3 annotation returned | **Unresolved reference failure**; not silently imputed |
| SHH | Multiple or no unique historical models | **Excluded** |
| DHH | Multiple or no unique historical models | **Excluded** |

**Correct denominators:** eight symbol targets were predeclared, but these are **not eight independent known-identity samples**. Two cases passed the preflight inclusion criteria; **one** completed a paired current-reference alignment and **one** failed on a missing/ambiguous official SOX3 source. This is not a measured recall, precision, or 50% accuracy rate.

## What this proves, and what it does not

**PASS (software execution):** The real-data preflight extracted historic gene models from a pinned GTF, enforced bounds and taxon-specific NCBI references, did not count the HAND1/HAND2 duplicate twice, and retained exclusion reasons and source hashes. The actual comparison of the single eligible HAND1 locus reproduced the original striking alignment difference.

**PARTIAL (scientific breadth):** The protocol exposed an important coverage weakness: old gene-name tags and modern NCBI references are insufficient for these other preregistered genes under the current 40-kb limit. This test **does not** demonstrate generalizable performance beyond HAND1.

**UNVERIFIED:** Independent curator gene-ID confirmation, whole-genome reciprocal best-hit, true false-positive reduction on a blinded multi-gene cohort, analyst-hours savings, acquisition price, willing buyer, commercial ROI and therapeutic efficacy.

## Measured next research obstacle — not a sale promise

A commercially defensible technical evaluation needs an externally selected held-out gene panel with stable, curator-confirmed cross-assembly truth labels and a conventional BLAST/NCBI baseline. Expanding a length cap after seeing a failure would constitute a **new protocol version**, not retroactively validating this run. Further tests should focus on exon-/protein-aware alignment of long axolotl genes and alternative verified references for SOX3 without silently assuming a one-to-one match. Curator confirmation from AxoBase and the paper author was requested via verified Gmail sent receipts on 2026-11-01; no human reply was observed at this run.

**Commercial restriction:** Do not claim a cross-gene benchmark PASS or a measured saving in an industrial sales pitch from this panel.
