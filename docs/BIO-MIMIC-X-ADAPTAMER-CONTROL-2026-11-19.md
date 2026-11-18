# BIO-MIMIC X — Adaptamer/ADAR regulator (computational preclinical concept)

**Date:** 2026-11-19. **Scope:** non-clinical software. No genetic construct or treatment is supplied.

**Published basis:** Bryant et al., *Molecular Cell* (2026), DOI [10.1016/j.molcel.2026.09.037](https://doi.org/10.1016/j.molcel.2026.09.037). Drug binding to an RNA aptamer can allow endogenous ADAR editing to change a STOP codon, enabling translation. Demonstrated in human cell lines and FGF21-expressing mice; **not** in HAND1/HAND2-based regenerative therapies. The authors disclosed a patent filing.

## Module

`validation/adaptamer_control.py` simulates a switch with dose-response (Hill), basal leak, separate drug and protein half-lives, a switch/ADAR negative control and an ON/withdrawal trace. All model parameters are arbitrary, uncalibrated research placeholders; simulation proves **no** efficacy, regenerative activity or safety.

`evaluate_measurements` accepts independent *measured* data from CSV with columns:

`laboratory,study_doi,arm,replicate,protein,viability_pct,offtarget_fraction`

Accepted `arm`: `off`, `on`, `withdrawal`, `switch_negative`. Units of protein must be consistent across arms; missing washout/negative arms cause abstention, and mixed measurement scales must be rejected by the reviewer. These are minimum inputs, not a sufficient trial design. At least two distinct labs, two study DOIs and three biological replicates per arm **within each laboratory** are required for the *illustrative numerical gate*. Every laboratory is evaluated separately (no cross-laboratory pooling) to prevent a positive pooled result masking a negative laboratory. A reviewer must separately verify DOI-to-lab provenance, raw measurements, drug washout pharmacokinetics, sample identity and cellular context. Current thresholds (2x induction, 80% reversal, >=90% viability, <=1% off-target) are placeholders **not clinical acceptance criteria**; off-target cannot be inferred from viability alone.

```bash
python -m unittest tests.test_adaptamer_control -v
python validation/adaptamer_control.py --output /tmp/adaptamer-report.json
python validation/adaptamer_control.py --external-csv measurements.csv
```

## Independent evidence requirements

- **Response:** independently obtained dose-response points and controls for each specified cell type; estimate effect size with uncertainty, not a synthetic Hill-curve fit alone.
- **Adverse effects:** genuine, measured cell viability, bystander RNA editing/off-target effects and cell-state changes with vehicle, switch-negative and ADAR controls; any adverse outcome remains in the report.
- **Reversibility:** repeat ON/OFF cycles over biologically relevant time, measure drug clearance and actual protein decline; distinguish persistent protein from continued transcription.
- **Regeneration:** prespecified morphological, functional and transcriptomic outcomes in a validated regeneration model, compared with standard care and a constitutive-expression comparator. Existing axolotl HAND1/HAND2 locus ambiguity must be resolved before using those target labels as verified inputs.

**Status:** code and tests may PASS locally; independent biological and clinical validation **UNVERIFIED** pending actual independently generated data. No lab results invented and no claimed medical efficacy. New experimental application would require biosafety, ethical approval and legal/IP review.