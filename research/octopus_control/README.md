# ASTRA OCTOPUS CONTROL Ω — v0.1

## Scope
A reproducible standard-library Python **decision-model proxy**, not a soft-robot physics simulator. Inspired qualitatively by Wenci Xin et al., *Journal of Experimental Biology* (2026), DOI: 10.1242/jeb.252825, PMID 42987251. The article reports probing, moving 3–5 arms, squeezing, and an additional stage for some smaller openings. Our mathematical coefficients, traction and force rules are invented assumptions for falsification, **not parameters derived from the research paper**.

## Reproduction
From this directory:
- `python octopus_control.py`
- `python -m unittest -v test_octopus_control.py`

The deterministic grid uses **400 synthetic configurations** (10 apertures × 4 resistance values × 5 anchor qualities × 2 misalignment settings). Both algorithms operate on the same minimum-envelope constraint and base drive. The staged policy adds grip-assisted traction (explicit model assumption) and time/effort overhead; the direct policy has no anchoring. Includes negative controls for too-narrow geometry, zero grip and wide easy passages.

Running the program writes `report.json` (summary and SHA-256 of canonical observations) and `observations.json` (every scenario and algorithm outcome). The file `report-reference-20261114.json` records the initial locally reproduced result.

## Evidence rules
- **PASS**: local Python runtime and 16/16 unit tests on the locally tested source code on 2026-11-14.
- **PARTIAL**: a synthetic design exercise capable of demonstrating modeled benefits and modeled penalties under chosen assumptions.
- **UNVERIFIED**: physical superiority, actuator dynamics, safety, military suitability, industrial ROI, patentability, independent replication or real-world testing.
- Never market synthetic pass rates as real performance.
- Civilian and safety-focused inspection, maintenance and rescue only; no autonomous violence, covert entry or targeting.

## Next scientific gate
Reproduce with independently measured contact mechanics, real aperture geometries and an unbiased physical or finite-element reference; document counterexamples. Do not merge before review.
