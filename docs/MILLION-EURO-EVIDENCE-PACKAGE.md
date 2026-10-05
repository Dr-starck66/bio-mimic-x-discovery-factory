# BIO-MIMIC X — Million-Euro Evidence Package

This layer converts the research factory into an investor / acquirer diligence artifact without inventing valuation proof.

## What it does

- audits the current program portfolio;
- rejects non-species text fragments and unverified taxa from the investor package;
- quarantines known gene/entity extraction noise;
- selects the strongest flagship from a curated external-evidence registry;
- emits a deterministic SHA-256 evidence package;
- produces a due-diligence brief, external-validation brief and IP/risk register;
- keeps company-valuation readiness separate from a cash-exit claim.

## Current flagship logic

The first curated flagship is **Acomys cahirinus**.

The thesis is deliberately narrower than “IL-10 causes regeneration.” The package treats Acomys regeneration as a coordinated extracellular-matrix + immune-state phenomenon and records IL10 only as a translation anchor.

This design is falsifiable: if a single-node perturbation fully explains the phenotype, the combined-program thesis should be rejected.

## Hard gates

A million-euro cash-exit claim is blocked while any of these remain unresolved:

- no independent external validation of a BIO-MIMIC X output;
- no causal experimental result for the flagship hypothesis;
- no professional patentability / freedom-to-operate review;
- no verified commercial traction.

The generated status therefore remains **PARTIAL** until evidence changes.

## Run

```bash
python factory/million_euro_evidence.py
python -m unittest tests.test_million_euro_evidence -v
```

Generated files:

- `reports/million-euro-evidence/latest.json`
- `reports/million-euro-evidence/DUE-DILIGENCE.md`
- `reports/million-euro-evidence/EXTERNAL-VALIDATION-BRIEF.md`
- `reports/million-euro-evidence/IP-RISK-REGISTER.md`
- `public/data/million-euro-evidence/latest.json`

## Evidence boundary

The package is not a medical claim, company valuation, patentability opinion, freedom-to-operate opinion or proof of clinical efficacy.
