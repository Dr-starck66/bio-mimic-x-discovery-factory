# BIO-MIMIC X — ASTRA Ω DrugAge Longevity Sex Audit

Empirical exploratory evidence package, **not a clinical/antiaging product**.

Source: HAGR DrugAge Build 5 third-party snapshot (CC BY 3.0, attributed in `docs/`). Real-life-span reported percent changes, 3423 rows, 333 matched Female/Male comparisons, 101 PubMed identifiers. Source CSV is vendored in the GitHub PR under `data/drugage_build5_snapshot.csv` so that a complete run needs only the Python 3 standard library, not a paid provider or API.

To rerun after extracting the GitHub repository source:

```
cd research/longevity_sex_audit
PYTHONPATH=. python -m unittest discover -s tests -p 'test_drugage_sex_study_audit.py' -v
python analysis/drugage_sex_study_audit.py data/drugage_build5_snapshot.csv --output reports/recalculated.json
```

The independently derived `reports/DRUGAGE_SEX_AUDIT_20261118.json` used 20k study-level sign permutations and 10k study-level bootstrap samples in JavaScript. The provided Python standard-library implementation uses an independent seeded PRNG and is expected to produce similar, not binary-equal Monte-Carlo p-values. Study-level dependence, selected database and multiple hypotheses are material limitations. No new human lifespan intervention or quantum biological mechanism was demonstrated.