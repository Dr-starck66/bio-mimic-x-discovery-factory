# BIO-MIMIC X V10 — ECOSYSTEM-MIMIC

ECOSYSTEM-MIMIC adds an ecological self-organization analysis layer to the existing V9 scientific discovery factory. It is designed for longitudinal observations of a real ecosystem (pond, wetland, mesocosm, restoration plot, etc.).

## What it computes

- taxon richness;
- Shannon diversity and Pielou evenness;
- Bray-Curtis community turnover between observations;
- colonization and local-loss events;
- temporal stability of total abundance using inverse coefficient of variation when estimable;
- perturbation resistance/recovery descriptors from an explicit pre-event baseline;
- a taxon cofluctuation network;
- falsifiable ecological hypotheses.

## Epistemic gates

ECOSYSTEM-MIMIC is deliberately conservative:

- correlation never becomes an interaction claim;
- observational time series never become a causal claim;
- recovery values are descriptive metrics, not probabilities;
- sampling effort and detectability remain explicit limitations;
- fewer than two valid observations returns `INSUFFICIENT_DATA`;
- synthetic data are permitted only in tests, never in the production evidence file.

## Input contract

Production input lives at `data/ecosystem_mimic_observations.json`.

Each observation may contain:

```json
{
  "time": "2026-09-26T08:00:00+02:00",
  "taxa": {"taxon A": 12, "taxon B": 4},
  "environment": {"water_temp_c": 18.2, "ph": 7.4},
  "perturbation": null
}
```

A `perturbation` label marks a real observed event. Recovery is only estimated when at least two prior observations exist.

## Scientific basis

The implementation follows standard ecological practice rather than inventing a proprietary "truth score":

- temporal stability is represented with inverse coefficient of variation when the time series supports it;
- perturbation response is separated into resistance and recovery descriptors;
- Bray-Curtis dissimilarity describes compositional turnover;
- covariance edges are explicitly labeled as cofluctuation only.

Useful background:
- Nature 563, 109–112 (2018), *Biodiversity increases and decreases ecosystem stability*.
- Nature (2026), *Predicting temporal stability and resilience from resistance and recovery*.

## Integration

The brick is registered under `NO_DECORATIVE_BRICKS` and executed by `factory/control_plane.py` every factory cycle. With no production observations it reports `PARTIAL / INSUFFICIENT_DATA` instead of manufacturing ecological evidence.

The factory cycle persists the result under `ecosystem_mimic` and records `ecosystem_timepoints_analyzed` in the brick-usage ledger.
