# ASTRA BIO-MIMIC X — Dracosphere oxygen transport (2026-11-19)

**Scientific status:** PASS deterministic local physics tests (12/12). **NOT verified:** real dracosphere oxygen permeability; artificial dracosphere synthesis; regeneration; rejuvenation.

## Source observation and crucial distinction

Li et al., Nature Communications (2026), doi:10.1038/s41467-026-78965-0, describe ~12 µm dracospheres in *Chaetoderma shenloong*, surrounded by >20 lamellae, with reported multilayer thickness 77–1060 nm (506 nm mean). The research group's explanation of preferential host oxygen utilization is a **hypothesis**, not a directly measured radial oxygen gradient. The reported peak of 1,629 symbionts refers to a host cell, not a count per dracosphere. Direct living-animal oxygen measurements and isotopic nutrient transfer measurements remain absent.

## Quantitative test actually run

Stationary spherical diffusion, resistance in series for water plus N idealized membrane interfaces. Model outer radius 6 µm, inner radius 5.5 µm, D_water=2×10^-9 m²/s (assumption), lipid bilayer thickness 4 nm (assumption, geometric fit only). No parameters were fitted to the species.

Membrane permeability P values represent **other materials and measurement approaches**, never the native organelle: 0.2 cm/s (a cholesterol-dependent experimentally measured value, PMID 34694438), 12 and 15 cm/s (molecular dynamics POPC/cholesterol ranges, PMID 33966190), 100 cm/s (high-transport sensitivity case).

| P per membrane (cm/s) | J20/J0, idealized upper-limit oxygen supply | Reduction |
| ---: | ---: | ---: |
| 0.2 | 0.024390 | 97.56% |
| 12 | 0.600001 | 40.00% |
| 15 | 0.652175 | 34.78% |
| 100 | 0.925926 | 7.41% |

These are **scenario calculations**, not experimental estimates of oxygen transport in the animal.

The model also includes an optional *arbitrary*, dimensionless first-order bacterial sink (Da=1); this is **not** an estimate of bacterial respiration. Membranes are added as interfaces without subtracting lipid thickness from aqueous path length. This is a deliberately simplified passive barrier model and cannot show preferential host oxygen consumption by itself.

A reported local wall thickness of 77 nm is incompatible with 20 assumed 4 nm bilayers; the model marks this case `GEOMETRY_INVALID` instead of showing invalid numerical results.

## Test and reproduce, free and independent of GitHub Actions

```bash
python -m unittest discover -s tests -p 'test_dracosphere.py' -v
python validation/dracosphere_model.py --output dracosphere_results.json
```

Verified on the locally reproduced repository file layout: **12/12 PASS** (baseline zero membranes, near-infinite permeability negative control, monotonicity with N and P, geometry rejection, no-sink case, spherical-to-planar limit, input validity, report integrity). No GitHub Actions or remote production job claims.

## Biology / artificial reconstruction / anti-age boundary

Known methods make multilamellar vesicles, and synthetic giant vesicles have been used to encapsulate bacteria: https://pmc.ncbi.nlm.nih.gov/articles/PMC8955843/ ; https://doi.org/10.1002/advs.202307103 . **Neither demonstrates the dracosphere's structure and symbiotic function have been recreated.** In-vitro confirmation requires multilayer structure imaging, independent oxygen-gradient measurements, membrane chemistry, bacterial survival, nutrients and paired unilamellar controls.

Hypoxia is not automatically regenerative: low oxygen can create necrotic cores in engineered tissues (doi:10.1038/s41467-024-48719-x). Any regenerative claim needs tissue models with matching oxygen-only controls, viability and functional endpoints. No predicted or measured rejuvenation effect exists in this model; multi-donor longitudinal evidence controlling cell identity would be required.

**Falsification:** no O2 gradient difference from matched unilamellar controls; permeability unresponsive to composition where model predicts otherwise; membrane-induced nutrient deprivation; or absent tissue benefit at matched oxygenation all reject progressively stronger claims.

The scientific purpose of this PR is to preserve unfavorable controls and prevent a model-only observation from becoming a biological or medical claim.
