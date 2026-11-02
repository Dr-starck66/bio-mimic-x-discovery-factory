# BIO-MIMIC X — Technical evaluation outline

*Non-confidential · Research-stage software · 2 November 2026*

## Research question

Legacy gene annotations are frequently used outside the assembly and transcript models in which they were created. In a new reference, the original identifier may resolve to multiple candidates or to no clear match at all.

BIO-MIMIC X is a computational workflow for examining those cases with genomic sequence evidence, recording provenance and keeping unresolved mappings visible.

## Existing demonstration

One documented axolotl case concerns historical locus `AMEX60DD030069`, annotated with both HAND1 and HAND2 homology tags. When the original nucleotide window was compared with modern NCBI gene windows, the HAND1 candidate produced **28,830 matching bases across 28,853 local alignment columns**, with **23 edit operations**.

This result supports closer examination of the original HAND2 attribution. It does **not** establish a unique cross-assembly gene identity.

- [Source accessions, fixed genomic ranges, SHA-256 receipts and alignments](../reports/factory/HAND1-HAND2-ALIGNMENT-LATEST.json)
- [Methods and interpretation](../reports/factory/HAND1-HAND2-ALIGNMENT-EVIDENCE-2026-11-01.md)
- [Executable code and tests](../validation/hand1_hand2_global_alignment.py)

## Proposed independent assessment

The purpose of an initial evaluation is to establish whether the workflow improves the review of ambiguous identifiers *on an independent dataset*, compared with an established mapping procedure.

| Workstream | Suggested method | Evidence to return |
| --- | --- | --- |
| Input selection | Prospective partner selects a small, permitted set of legacy gene annotations and independent reference mappings | Dataset manifest and permitted use |
| Baseline | Document the partner's normal NCBI/Ensembl/BLAST-based review procedure | Same-case baseline outcomes |
| Sequence review | Run the existing source-verified candidate comparison on the identical cases | Exact-source receipts, alignment records and abstentions |
| Evaluation | Compare incorrect assignments, supported assignments, unresolved cases and analyst review effort, if timed | A case-level report with denominators, not only favorable examples |
| Reproducibility | Provide scripts, dependency versions and representative negative cases | Re-runnable technical record |

The dataset size, baseline, security requirements, work schedule and commercial terms would be agreed before starting. The first discussion can use **public or non-sensitive data**; no confidential research materials are requested on this page.

## Current boundaries

The documented finding is an alignment of **candidate gene windows**, not a genome-wide reciprocal mapping. A separate four-family screen identified data-availability and reference-mapping limitations and did not produce a representative accuracy estimate. The findings are available in the [screening report](../reports/factory/AXOLOTL-PARALOG-PANEL-EVIDENCE-2026-11-02.md). Independent biological validation and measured industrial efficiency gains remain open questions.

## Request a technical conversation

For computational biology, data-platform and R&D teams interested in evaluating historical gene-identity checks: **[contact BIO-MIMIC X](mailto:dr.starck66@gmail.com?subject=BIO-MIMIC%20X%20technical%20evaluation)**.

The public materials describe the software and its current technical evidence. They are not a clinical, regulatory or efficacy claim.
