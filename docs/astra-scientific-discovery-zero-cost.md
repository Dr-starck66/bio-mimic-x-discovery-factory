# ASTRA SCIENTIFIC DISCOVERY Ω — zero cost, auditable pilot

This pilot **reuses** BIO-MIMIC X's existing
\`factory/hypothesis_engine.py\` and \`factory/experiment_planner.py\`.
It is **not** an autonomous protein generator, drug discovery service,
physical experiment, or free GPU cluster.

## Run on the existing repository

No installation beyond Python's standard library:

\`\`\`bash
python -m unittest tests.test_astra_discovery_zero_cost -v
python factory/astra_discovery_zero_cost.py \
  --knowledge data/knowledge-base.json \
  --focus regeneration \
  --limit 5 \
  --out reports/astra-scientific-discovery.json
\`\`\`

Optional **retrospective, read-only** reanalysis of Anthropic's open CSV
(do not upload sequences or any molecular design output to this repository):

\`\`\`bash
python factory/astra_discovery_zero_cost.py \
  --knowledge data/knowledge-base.json \
  --retrospective-csv /path/to/public/design.csv \
  --out reports/astra-discovery-retrospective.json
\`\`\`

Source: https://huggingface.co/datasets/Anthropic/scorpion-toxin-binder-design
License: CC BY 4.0, attribution required on reuse.

## Scientific integrity

* The catalogue's \`evidence\` and \`humanity\` values are editorial,
  not independently verified measurements.
* Three competing causal explanations per catalogue record are generated;
  two **proposed, not executed** plans are produced using the existing engine.
* Negative controls, explicit falsifiers and SHA-256 receipt are mandatory.
* The optional retrospective CSV reports only published aggregate outcomes,
  not de novo protein designs, rankings of new sequences or wet-lab results.
* Status remains **PARTIAL** even if the code and local tests are PASS.
* No paid service, external model call or recurring workflow is created.
* No source PMIDs are invented: absent identifiers remain absent.
* Deployment/public automation and biological validation are **UNVERIFIED**.

## Next technical boundary

Use an existing, explicitly free and already authorized remote compute runtime
for larger retrospective evaluation. Check provider billing and access *before*
execution; do not silently fall back to paid Hugging Face Jobs or GitHub Actions.
