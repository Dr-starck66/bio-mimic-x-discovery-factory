# ASTRA BIO-MIMIC X Ω — vulvovaginal structural-repair evidence gate

Date: 2026-11-23. **Research-only**, 0€ incremental cost, no new scheduled task, no new GitHub Action, no clinical recommendation.

## Falsifiable question

Does an intervention improve structural vaginal epithelial maturation **and barrier function and organized extracellular-matrix architecture** beyond vehicle, rather than mainly changing hydration and patient-reported symptoms? An intervention that improves symptoms without independent tissue recovery is a negative control for the **structural** claim, not a failed treatment.

## Evidence retrieved from primary studies (not reanalyzed here)

| Reference | Design | Useful contribution | Important limitation |
|---|---|---|---|
| Hummelen et al., PLoS ONE 2011; GEO `GSE26761`, PMID 22073175; https://pmc.ncbi.nlm.nih.gov/articles/PMC3206802/ | Human vaginal surface epithelial microarray; 4 dryness vs 6 controls, non-interventional | MMP7 +13.75x, SPINK7 −38.65x, TGM3 −21.86x in original selected-gene table | Tiny unpaired cohort, outcome is dryness/atrophy association; epithelial brush lacks native full-depth ECM; selected p-values are not a preregistered independent gene-set validation |
| Cotreau et al., BMC Medical Genomics 2008, DOI 10.1186/1755-8794-1-27; https://link.springer.com/article/10.1186/1755-8794-1-27 | Biopsies from 19 postmenopausal women before/after 3 months systemic estradiol | 1,668 genes changed ≥1.7-fold at reported p<0.01; longitudinal estrogen response | Pre/post treatment is not proof of lasting, estrogen-independent tissue regeneration; source has no untreated parallel arm reported in this contrast |
| Zelus et al., Advanced Materials 2025, DOI 10.1002/adma.202419977; https://pmc.ncbi.nlm.nih.gov/articles/PMC12463450/ | Ovariectomized rats, acellular vaginal ECM hydrogel vs controls, two weeks | Histological thickness, p63 stem/progenitor marker, Ki67, αSMA; histological measurement method and vehicle/collagen controls | Animal-only, 3–9 animals/group in some analyses; not human efficacy or durable repair after withdrawal |
| 2026 Frontiers in Immunology multi-omics, https://pmc.ncbi.nlm.nih.gov/articles/PMC13375785/; BioProject PRJNA1347381 | Vaginal anterior wall in severe POP: topical estrogen n=6 vs no estrogen n=5 | 116,775 cells, distinct fibroblast groups incl. HAS1+ candidate reparative niche | Only **11 independent patients**, not 116,775; advanced prolapse confounds general GSM; spatial evidence presented from one representative sample per group; non-randomized context; no validated causal intervention on HAS1 |
| GEO `GSE284171` https://usebiotransfer.org/tools/geo-finder/GSE284171/ | Single-cell analysis of vaginal epithelial organoids; 3 samples (hormone conditions) | Differentiation and cell-state hypotheses under estrogen/progesterone | Not independent clinical replication, no whole-wall ECM; study summary says hormones minimally changed proliferation |

## Design for an independent, controlled structural assessment

* Two independent arms (`active`, `vehicle`), paired pre/post within each biological subject; sample sizes are **unique subjects**, never cells, microscopic fields or technical replicates.
* `epithelial_thickness_um` (histology; direction greater), `barrier_teer_ohm_cm2` (standardized organoid/ex-vivo barrier assay; greater), `ecm_architecture_score` (0–1 **blinded** normalized reference score; greater) are **three co-primary structural endpoints**. Define and freeze their units, tissue type, imaging field and assay calibration before data collection.
* `hydration_index` (0–1, greater) and `symptom_score` (0–10, lesser) are **secondary, explicitly non-structural** endpoints. Do not conflate symptom relief with tissue repair.
* A complete and validated tissue-structure study should also measure p63/Ki67 localization, collagen/elastin morphology/turnover and fibrosis, and persistence after treatment withdrawal. Marker abundance alone can increase during fibrosis or inflammation.
* Difference-in-differences is calculated per endpoint: mean(post−pre in active) − mean(post−pre in vehicle), after applying the prespecified desired direction. Two-sided **subject-label permutation** p-values are exact when feasible, otherwise fixed-seed Monte Carlo; 95% percentile bootstrap intervals resample **subjects**, not cells. Holm correction is applied to the three structural endpoints. The gate is exploratory and not a registered clinical diagnostic.
* A structural **signal**, still **not proof of regeneration**, requires directional agreement of all three structural endpoints, each adjusted p<0.05 and each bootstrap interval strictly positive. Zero/negative or unsupported contrasts stay negative or partial. No post hoc threshold fishing.
* The `>=6` subjects per arm preflight is only an **implementation guard** against vanishingly small samples; it is **not a power calculation** or evidence that n=6 is sufficient. Pretrial power and blinded histology calibration are still mandatory.

## Data schema and execution

Each UTF-8 CSV row: `subject_id,arm,timepoint,epithelial_thickness_um,barrier_teer_ohm_cm2,ecm_architecture_score,hydration_index,symptom_score`. Exactly two rows per subject (`pre` / `post`). Arm is `active` or `vehicle`. No imputation; partial or duplicate subject measurements are rejected. A local SHA-256 of the actual input is emitted.

```bash
python -m unittest -v validation/test_vva_repair_gate.py
python validation/vva_repair_gate.py measured_vva_pre_post.csv --source 'GEO_or_trial_ID + independently verified checksum'
```

## Gate states, 23 Nov 2026

- **PASS (implementation only):** local standard-library unit tests against *synthetic* fixtures, including null, hydration-only, positive structural synthetic fixture, missing/duplicate/malformed samples and exact permutation null.
- **PARTIAL (bibliography):** independent clinical and model papers identified with documented denominators and important confounds.
- **UNVERIFIED (biology):** no raw GEO or cohort patient values downloaded in this sandbox; no actual clinical/bioinformatics comparison run; no effect of any intervention independently observed by this project.
- **UNVERIFIED (translation):** no recovery after withdrawal, functional long-term rescue, antifibrotic safety or human efficacy validation.

### Negative controls to retain

1. Hydration and patient symptoms improve; tissue structural endpoints unchanged → **do not call it regeneration**.
2. ECM gene or collagen quantity up without organized physiological architecture/barrier recovery → **do not call it regeneration**.
3. Many single cells but very few patients → do not inflate n/power; aggregate to biological patient.
4. A chronic POP/ovariectomized-rat signal does not automatically generalize to uncomplicated human GSM.
5. Hormone-response genes in cross-sectional dryness data cannot establish an estrogen-independent therapeutic mechanism.

This protocol is a research analysis tool, not advice to administer any vaginal product, hormones, tissue-derived hydrogels or experimental materials.
