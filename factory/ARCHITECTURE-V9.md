# BIO-MIMIC X V9 — Scientific Reasoning Layer

V9 extends the validated discovery factory without replacing the evidence, taxonomy, Human Bridge, or reliability gates.

## Runtime path

SUPPORTED claim
→ Morpheus adversarial audit
→ Ω-CAUSAL counterfactual plan
→ Human Bridge context
→ Ω Hypothesis Engine
→ Ω Debate / Contradiction Engine
→ Ω Experiment Planner
→ Ω Scientific Reasoning dossier
→ Ω Scientific Discovery Memory

## Epistemic rules

- Hypotheses are always stored as `HYPOTHESIS`, never as established facts.
- Debate scores are evidence-prioritization heuristics, never probabilities of truth.
- Experiment plans are `PROPOSED_NOT_EXECUTED`.
- Animal-to-human bridges do not imply efficacy.
- Every V9 dossier carries `clinical_efficacy_claim=false`.
- Every dossier is deterministically fingerprinted with SHA-256.
- Hypothesis lineage is persisted separately from the factual claim ledger.

## Active V9 bricks

1. `scientific-reasoning` — orchestrated reasoning dossier.
2. `hypothesis-engine` — primary + competing falsifiable hypotheses.
3. `debate-engine` — adversarial objections and counter-tests.
4. `experiment-planner` — conceptual falsification plans with kill criteria.
5. `scientific-memory` — hypothesis lineage and reasoning-change events.

These are active bricks under the repository's `NO_DECORATIVE_BRICKS` policy and must appear in the runtime usage ledger.

## Validation

The V9 gate requires:

- Python compilation of all new modules and the control plane;
- the full repository unit-test suite;
- the brick audit;
- registry uniqueness;
- explicit `usage.use(...)` integration for all five V9 bricks.

A separate full-cycle smoke test executes the actual control plane against the committed organization state without pushing that ephemeral state back to `main`.
