# ASTRA MEDICAL Ω — NATALEE access feasibility + testable IPD bridge
**19 Nov 2026. Research-only. No clinical claims.**
## New independently verified access finding
NATALEE (NCT03701334) remains an active follow-up trial (expected completion around May 2030 in current trial listings). The Novartis data-sharing policy normally excludes participant-level sharing from interim results until the final study clinical study report and publication. **The 2026 six-year published analysis does not itself grant access**. Any exception can only be confirmed by the official sponsor portal.

Official routes:
- [ClinicalStudyDataRequest.com — Novartis](https://www.clinicalstudydatarequest.com/Study-Sponsors/Study-Sponsors-Novartis.aspx)
- [CSDR guide](https://www.clinicalstudydatarequest.com/Help/Help-How-to-Request-Data.aspx): a verified user account is required before an enquiry or proposal.
- [Novartis transparency](https://www.novartis.com/clinicaltrials/transparency)
- [Vivli Novartis policy](https://vivli.org/ourmember/novartis-pharma-ag/)
- [Trial register](https://clinicaltrials.gov/study/NCT03701334)

**Administrative proof:** Novartis-only request route identified, but no authenticated researcher identity, no sponsor feasibility confirmation, no data-sharing agreement. **Enquiry NOT sent. Research proposal NOT submitted. IPD 0 rows.** Do not fabricate sponsor approval or investigator credentials.

## Prior art and scientific distinction
[Howard et al., Clinical Cancer Research, 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC12809111/) already built machine-learning models using NATALEE and Flatiron data: external prognostic C-index 0.66 and NATALEE-trained prognostic C-index 0.70. These discriminate **recurrence risk**, NOT individually observed causal ribociclib effects. A legitimate novel study would preregister treatment-by-baseline interactions, absolute survival effect estimands and credible independent validation, including negative findings.

## Implemented, tested, isolated proof-of-concept (conversation artefact)
Local package name: `ASTRA_NATALEE_RESEARCH_BRIDGE_20261119.zip`
Archive SHA-256: `80a98b96c52c937e7f22ae83311509f002679a6537cc612afe3da4a91d43520b`.
Contains:
- `natalee_ipd_audit.py`: offline Kaplan-Meier 72-month arm contrasts by two prespecified baseline strata, Greenwood approximate intervals, interaction contrast, exact input schema, study-data governance gate and aggregate-only output.
- `test_natalee_ipd_audit.py`: **15/15 PASS** normal Python and **15/15 PASS** `python -O`. Controls for arm and subgroup inversion, right censoring, zero events, unknown labels, malformed follow-up, leakage columns, duplicate IDs, inadequate follow-up, unsafe subgroup size, unauthorized invocation.
- `synthetic_only_240_rows.csv`: only invented records; intentional contrast in groups A (+0.25) and B (−0.20) with interaction +0.45, **meaningless for human patients**.
- `RESEARCH_PROPOSAL_CSDR_NATALEE.md` and `.pdf`: formal scientific proposal drafted in English; not submitted.
- `FEASIBILITY_ENQUIRY_FOR_CSDR.md`: question about sponsor study availability; not sent.
- `MANIFEST.json` with file hashes, `test_log_python.txt` and `test_log_optimized.txt`.

A first local test exposed a real implementation bug: `summary()` silently ignored an unknown treatment label; input validation was corrected, then 15/15 PASS.

### Status matrix
- **PASS**: source-specific sponsor policy researched; Python test of synthetic KM calculations; negative controls; PDF proposal rendered and checked; archive SHA calculated.
- **PARTIAL**: web-based trial completion date obtained from current trial mirrors; the sponsor's exact study-availability status is not verified by login.
- **UNVERIFIED**: availability of 2026 NATALEE IPD; submission success; 6-year trial data access; clinical model performance; external validation, patient-specific benefit.
- **Costs:** 0 EUR additional. No new automation, hosting, patient export or clinical deployment.

**Scope note:** Tool is a non-predictive baseline estimator; it does not demonstrate individual treatment-effect identification. The two potential outcomes of any single patient cannot both be observed, even within randomized trials. Do not deploy into medical decision making.