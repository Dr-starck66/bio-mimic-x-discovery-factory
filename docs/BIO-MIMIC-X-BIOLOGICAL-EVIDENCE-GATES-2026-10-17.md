# BIO-MIMIC X — Independent biological evidence gates (audit 2026-10-17)

**Status: SOFTWARE PASS / ORIGINAL PREREGISTERED GEO HYPOTHESIS FAIL / NEW BIOLOGICAL VALIDATION UNVERIFIED.**

This file records a public-evidence feasibility audit. It is not a claimed experiment, independent replication, protocol acceptance, a change to the preregistration, or a laboratory PASS. No new GitHub Actions run, paid service, animal experiment or external contact is authorized by this document.

## A. Locked historical result (never rewrite)

- Frozen original protocol: [validation/PREREG-GEO-2026-10-16.md](../validation/PREREG-GEO-2026-10-16.md).
- Software key-selection bug in `prepare()` fixed in [commit 5d2cb5a](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/commit/5d2cb5aa4eccf9845a152e72e559439800fde4b8): for `kind="array"`, use the `Acomys` group, not the `Mus` group.
- CI run [38961739243](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/38961739243): workflow **success**, script outcome **FAIL_PRE_REGISTERED_HYPOTHESIS** (not an experiment success).
- GSE74387 delta = +0.10063677; sample bootstrap 95% CI [-0.07249126, +0.19307711]: **FAIL** because interval includes zero.
- GSE113081 delta = +0.12341074; sample bootstrap 95% CI [+0.02945860, +0.18971694]: **PASS in this cohort only**.
- Global two-cohort criterion: **FAIL**. See [machine-readable record](../reports/independent-data-validation/2026-10-16.json). Never change thresholds, repeat until favourable, exclude GSE74387 after seeing results, or relabel this historical result PASS.

## B. External datasets — suitability for DIFFERENT biological questions

This assessment is based on GEO series/sample descriptions and published abstracts; no new numerical expression-data analysis is claimed.

| External source | Independently collected material and design | Re-use classification | Why |
| --- | --- | --- | --- |
| [GSE71761](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE71761) | 4-mm **ear** biopsy, Acomys and Mus, D0/5/10/15/20, 3 animals/species/time, 3 sequencing runs per animal | **NOT_COMPARABLE** to original dorsal D0/7/14 endpoint; possible exploratory ear comparison | Triplicate runs **do not** multiply the biological n; anatomical site and time grid differ |
| [GSE159938](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE159938), within [GSE159939](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE159939) | Bulk RNA-seq **dorsal epidermis and dermis**, Acomys and Mus, 25 sample-level files; genotype/time/region differ and must be parsed per GSM (e.g. Acomys dermis PWD14 and PWD21) | **UNVERIFIED_COMPARABILITY** for stratified mechanistic exploratory work; **NOT an automatic direct replication** | Tissue layers, sampling stages, genotypes and region must be matched at sample level; do not mix WT with KO or epidermis with dermis |
| [GSE224433](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE224433) | Published scRNA-seq and perturbations of ERK/FGF/ErbB in Acomys/Mus, including inhibitor and growth-factor conditions | **PUBLISHED_CAUSAL_PRIOR_ART** and possible reanalysis, **NOT an original BIO-MIMIC X experimental result** | Original authors report effects of ERK inhibition and ectopic activation on regenerative outcomes |
| [GSE182141](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182141) | Ear scRNA-seq, Mus/Acomys days 0,3,5,10,15; macrophage-focused study | **PUBLISHED_PRIOR_ART / EXPLORATORY** | Existing publications already support some macrophage-induced fibroblast matrix-turnover effects; assess novelty first |

Evidence:
- GSE71761 NCBI GEO accession (ear and biological sample design): https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE71761
- GSE159938 NCBI GEO series, sample GSM4850938 (Acomys dermis day14) and GSM4850939 (day21): https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4850938 ; https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4850939
- GSE224433 GEO summary of published ERK perturbations: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE224433
- GSE182141 GEO summary: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE182141
- Yoon et al. 2020 proteomics: https://doi.org/10.1038/s41598-019-56823-y — Mus D14 proteome can approach baseline while scar formation has occurred, so generalized 'return to day0' is not a valid direct scar-free regeneration endpoint.

## C. Required no-false-PASS scientific workflow

### Gate 1 — sample-level data audit (NOT YET EXECUTED)
For any candidate series download deposited metadata and expression matrices, hash inputs, record retrieval date and sample-level accession IDs, species, tissue layer, wound location, post-wound day, region, genotype, donor, and treatment. Verify species/ortholog mapping, missing values, assay measurement scales and biological independence. Refuse pseudo-replication of cells, sequencing runs or technical assays as independent animals. If conditions cannot be matched, emit `NOT_COMPARABLE`, not a positive result.

### Gate 2 — exploratory reanalysis (NOT YET EXECUTED)
Only after Gate 1, test a prespecified **distinct** mechanistic signature involving ECM remodeling + immune state and potentially ERK, with contrasts normalized within species, multiple-testing correction, donor-level or sample-level uncertainty, data provenance, negative controls, full contradictory results and a held-out dataset. Any signature inspired by previously inspected source studies must be explicitly labeled **exploratory/hypothesis generating**, not a confirmatory independent PASS. Published perturbation results are prior art and cannot establish novelty of BIO-MIMIC X.

### Gate 3 — new independent controlled experiment (UNVERIFIED; requires laboratory)
See [existing proposed prospective protocol](../validation/PROSPECTIVE-LAB-PROTOCOL-2026-10-16.md): 2x2 factorial Mus/Acomys ECM and macrophage-conditioned medium, with fibroblast activation and an interaction term. Before acquiring fresh observations, an independent qualified lab must agree on material availability, identity validation, institutional approvals, anti-contamination checks, independent biological donors, statistical power, randomization, blinding, batch handling, exclusion rules and minimum meaningful effect size. **A negative interaction on fibroblast ACTA2 alone does not establish in-vivo scar-free regeneration.** An additional independently assessed structural/fibrosis or functional endpoint would be needed to substantiate that larger claim.

### Gate 4 — proof and attribution
- `PASS_SOFTWARE`: replay and source integrity reproducible, code/CI evidence.
- `FAIL_ORIGINAL_PREREG`: preserved for GSE74387/GSE113081; cannot be 'fixed' by a new hypothesis.
- `PASS_NEW_INDEPENDENT_EXPERIMENT`: **only** if a previously locked, explicitly distinct primary criterion succeeds in authentic independent lab measurements with valid controls, biological units, identifiable provenance and independent analysis.
- `UNVERIFIED_NOVELTY`, `UNVERIFIED_CAUSAL`, `UNVERIFIED_CLINICAL`, `UNVERIFIED_IP`: remain until justified by dedicated evidence. Prior publications confirm their authors' findings, not a new independent BIO-MIMIC X discovery.
- A wet-lab in-vitro cellular assay can support a mechanism but does not, by itself, justify claims of effective scar-free tissue repair or therapy.

## Decision as of 2026-10-17

**Do not report a biological PASS.** Best next action without new expenditure: finish metadata comparability review on GSE159938 and critically review prior art before locking a genuinely new primary biological endpoint. Direct experimental proof requires a collaborating qualified lab; partnership, funding and execution are currently **UNVERIFIED**.

Issue tracker: [#12](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/issues/12).
