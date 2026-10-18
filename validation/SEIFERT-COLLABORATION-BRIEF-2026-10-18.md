# BIO-MIMIC X — Public collaboration brief for Prof. Ashley W. Seifert
**Date:** 18 October 2026 · **Status:** Independent computational work; prospective biology **not performed**

## Correspondent and project
**Dr Starck** is a web-development-community nickname used by the project's self-taught independent developer, **not a medical or academic title or claim to hold a doctorate**. The developer presents **BIO-MIMIC X**, an independent, publicly inspectable computational project for evidence-linked comparative-regeneration hypothesis screening, reproducible analysis and falsification. This description does **not** claim an academic appointment, medical credentials, peer-reviewed authorship, or institutional endorsement. A fuller personal biography, qualifications and any previous peer-reviewed publication list have **not been independently supplied or verified**; this GitHub repository is a public project record, **not** a substitute for a CV.

Public project: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory

## Public outputs available for independent inspection
1. **Prospectively recorded analysis plan for retrospective datasets** (2026-10-16): design and thresholds for published GEO cohorts **GSE74387** and **GSE113081**. [Prerecorded criteria](PREREG-GEO-2026-10-16.md).
2. **Recorded unfavorable outcome**: the preregistered criterion of replicated expression-response resolution was **not achieved across both cohorts**. The microarray cohort's uncertainty crossed zero. The conclusion is **not independently replicated**, and neither causal biology nor a therapeutic claim follows.
3. **Auditable computational implementation**: source and GitHub Actions job history in the public repository, e.g. [workflow run 39015492410](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/39015492410). On inspection of that run, unit/replay/negative-control and mocked-browser jobs had successful conclusions. A successful software test is **not** biological validation.
4. **Available individual-animal observations and missing molecular pairing**: [animal-level assessment, 2026-10-18](ANIMAL-LEVEL-DATA-ACQUISITION-2026-10-18.md). Four Acomys have documented individual whisker-innervation observations from a third-party published dataset, but **no validated same-animal link to molecular signatures**; cross-study datasets must not be merged as though matched.
5. **Proposed blinded 2×2 experimental design** (not executed): [prospective proposal](PROSPECTIVE-LAB-PROTOCOL-2026-10-16.md).

## Rationale and what is *not* claimed as new
Existing work already supports roles of:
- Macrophage secretions in Acomys regenerative fibroblast behavior: Simkin *et al.*, *Developmental Cell* (2024), DOI: [10.1016/j.devcel.2023.12.017](https://doi.org/10.1016/j.devcel.2023.12.017).
- Acomys-produced ECM in modifying macrophage behavior: *Exploring the Unique Extracellular Matrix Composition of Acomys as a Potential Key to Resisting Fibrosis* (2025), DOI: [10.1021/acsbiomaterials.5c00810](https://doi.org/10.1021/acsbiomaterials.5c00810).
- Proteomic matrisome changes during ear regeneration: *ECM-Focused Proteomic Analysis...* (2025), DOI: [10.1021/acs.jproteome.4c00810](https://doi.org/10.1021/acs.jproteome.4c00810).
- The ERK signaling comparator: *An ERK-dependent molecular switch antagonizes fibrosis and promotes regeneration in spiny mice (Acomys)* (2023), https://pmc.ncbi.nlm.nih.gov/articles/PMC10132760/.

**Novelty of an ECM-by-macrophage-secretome interaction has not been established.** This is not a claim that the interactions have never been tested, nor that they will show synergy.

## Narrowly scoped falsifiable question
**Do an Acomys-derived cell-deposited ECM and Acomys macrophage-conditioned factors show a *non-additive* effect on ACTA2/alpha-SMA-positive myofibroblast differentiation in Mus fibroblasts relative to species-matched controls?**

A blinded, randomized **2×2** compares ECM source (Acomys vs Mus) and conditioned-medium source (Acomys vs Mus). **Primary analysis** is the factorial interaction term in a model accounting for independent biological donors/batches; no conclusion from technical replicates alone. A negative or null interaction is an informative falsification. Predefine a biologically relevant effect threshold, sample size, cell viability controls and robust batch handling with the experimental partner before any data acquisition.

**Important confounders:** ECM stiffness/processing, matrix batch identity, conditioned-medium normalization, cytokine exposure and cell viability must be measured or controlled; alternative ERK-related explanations should not be inferred away. In vitro findings cannot establish in vivo regeneration.

## Specific, low-burden collaboration request
Only **when convenient later in 2026**, a short scientific feasibility assessment by the laboratory or a willing student: is the interaction question already answered in existing data; would the proposed controls be biologically meaningful; and are existing samples/data suitable for a **computational analysis first**? No obligation to provide materials, bench time or unfunded labor is assumed. For any prospective pilot, ethics, resources, data-access agreements, authorship and IP terms would be worked out in advance.

## Evidence status, 18 October 2026
- **PASS (software only):** observed successful repository workflow run 39015492410.
- **FAIL (pre-specified replication gate):** two-cohort replication criterion not met.
- **PARTIAL (data acquisition):** public individual-animal phenotypes exist, but same-animal molecular-to-phenotype pairing not shown.
- **UNVERIFIED:** original biological discovery; mechanism; experimental collaboration; in vitro interaction; animal-level predictive superiority; scientific publication or formal affiliation.

This brief is intended to make the proposal easy to **decline, critique or improve**. It does not request immediate action.
