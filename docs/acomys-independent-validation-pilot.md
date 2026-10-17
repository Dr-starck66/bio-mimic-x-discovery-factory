# BIO-MIMIC X — Acomys independent validation pilot (evidence gate)

**Status: DESIGN_READY / EXPERIMENT_UNVERIFIED** (2026-10-17). This document is a proposed independent study, **not a claim of novel biology, experimental success, or external lab approval**. No new paid service or scheduled task is authorized.

## Falsifiable question and prior work
The existing flagship proposes that joint changes in extracellular matrix (ECM) and immune state, rather than IL10 alone, are associated with and may be necessary for scar-free repair in *Acomys cahirinus*. Compare with *Mus musculus*. The published regeneration phenotype itself is already known; any claim of novelty must be about an independently reproducible **new predictive or causal signature**, not about discovering Acomys regeneration.

Primary evidence from the project's literature registry:
- PMID:29892004, doi:10.1038/s41598-018-27178-7 (skeletal muscle regeneration, 2018).
- PMID:31141508, doi:10.1371/journal.pone.0216228 (dermal wound transcriptomics, 2019).
- PMID:32849592, doi:10.3389/fimmu.2020.01697 (immune-state comparison, 2020).
- PMID:40534468, doi:10.1021/acs.jproteome.4c00810 (independent ECM-focused proteomics, 2025).
- PMID:40883787, doi:10.1186/s41232-025-00391-4 (lung injury, 2025).

Externally discoverable datasets:
- **GSE113081**: *Acomys* and *Mus* dorsal wound transcriptomics at day 0, 7, 14; N=4 per species/time point, with one Mus control sample excluded for QC by the depositors. This is original study data, NOT an independent replication.
- **GSE159939**: separate wound-induced follicle-regeneration series involving *Acomys* and *Mus*; check subseries, animal tissue, times and assay/platform comparability *before* selecting any independent test subset.
- 2025 ECM-focused proteomics, doi:10.1021/acs.jproteome.4c00810: published experimental findings; supplementary Tables S1–S7 may be used for independent computational scrutiny, not counted as new validation by BIO-MIMIC X.

## Stage A — External data reanalysis, zero-cost
1. Register dataset accession, sample metadata, excluded samples, source URL, retrieval date, downloaded file checksum and analysis code/versions **before opening outcomes**. Do not use synthetic inputs to pass a live-data gate.
2. Predefine injury site, tissue, timepoint strata, ortholog mapping and the ECM vs immune signature from the training source; lock selected genes and direction before independent evaluation.
3. Replicate first within GSE113081 only as a **software/data reproducibility** test (sample QC, count normalization, matched *Acomys*/*Mus* contrasts, multiple-testing correction, effect-size uncertainty, biological replicates).
4. Hold out GSE159939 and any usable 2025 proteomics data. Mark **NOT_COMPARABLE** rather than substituting incompatible tissue/cell type, timepoint or platform. Use sample-level validation; prohibit pooling correlated technical replicates or leaking test outcomes into marker selection.
5. Report results including negative and conflicting effects; no positive result on public previously published data satisfies independent prospective experimental validation.

Pre-specified dry-lab decision rule: require concordant signed ECM **and** immune effects on at least two comparable external studies, with uncertainty and multiple-testing corrections reported; if studies are not comparable or data unavailable, classify UNVERIFIED/NOT_COMPARABLE. This rule will itself require prospective calibration and a locked gene list before a confirmatory analysis can PASS.

## Stage B — Independent prospective biological experiment (needs external authorized lab)
- Request an independent institutional lab to agree to a written protocol, ethical approvals, sample-size justification, blinding, randomization and independent record of preregistration **before any wet-lab work**.
- Prespecify matched wound models and readouts for histological fibrosis/regeneration, ECM composition, immune-cell states, timepoint/tissue and cage/sex/age covariates.
- Compare sham/vehicle and independent perturbations of one immune candidate, one ECM candidate and a joint condition, with a qualified lab handling all experimental interventions and animal welfare.
- Specify primary effect size, failure threshold, and whether single-node perturbation explains the complete phenotype. Include a perturbation-failure negative control and correction for multiplicity.
- Independent analyst must receive deidentified data, raw measurement provenance, method, uncertainty and negative findings. No fabricated or self-authored review counts as independent.

**Kill conditions**: no reproducible joint signal; a single-node model fully explains the phenotype; tissue/timepoint/species confounds invalidate comparisons; no independently verified biological result; adverse or null data contradict the claimed mechanism.

## External scientific contacts for *requesting* a study, not accepted partners
- Prof. Kerstin Bartscherer, Osnabrück University — Acomys/skin regeneration project, https://www.regenerate-it.eu/research/project-7/ ; contact is published there.
- Dr. Willeke F. Daamen, Radboud University Medical Center — matrisomal regeneration overview, doi:10.1039/D3BM00835E.
- Prof. Kirk C. Hansen, University of Colorado — 2025 ECM proteomics corresponding author (source author; **not independent** of that publication).

A collaboration is NOT verified unless an actual written acceptance and attributable external evidence is preserved. No email has been sent by generating this document.

## Release gates — keep independent
| Gate | As of 2026-10-17 | Required evidence |
|---|---|---|
| Reproducible software replay | PASS (GitHub workflow 39007588412) | Logs/artifacts with matching SHA |
| Chromium UI tests | PASS (same workflow) | Real browser CI, mocked providers separately marked |
| External cohort data reanalysis | UNVERIFIED | Downloaded and independently analyzed real GEO material with QA |
| Prospective independent wet-lab validation | UNVERIFIED | Preregistered experiment + signed independent data |
| Original causal discovery | UNVERIFIED | Results beyond prior art, defensible causal evidence |
| Sale for EUR 1M | UNVERIFIED | Authentic binding offer or completed transaction |

**Anti-false-PASS:** A published external paper confirming known *Acomys* biology is prior art, not proof that BIO-MIMIC X made an original discovery. A clinician's opinion is not wet-lab validation. A platform demo is not deployment on a real accessible production hostname.
