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

## Commercial proof correction (2026-11-01)

The local-only commercial evidence registry formerly marked any `PAID_PILOT` or `RESEARCH_CONTRACT` entry with a source ID or 64-character hash as `PASS`. That allowed **false-positive commercial commitments** without confirming a real payer, signature, contract or inbound response.

The new gate is **fail-closed**: local registry entries are screened for metadata but remain `UNVERIFIED` until an independently authenticated, provider-backed verification adapter exists and has been executed. The free-text fields `paid=true`, `signature_verified=true`, a Gmail `SENT` ID or a fake SHA-256 cannot by themselves promote a sale. `verified_entries=0` is intentional in the absence of connected verification evidence.

This is a correction to the code's evidence standard, not a loss of a previously established sale: no customer order, payment or authenticated LOI had been recorded. The buyer-facing [non-confidential fact sheet](BIO-MIMIC-X-NONCONFIDENTIAL-BUYER-FACT-SHEET-2026-11-01.md) focuses on measured science-software behavior and preserves negative results. Do not confuse it with a binding commercial offer.

## Evidence boundary

The package is not a medical claim, company valuation, patentability opinion, freedom-to-operate opinion or proof of clinical efficacy.
