# ASTRA MEDICAL Ω — Sequential Hypothesis Simulator v0.1

**Research-only. Synthetic structured cases only. No medical device, patient diagnosis, clinical advice, treatment or triage.**

Designed to live alongside the existing `tools/astra_medical_claim_audit/` audit, literature, SciFact benchmark and negative controls. It does **not** replace or claim to reproduce Microsoft MAI-DxO or the SDBench metrics.

Uses fixed hypotheses and *experimenter-supplied* prior probabilities and test likelihoods. A sequential controller ranks candidate tests by expected reduction in Shannon entropy divided by `(1 + artificial_test_cost)`, asks the synthetic harness for results, updates Bayesian probabilities and classifies **only** beyond a configured stop threshold; otherwise it abstains. Values are invented for synthetic algorithm validation and are not calibrated against healthcare data. The truth label is used only after classification to compute test metrics. Pure Python standard library, no LLM and no network.

## Execute

```bash
python3 -m unittest discover -s tests -v
python3 sequential_diagnosis.py examples/synthetic_suite.json --out examples/synthetic_report.json
```

The report exposes case-level trace, hypothetical test costs, accuracy among decided, abstention/coverage, source SHA-256, and `clinical_validation=UNVERIFIED`. Do not compare accuracy on these easy invented cases to Microsoft's clinical benchmark. Controls include no-information abstention, reversal on negative results, posterior arithmetic, expensive test avoidance, data leakage checks, invalid probabilities and explicit rejection of identifying fields.

Future formal comparison requires using the **official** Microsoft SDBench harness, with its licensed data policy, fixed judge/gatekeeper, matching agent interface, a legitimate compatible inference endpoint, and separate evaluation. No such comparison is claimed here.

Official reference: https://github.com/microsoft/sdbench (MIT license; external dependency not bundled). Research paper DOI: https://doi.org/10.1126/science.aeh7930.