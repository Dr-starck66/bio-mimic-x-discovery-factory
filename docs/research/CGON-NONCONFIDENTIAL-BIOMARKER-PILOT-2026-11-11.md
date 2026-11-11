# Independent bladder-cancer immunotherapy biomarker evidence audit — non-confidential summary

**BIO-MIMIC X / ASTRA Ω | Public-data research demonstration | 11 November 2026**

## Potential relevance to CG Oncology
Early biomarker hypotheses can look promising in small discovery analyses but fail across different cohorts and clinical outcomes. We are offering an **independent computational feasibility evaluation** that preserves negative results and audits whether apparent tumor / immune signatures survive source, patient, control-group, and multiple-testing checks.

We **do not claim** to be affiliated with CG Oncology, to have analyzed any cretostimogene-treated patient records, or to have discovered a validated predictive marker for its trials.

## Demonstrated, not proposed
- An authentic RNA expression matrix from GSE244895 (35 samples, 12 paired patients), strict SHA-256 source audit, 12 unit tests and cross-language effect/p/q recalculation.
- In a **separate public BCG responder/nonresponder cohort GSE176178**, actual featureCounts matrix for **40 patients** (17 durable responders, 23 others) processed reproducibly, with blinded-to-results preselected two-gene immune signatures, 20,000 global/sex-stratified label permutations per signature and 2,000 bootstrap replicates.
- **Negative evidence:** none of three CD8, chemokine or macrophage RNA proxies was significant after sex-stratified BH correction (all q≈0.978). Outcomes and assays differ between datasets: these cannot be presented as direct cross-cohort replication of the same biomarker endpoint.

Reproducible method + source-provenanced results: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/45

## Narrow proposal for a feasibility discussion
A 20–30-minute scientific scoping call to determine whether an **independent, non-confidential replication and false-discovery audit** could help your research teams. A possible small pilot would be defined around one study question, an approved dataset, pre-specified molecular endpoints, patient-wise splits, baseline models and negative controls; full methodology, failures and reproducibility logs delivered as reviewable artifacts.

**What we would need from a sponsor**: agreement on the scientific question and endpoints; a suitably de-identified, legally shareable dataset with clinical outcomes under relevant governance, or approval to use public data only. We would not handle identifiable patient data or run biological/viral experiments.

**Not offered or asserted:** patient-specific treatment advice, molecular prediction of cretostimogene outcomes, regulatory evidence, validated cancer therapy enhancement, intellectual-property ownership over public data, or commercial valuations.

Contact channel confirmed by the company: **bd@cgoncology.com**. No contact has yet been sent by this research deliverable.
