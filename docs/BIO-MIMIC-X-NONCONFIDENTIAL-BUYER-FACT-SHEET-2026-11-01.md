# BIO-MIMIC X

## Evidence-led gene annotation review

*Research-stage computational software · Technical overview · Updated 2 November 2026*

BIO-MIMIC X is a computational research workflow for situations in which historical gene labels, modern reference assemblies and candidate orthologues do not agree cleanly. It combines source-level sequence comparison with accession tracking and reproducible output records. The intended use is **research data quality review**, not a therapeutic intervention.

**[Open the BIO-MIMIC X research-software overview](https://bio-mimic-x-industrial-evidence-if9m9p.v2.appdeploy.ai/)**

### Where it fits

Research groups often need to revisit public gene annotations created for a different genome build or transcriptome release. Carrying a symbol forward as if it were a confirmed exact locus mapping can affect downstream interpretation.

The current pipeline can help a reviewer:

- Locate reference sequence windows by accession and genomic coordinates.
- Verify source length and sequence fingerprints.
- Compare competing gene candidates at the nucleotide level.
- Produce interpretable alignment records and retain cases where evidence is missing or ambiguous.
- Re-run recorded software checks on public research data.

### A documented axolotl example

Historic axolotl locus `AMEX60DD030069` has conflicting HAND1/HAND2 homology labels. A pinned-source alignment of its **28,911-base** genomic window with the modern NCBI HAND1 candidate produced **28,830 matching bases in 28,853 local alignment columns**, with **23 edit operations**.

The candidate HAND2 window gave a substantially weaker match in its own alignment. Because those modern reference windows have different lengths, the numerical results should not be treated as a calibrated probability or a genome-wide unique-identity determination.

The original, potentially misleading HAND2 assignment was corrected in the project's analysis rather than silently retained.

**Reviewable evidence:**

- [Exact sequences, accessions, coordinates, source SHA-256 values and alignment metrics](../reports/factory/HAND1-HAND2-ALIGNMENT-LATEST.json)
- [Scientific case note](../reports/factory/HAND1-HAND2-ALIGNMENT-EVIDENCE-2026-11-01.md)
- [Reproducible source code](../validation/hand1_hand2_global_alignment.py)
- [Acceptance run 41359105768](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/41359105768)

### What remains to be tested

A broader screening exercise included HAND1/HAND2, PAX6/PAX7, SOX2/SOX3 and SHH/DHH. It documented missing or ambiguous annotations and genomic-window limitations. **One complete, distinct historical-locus comparison** was obtained from that preregistered panel. It therefore cannot support a population-level accuracy estimate or an industrial time-saving claim.

The complete [screening report](../reports/factory/AXOLOTL-PARALOG-PANEL-EVIDENCE-2026-11-02.md) and its [machine-readable results](../reports/factory/AXOLOTL-PARALOG-PANEL-LATEST.json) include the excluded and unresolved cases.

Independent review of the historic gene mapping, larger holdout datasets and a comparison against conventional analysis are necessary to assess general use.

### Independent technical evaluation

The next useful step is to examine a **partner-selected, non-sensitive dataset** with independent reference labels, against the partner's established NCBI/Ensembl/BLAST procedure. A report would compare supported assignments, incorrect assignments, appropriate abstentions, source traceability and review effort where measured.

[Read the technical evaluation outline](BIO-MIMIC-X-INDUSTRIAL-PAID-PILOT-SCOPE-2026-11-02.md).

### Contact

For a non-confidential review or technical discussion: **[dr.starck66@gmail.com](mailto:dr.starck66@gmail.com?subject=BIO-MIMIC%20X%20technical%20evaluation)**.

**Scope:** The software is a research-stage prototype. Neither clinical use nor generalizable performance has been independently validated; ownership and rights to third-party materials require ordinary due diligence. The publicly accessible source files do not, by themselves, establish exclusivity.
