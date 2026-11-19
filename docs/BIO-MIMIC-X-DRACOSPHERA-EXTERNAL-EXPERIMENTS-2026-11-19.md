# BIO-MIMIC X — experimental evidence gate (19 Nov 2026)

**Scope: public experimental measurements + computational cross-study comparison. This does NOT constitute a new wet-lab experiment by ASTRA.**

## Primary experimental observations

1. Natural `Chaetoderma shenloong` multilamellar `dracosphera` (diameter ~12 µm, >20 lipid layers) documented by Li et al., *Nature Communications* 2026, [DOI 10.1038/s41467-026-78965-0](https://doi.org/10.1038/s41467-026-78965-0). Oxygen barrier was hypothesized, not established by native organelle oxygen flux.
2. Living bacteria cultured and monitored in **giant unilamellar lipid vesicles** (Basicles), including riboflavin production from ~0.13 to ~0.29 fluorescence AU/min after inducer, [DOI 10.1021/acsami.9b12169](https://doi.org/10.1021/acsami.9b12169). This does **not** recreate the 20-layer organelle.
3. Direct oxygen efflux measured on artificial liposomes: P(O2)=0.03 cm/s at **0% cholesterol**, P(O2)=0.2 cm/s at **45 mol% cholesterol** (35 °C). Increasing cholesterol increased experimental permeability **6.67-fold** in this system — important negative control against oversimplified barriers. Source: [DOI 10.1007/s00018-021-03974-9](https://doi.org/10.1007/s00018-021-03974-9). These are NOT native `dracosphera` values.
4. Relevant independent raw-data deposits: [PRJNA1206974](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1206974), [MTBLS15431](https://www.ebi.ac.uk/metabolights/MTBLS15431), [Figshare processed expression 33335040](https://doi.org/10.6084/m9.figshare.33335040).

## Results verified locally outside GitHub Actions

- Previous analytical model archive re-executed: **12/12 deterministic tests PASS**.
- Added published-measurement evidence gate with eight falsification/provenance tests: **20/20 combined tests PASS** in local container.
- Programmatic published aggregate numbers only: `P45/P0=6.6666667`; `riboflavin slope ratio=0.29/0.13=2.2307692`.
- These ratios are reanalyses of published values, **not** experimental measurements made by ASTRA.
- Original 20-layer spherical model is still **conditional** on membrane material, structure and inner sink, not a biological measurement.
- At steady state without consumption, a passive barrier **does not** sustain an O2 concentration gradient. A legitimate laboratory test must measure *time-dependent* O2 equilibration first; long-lived gradients require a verified interior sink.

## Exact experiments not performed

**Artificial reconstruction:** cryo-EM validated 0, 1, 5, 20 membrane layers, one chemistry and size distribution, empty vesicles before nonpathogenic authorized bacterial model. Oxygen transfer pulse response, leakage controls, viability and traceable nutrient uptake, multiple independent preparation days, blinded image scoring. Reject if lamellae absent, permeability unchanged, apparent gradient is a sensor artifact, or oxygen restriction destroys bacterial viability.

**Regeneration/rejuvenation:** after abiotic oxygen proof, a separate **sterile** mammalian-cell experiment, *no bacteria*; normoxia vs oxygen-matched hypoxia vs one-layer vs twenty-layer membranes, donor randomization, viability, cell identity, functional regeneration assay, multiple independent DNA methylation clocks and replication. If no effect beyond oxygen-matched control, no specific BIO-MIMIC X claim. DNA age shifts without functional or identity controls are insufficient.

## Evidence status

| Claim | Status |
| --- | --- |
| Natural dracosphera observed in published microscopy | PASS — external literature |
| Bacterial growth inside artificial unilamellar lipid vesicles | PASS — external literature |
| Oxygen permeability of some lipid bilayers measured | PASS — external literature |
| ASTRA reproducible analytical model and published-data cross-comparison | PASS — local computational tests |
| 20-layer living artificial organelle rebuilt by ASTRA | **FAIL — NOT EXECUTED** |
| Native dracosphera O2 gradients directly measured by ASTRA | **FAIL — NO PHYSICAL DATA** |
| Tissue regeneration and epigenetic rejuvenation by artificial organelle | **FAIL — NOT EXECUTED** |

This branch deliberately keeps failed/no-data evidence visible. No biomedical claim, no deployment, no new paid infrastructure. Experimental partnership is required for the remaining biological gates.


## 2026-11-19 — Recorded collaboration outreach (not a laboratory result)

Two proposals were sent from the project owner's previously used scientific correspondence account; Gmail confirmed SENT status and the messages were subsequently found under sent mail. No experiment has started, and delivery to recipients / acknowledgment / in-kind funding / collaboration acceptance remain unconfirmed.

1. Original *Nature Communications* corresponding-author team: Jian-Wen Qiu (HKBU, primary recipient), Pei-Yuan Qian (HKUST, cc), Jin Sun (OUC, cc). Proposed exchange of original membrane data and a blinded 0/1/5/20-lamellae oxygen-equilibration experiment.
2. Laboratoire Charles Coulomb, Université de Montpellier / CNRS (official secretariat): requested referral to the physics of living and biomimetic systems research team, emphasizing existing giant-vesicle microfluidics expertise and no financial commitment.

Do not include private email IDs or assert replies from scientific partners. The project next requires a named principal investigator and access to measured oxygen-kinetic traces, verified multilamellar microscopy, controls, preparation batch IDs and all negative results, under the host laboratory's ethics/biosafety governance. The existing computation package remains analysis only.
