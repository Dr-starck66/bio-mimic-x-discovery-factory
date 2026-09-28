# MICROCLEAN-X Phase 4 — Digital Twin

Phase 4 is a **dimensionless heuristic surrogate**, not a physical simulator and not new experimental evidence.

It explores 25,000 virtual perturbations around the five DOI-backed Phase 3 architectures.

## Virtual dimensions

- adsorbent dose ratio;
- contact-time ratio;
- magnetic-fraction ratio;
- surface-affinity ratio;
- pH offset from the published/reference condition;
- matrix complexity.

The engine deliberately avoids inventing exact synthesis recipes when the literature does not provide enough comparable parameter data.

## Outputs

For every virtual variant it estimates:

- removal proxy;
- uncertainty-adjusted lower-bound removal;
- magnetic-recovery proxy;
- cycle-10 durability proxy;
- relative release-risk proxy;
- complexity proxy;
- adversarial stress-test values;
- research-priority robust score.

## Evidence anchoring

The baseline point for each architecture is calibrated to its published maximum removal value from the Phase 3 evidence registry.

The engine then explores relative perturbations only. As distance from the evidence anchor grows, model uncertainty increases.

## Pareto search

All 25,000 variants are simulated. The top 50 robust candidates from each architecture are then used for a non-dominated Pareto frontier across:

- lower-bound removal;
- stressed magnetic recovery;
- stressed cycle-10 durability;
- release risk;
- complexity.

## Fail-closed rule

No simulation can become:

- a measured result;
- a safety validation;
- an efficacy certification;
- a field-ready recommendation.

Only independent physical measurements can cross that boundary.
