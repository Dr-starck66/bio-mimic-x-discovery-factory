# MICROCLEAN-X Phase 5 — Experiment Selector

Phase 5 converts Digital Twin uncertainty into a short physical-validation queue.

It does **not** execute experiments.

## Selection objective

Choose three experiments that reduce different uncertainties rather than spending all resources on the same question.

Candidate experiment families:

- cross-polymer + real-matrix generalization;
- magnetic recovery + secondary-release mass balance;
- ten-cycle durability;
- matched ecotoxicity/leachate screen;
- pH × matrix operating-window map;
- champion-versus-reference reproducibility replay.

## Expected-information-gain proxy

The selector computes a heuristic proxy from:

- mean Digital Twin uncertainty;
- disagreement among architectures;
- release-risk burden;
- magnetic-recovery gaps;
- durability gaps;
- missing real-matrix evidence;
- missing reuse evidence;
- candidate coverage;
- relative experimental burden.

This is not formal Shannon information gain and is not a measured quantity.

## Diversity constraint

The final three experiments must have distinct primary axes.

That prevents three superficially high-scoring experiments from all testing the same weakness.

## Fail-closed rule

Every selected experiment is stored as `PROPOSED_NOT_EXECUTED`.

The report hard-codes:

- physical experiments executed = 0;
- new measured results = 0;
- safety established = false.

Only real measurements can update these states.
