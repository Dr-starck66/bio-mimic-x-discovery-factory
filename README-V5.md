# BIO-MIMIC X V5 — Autonomous Research Lab

## What is autonomous now

Once this repository is on GitHub and Actions are enabled, `.github/workflows/daily-lab.yml`
runs the laboratory every day at **04:17 Europe/Paris**.

The run:
1. selects research tracks using an exploration/exploitation policy;
2. queries Europe PMC;
3. detects previously unknown taxon names, mechanisms and gene symbols;
4. checks a sample against Europe PMC annotations;
5. verifies candidate species against Ensembl when possible;
6. updates the cross-species knowledge graph;
7. runs Evidence/Skeptic/Arbiter scoring;
8. attaches Morpheus falsification flags;
9. updates the learning policy from actual yield;
10. creates a SHA-256 replay fingerprint;
11. saves a daily Markdown report;
12. commits the new state back into the repository.

No paid model or paid API is required.

## Self-improvement: what it means

V5 **does not rewrite its own source code**.
It improves its *research policy*:
- underexplored tracks are automatically explored;
- productive tracks receive more weight;
- query terms are reweighted from measured discovery yield;
- evidence accumulates rather than being discarded;
- negative knowledge prevents repeated dead ends.

This is measurable learning, not a marketing label.

## Zero-cost cloud path

GitHub Actions can execute the runner. The included workflow uses standard Ubuntu runners,
no GPU and Python's standard library only.

For maximum defensibility, keep the research repository private and expose only a sanitized
dashboard/data snapshot separately.

## Files

- `lab/runner.py` — autonomous research cycle
- `lab/tracks.json` — research programs
- `state/knowledge_graph.json` — cumulative graph
- `state/learning.json` — learned search policy
- `state/negative_knowledge.json` — failed hypotheses
- `state/runs.json` — history
- `reports/` — daily reports
- `.github/workflows/daily-lab.yml` — daily scheduler
- `public/` — optional public dashboard
- `assets/VALUATION-READINESS.md` — objective asset-readiness gates

## Scientific guardrail

This system prioritizes hypotheses. It does not diagnose, prescribe, or establish human efficacy.
