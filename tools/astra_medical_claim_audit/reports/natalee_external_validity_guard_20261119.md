# ASTRA MEDICAL Ω — NATALEE external-validity safeguards, 19 November 2026

Research-only. Does not assert a validated ribociclib-responder model.

## New primary methodological criticism
Xin Zhou, *Misclassification and Circular Inference Undermine the Reported NATALEE Benchmark*, **4 Nov 2026**, DOI **10.2147/DDDT.S666928**: https://www.dovepress.com/misclassification-and-circular-inference-undermine-the-reported-natale-peer-reviewed-fulltext-article-DDDT

This is a critique of the **Abdel-Razeq et al. observational eligibility benchmark**, NOT of NATALEE randomization or of the Howard et al. model per se. Failure modes to exclude in *future independent observational external validation*:

1. Do not interpret missing Ki-67/genomic-risk tests in node-negative records as biologically ineligible. Use explicit missing/unknown eligibility and report missingness by calendar era and institution.
2. Do not eliminate outcomes with <6 months follow-up without reporting early events and sensitivity analyses against immortal-time or early-truncation bias.
3. An eligibility score constructed from nodes, tumor size and grade can correlate with outcomes by construction. Its separation is **prognostic**, not evidence of a causal benefit from administering a CDK4/6 inhibitor.
4. A predictive-treatment claim needs actual exposure comparator, baseline factors, clear time-zero, randomization or well-justified causal design, treatment-by-feature interactions, holdout evaluation and calibrated absolute effects. Patient-specific counterfactuals remain unobservable; at best estimate conditional **average** treatment effects.
5. Preserve negative controls (arm-label permutation, temporal selection, shuffled outcomes), baseline risk-only comparator, multiple-testing accounting and confidence intervals.

## Actually executed real-data benchmark
Historical public GBSG2 data (686 genuine deidentified patient records; **not ribociclib**), sourced from public GitHub file blob SHA `677e12eb6cc0e0a5e9a11acc74aff8266b403f8e`.

- Prognosis: prespecified `log1p(positive_nodes)` C-index **0.64524**; bootstrap 95% **0.61490–0.67929**; 100 shuffled-score negatives mean **0.50084** (0 surpassed original).
- Exploratory treatment interaction, historical hormone therapy, 3y RFS, nodal strata ≤3/>3: **−4.792 percentage points** interaction, bootstrap 95% **−19.95 to +11.94 pp** and 300-permutation Monte Carlo p **0.51827**. An earlier separate permutation sequence gave p≈0.58; neither supports heterogeneity.
- 8/8 executable sanity checks and independently re-read code and report GitHub.
- Executable code: `tools/astra_medical_claim_audit/gbsg2_real_benchmark_20261119.mjs`
- JSON aggregate audit: `tools/astra_medical_claim_audit/reports/gbsg2_real_benchmark_20261119.json`.

## Sponsor access and research team
NATALEE NCT03701334 remains ongoing; Novartis policy generally withholds interim IPD. CSDR submission is only by registered portal enquiry/proposal and subsequent independent review. No submission number, sponsor data, clinical collaborator acceptance or independent clinical validation obtained. The project's working research signature is **Dr Starck / ASTRA Ω Research**, *no verified institutional affiliation or degree*. Do not misrepresent as an institutional principal investigator. Two existing Gmail drafts have been updated, **not sent**.

Scientific statuses: PASS public data calculations and source commits, UNVERIFIED ribociclib subgroup response prediction, and PARTIAL official data-access feasibility.
