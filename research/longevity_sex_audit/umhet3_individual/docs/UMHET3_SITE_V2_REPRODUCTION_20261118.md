# BIO-MIMIC X — UM-HET3 site heterogeneity v2 (2026-11-18)

This is an **exploratory, observational** and zero-cost reproducibility package, not a causal aging mechanism, clinical result, or novel longevity intervention.

**Verified sources:** DannyArends/UM-HET3, pinned original GitHub blob `4b23a79950182df8564af63803b481179f6e8d17` and 6,438-animal derived CSV blob `dea9bfa0086228b40e450c0e235f252c83eea528`. Original paper: DOI 10.1038/s41586-026-10407-9; pre-existing sex×site phenomenon: Cheng 2019 DOI 10.1111/acel.12905.

## Reproduction (after cloning the BIO-MIMIC X research branch)

```bash
cd research/longevity_sex_audit/umhet3_individual
python -m unittest discover -s tests -p 'test_umhet3_decomposition_v2.py' -v
python analysis/umhet3_decomposition_v2.py data/UMHET3_6438_PHENOTYPES.csv --out reports/UMHET3_DECOMPOSITION_PYTHON_REPLAY.json
```

The Python implementation uses only standard library. The synthetic test suite was run locally with **15/15 PASS**. The actual 6,438-animal analysis and 2,200/1,500 bootstrap replicates were **executed in a JavaScript connector runtime**, and the resulting JSON evidence is committed in `reports/` on the branch. The whole-cohort Python replay could not be independently run in the local container because the full CSV was not mounted, so the **full Python replay status remains UNVERIFIED**. Different bootstrap RNGs won't yield byte-for-byte equivalent intervals.

## Empirical results

- Five common cohorts: 2004, 2005, 2006, 2007, 2009; **n=5242**.
- Standardized sex gap F−M (days): Jackson **+116.93**, Michigan **+38.19**, San Antonio **+77.62**.
- UM vs JL standardized mean lifespan in males **+109.05 days**, females **+30.32 days**, i.e. sex-gap contrast **−78.74 days**. Naive bootstrap 95% for JL−UM sex-gap difference: **[51.91,105.04]**.
- Controls-only F−M gaps: JL **+106.06**, UM **+33.79**, UT **+128.60**.
- Earlier cohorts 2004–06: F−M JL **106.21**, UM **22.28**, UT **85.48**; later 2007,2009: JL **131.18**, UM **59.35**, UT **67.17**.
- **Negative evidence**: 2007 UT−UM gap was **−45.04 days**, reversing the assumption of universally higher UT sex gap.
- Body mass comparison (males surviving to 183d, BW6 observed, cohorts 2005,2006,2009): nonparametric 6g bin, >=3 each site×year×treatment×BW bin, **17 common-support strata, n=1415**. On the same sample the UM−JL contrast is **+87.50 days before** BW standardization, and **+27.43 days after**, naive 95% CI **[−4.32,+57.90]**. This is **68.6% descriptive attenuation, not mediation**.
- **Falsification/sensitivity**: shift the 6-g bin boundary by 3g and residual UM−JL becomes **+38.31 days**, with different overlap sample; using 5/8/10g and shifted boundaries yields residual **+27.4 to +53.4 days** for pooled treatment code. Controls-only result ranges **−10.5 to +35.0 days** depending on bin specification.
- The published research in 2019 and 2026 already reported sex×site differences and body mass association. This work is a *reanalysis and sensitivity audit*, not an original biological finding.

## Data integrity warning

The 2026 Nature Methods text reports **3401 females and 3037 males**, whereas the author's `Figures/Figure1.R` uses `sex==1` as male, and the published phenotype file contains **3401 `sex==1`** and **3037 `sex==0`**. The figure code and recorded sex counts appear inconsistent with the prose. The numeric code is interpreted as in Figure1.R here; **this discrepancy must be resolved with source animal-level metadata before any sex-specific scientific publication**. This is a candidate reproducibility/documentation discrepancy, not a confirmed publication error.

## Hard limits

- No individual right-censoring flag in the derived phenotype CSV: no Kaplan-Meier, Cox, or hazard claims from this extract.
- No cage/litter or intervention-specific drug information; treatment=1 pools individually non-significant interventions, not one drug arm.
- BW6 conditions on age 183-day survival and weight measurement, causing selection/collider risk.
- Causal explanation for the Michigan site gap and new antiaging targets **UNVERIFIED**.
- 24,296-mouse GeneNetwork cohort **not** fully downloaded and analyzed here; only pinned genotyped 6,438 subset.