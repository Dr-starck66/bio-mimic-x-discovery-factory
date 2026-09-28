# MICROCLEAN-X

MICROCLEAN-X is a fail-closed research campaign inside BIO-MIMIC X for magnetic microplastic remediation.

## Baseline

Primary reference:

- Jeonghyo Kim, Apabrita Mallick, Su-Jin Song, Martin Pumera.
- *Magnetic MXene-based microrobots for soil microplastics removal*.
- NPG Asia Materials, 2026.
- DOI: 10.1038/s41427-026-00670-7

The seed records the reported laboratory removal values used as the benchmark: 94.0% polystyrene and 89.2% PET in water; 80.6% polystyrene and 72.2% PET in the soil model.

## Objective

Search for magnetically recoverable alternatives to the nickel-bearing reference while refusing to equate "nickel-free" with "safe".

Initial hypotheses:

1. Ti3C2Tx + Fe3O4
2. Ti3C2Tx + gamma-Fe2O3
3. Ti3C2Tx + chitosan-stabilized Fe3O4
4. Ti3C2Tx + silica-coated Fe3O4

These are research hypotheses, not validated replacements.

## Mandatory gates

A hypothesis cannot be promoted until it has:

- direct microplastic-removal evidence;
- quantitative magnetic-recovery mass balance;
- secondary-pollution / particle-release measurements;
- repeated-cycle evidence;
- an ecotoxicity comparison against matched controls.

The engine intentionally reports zero promoted alternatives at seed stage. A non-zero promotion without evidence is treated as a regression.

## Automated outputs

`python factory/microclean_x.py` writes:

- `reports/microclean-x/latest.json`
- `reports/microclean-x/LATEST.md`
- `public/data/microclean-x/latest.json`

The GitHub Action reruns the evidence gate weekly and whenever the campaign code or evidence seed changes.

## Interpretation rule

The research-priority score answers only: **what should be tested next?**

It is not a safety score, an efficacy score, a field-readiness score, or evidence that a material works for microplastics.
