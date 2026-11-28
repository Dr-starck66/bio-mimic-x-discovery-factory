# BIO-MIMIC X — Comparative cryptobiosis evidence register
Date: 2026-11-28. Research lead: Docteur Stark (requested pseudonym). Retrospective literature comparison; not a new experimental finding or a registered protocol.

## Reuse and scope
Existing README describes ASTRA TARDIGRADE (TARDI-SHIELD/DORMANCY/RECOVERY), Claim Ledger, negative knowledge graph, SHA-256 replay and sequence-supported annotation workflow. TARDI modules are engineering analogies, not biological efficacy evidence. Extend the existing project; no separate repository.

## Source-pinned observations
| System | Observation | Boundary | Primary source |
|---|---|---|---|
| P. kolymaensis | Trehalose increases up to 20-fold with preconditioning; lipid reserves decline. | Mixed developmental stages; two independent experiments, technical replicates not independent cohorts. | https://doi.org/10.1371/journal.pgen.1010798 Fig 4 |
| C. elegans dauer | No significant viability decline reported after 480 days in combined dry/frozen state; dry room-temperature survival declines markedly within ~10 days. | Different conditions, no exact effect size extracted; not mammalian longevity. | same Fig 4E/F |
| Tardigrades | H. dujardini/exemplaris and R. varieornatus exhibit differing transcriptional responses to drying. | Do not pool species or assume universal CAHS response. | https://doi.org/10.1371/journal.pbio.2002266 |
| A. vaga | Rehydration-associated LEA, heat-shock and repair pathways; repair after rehydration, not necessarily prevention of DNA damage. | Association, not causal transfer to mammals. | https://doi.org/10.1186/s12915-023-01807-8 ; https://doi.org/10.1111/jeb.12326 |
| Mammalian cultured cells | Stress-responsive tardigrade protein assemblies and reversible metabolic slowing already reported. | Osmotic stress is not complete drying, tissue preservation or lifespan. Persistent assemblies can compromise recovery. | https://doi.org/10.1002/pro.4941 |
| Negative evidence | CAHS D does not retain extra water in dry systems. | Reject generic water-retention explanation. | https://pmc.ncbi.nlm.nih.gov/articles/PMC10300006/ |
| Negative evidence | Constitutive tardigrade stress proteins have context-dependent costs in C. elegans. | Do not claim universal longevity benefits. | https://pmc.ncbi.nlm.nih.gov/articles/PMC13733966/ |
| Prior art | Trehalose–CAHS synergy already demonstrated. | Not a novel BIO-MIMIC X finding. | https://pmc.ncbi.nlm.nih.gov/articles/PMC9526748/ |

## Acquisition manifest
- Nematode: https://doi.org/10.5281/zenodo.6590382 ; article supplementary S4 Data (survival), S5 Data (trehalose), S6 Data (long-term survival), S7 Data (brood size). Original data bytes not acquired.
- Tardigrade: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE94295 and https://www.ncbi.nlm.nih.gov/sra/?term=SRP098585 (desiccation); GSE168917 is bleomycin, an orthogonal stress dataset, not desiccation.
- Rotifer: https://www.ncbi.nlm.nih.gov/bioproject/PRJNA962496 (SAMN34396008–SAMN34396072; 65 accession identifiers, not necessarily 65 independent replicates). Also PRJEB23547 for desiccation-tolerant and nondesiccating species genome comparisons.
- Mammalian cell comparator: https://doi.org/10.1002/pro.4941 (source measurements and independent donor metadata to request/verify).
All raw matrices and binary integrity UNVERIFIED. Direct HTTPS attempt to PLOS supplementary endpoint failed DNS in local execution environment; GEO page challenge encountered. No successful download claimed.

## Prospective test concept (not preregistered)
Compare phase-aware protection and recovery against a phase-agnostic baseline using independent studies; distinguish dry, frozen and osmotic stress; map conserved pathways separately from lineage-specific functional analogues. No cross-species pooling of raw expression or pseudoreplication. Primary conceptual endpoint is recovery of biological function after stress, alongside survival; metabolic suppression alone is not success. Record adverse effects and contradictory results, and compare against conventional stress-response models. Estimate uncertainty by independent biological unit; keep held-out study/species separate; require complete provenance and outcome data before inferential analysis. Numerical acceptance thresholds to be frozen before held-out data inspection. Mammalian validation requires independent donor/cell contexts, suitable controls and qualified collaborators. Not a treatment, intervention protocol, or claim of anti-aging efficacy.

## Status
PASS: repository reuse and primary literature/accession identification.
PARTIAL: descriptive comparison and acquisition manifest.
FAIL: direct download attempt (DNS).
UNVERIFIED: raw matrices, hashes, independent cohort structure, comparative inference and mammalian efficacy.
Cost: 0 EUR. No publication or OSF registration performed.
