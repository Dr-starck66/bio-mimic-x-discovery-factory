# MICROCLEAN-X Live Evidence Radar

This module upgrades MICROCLEAN-X from a static evidence seed to an autonomous public-literature radar.

## Live sources

- Crossref REST API
- Europe PMC REST API

No paid API key is required.

## What it does

Every daily run searches multiple microplastic-remediation queries, merges duplicate papers by DOI/PMID, detects magnetic-remediation context, extracts material signals, and builds an evidence queue.

Initial tracked material families include:

- Fe3O4 / magnetite
- gamma-Fe2O3 / maghemite
- chitosan
- silica
- MXenes
- biochar
- alginate
- nanocellulose
- metal-organic frameworks
- graphene oxide
- ferrites

## Fail-closed policy

A material can become `REVIEW_QUEUE` only when at least two independent literature records support a microplastic context and at least one also contains magnetic-remediation context.

`REVIEW_QUEUE` means only **worth deeper review**.

The live radar never turns a literature hit into:

- validated efficacy;
- environmental safety;
- field readiness;
- automatic promotion into the MICROCLEAN-X experimental candidate set.

That promotion remains controlled by the stricter MICROCLEAN-X evidence gate.

## Outputs

- `state/microclean-x/live_latest.json`
- `reports/microclean-x/live_latest.json`
- `reports/microclean-x/LIVE-LATEST.md`
- `public/data/microclean-x/live_latest.json`

The workflow runs daily and can also be launched manually.
