# BIO-MIMIC X V6 — Autonomous Scientific Organization

V6 upgrades the V5 autonomous lab into a daily multi-laboratory research organization.

## Autonomous specialist labs
- ONCO-X
- REGEN-X
- NEURO-X
- IMMUNO-X
- LONGEVITY-X
- METABOLIC-X
- PRESERVE-X

## Daily flow
Parallel specialist labs → evidence/skeptic/arbiter → committee merge → cross-lab convergence → challenge assignment → 100 internal research-credit allocation → organization memory → daily report → SHA-256 replay.

## What is real
- The labs run as separate GitHub Actions matrix jobs.
- Their outputs are immutable artifacts for the committee step.
- The committee merges evidence and allocates priorities deterministically.
- Cross-lab support increases priority.
- Challenge density and weak provenance reduce priority.
- State and decisions persist across days.

## What is not claimed
- Research credits are not money.
- Committee scores are not clinical-success probabilities.
- The software does not prove efficacy in humans.
- A $1M valuation is a target, not a guarantee.

## Main files
- `organization/labs.json`
- `organization/lab_worker.py`
- `organization/committee.py`
- `.github/workflows/scientific-organization.yml`
- `public/organization.html`
- `organization/ARCHITECTURE-V6.md`
- `PUBLISH-V6-ONECLICK.ps1`
