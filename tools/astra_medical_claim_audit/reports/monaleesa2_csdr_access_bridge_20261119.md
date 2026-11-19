# ASTRA MEDICAL Ω — CSDR MONALEESA-2 access bridge (2026-11-19)

## Newly confirmed real access route

**CSDR publicly lists study NOVARTIS-CLEE011A2301 (MONALEESA-2, NCT01958021) as _Ready to Share_ (posted May 2024).** https://www.clinicalstudydatarequest.com/Posting.aspx?ID=21159

Randomized phase III: **ribociclib + letrozole versus placebo + letrozole** in postmenopausal HR+/HER2− **advanced/metastatic** breast cancer. This is a stronger, appropriately randomized dataset for assessing treatment-effect heterogeneity than the small public FELINE genomic subcohorts. It is **not NATALEE** (adjuvant early breast cancer); transportability is unproved. NATALEE interim IPD currently unavailable to this project.

### Correct claims / exclusions

The public CSDR page establishes study **listing eligibility**, not approval of our research proposal, applicant credentials, or actual possession of IPD. Formal portal registration, independent protocol review and a qualified lead investigator are still needed. **0 patient-level MONALEESA-2 records received. Formal request NOT submitted.**

Novartis ordinarily **excludes participant-level genetics / exploratory biomarker data**, as well as imaging and patient narratives. Do not request unavailable data without an explicit sponsor exemption. https://www.clinicalstudydatarequest.com/Study-Sponsors/Study-Sponsors-Novartis.aspx

## Submission-ready methodology (researcher must review)

**Title:** Clinical heterogeneity in randomized ribociclib treatment: conditional absolute PFS benefit in MONALEESA-2.

**Hypothesis:** The average **absolute** progression-free survival benefit at 24 months varies across a few prespecified *baseline clinical* risk groups, even if relative effects are homogeneous. Differing absolute benefit due to baseline risk is **not** itself a differential treatment sensitivity; treatment × baseline interaction must be tested separately.

**Request only approved anonymized fields:** treatment randomization, baseline age, ECOG, visceral involvement, metastatic burden, prior endocrine therapy/treatment-free interval (each subject to actual dataset specifications), PFS/OS times, events and censoring, trial design/SAP/specifications, shareable toxicity definitions.

**Analysis:** ITT as allowed by trial definitions; baseline-only features and appropriate survival methods; no early-event exclusion or outcome leakage. Benchmark no-interaction survival model and KM estimates, then ≤3 predeclared treatment interactions. Compare 24-month conditional **average** absolute risk reduction or RMST differences, with participant-level bootstrap, multiplicity correction (Holm), missingness and censoring sensitivity, and calibration in groups. Report all null results. Use MONALEESA-3/-7 only with *separate approved access* and population/partner-therapy transportability assessment. Never call an unobservable individual counterfactual a known patient response.

**Independent controls:** random treatment-label permutation, noise-marker rejection, identical-treatment-effect model benchmark, calibration to observed arms and time-zero validity. No external clinical deployment until independent oncologist and statistician review.

**Governance:** no claimed doctor/biostatistician degree or institutional affiliation; signed data-use agreement and secure sponsor-authorized enclave mandatory; no IPD exports to GitHub or AI chats, aggregate approved results only. No paid infrastructure or new subscriptions authorized.

## Falsification-oriented dataset check (actual access test)

- **GSE274139**: 35 GEO samples, 16 PRE and 19 POST, raw 160 MB; no placebo arm or PFS endpoints linked in inspected GEO metadata.
- **GSE274141**: 54 GEO samples, 2.1 MB counts matrix; observational CDK4/6 categories, no placebo arm in GEO metadata.
- **GSE285861**: 168 GEO sample records and 1.9 MB expression data; checked GEO sample characteristics contain only FFPE tissue, not PFS/event outcomes; cannot verify individual benefit from metadata alone.

These counts are public **GEO series sample records**, not comparable to all 89/61 patients included in the source publication. Do not transform unsupported sample counts into patient-level causal data.

## Evidence / test provenance

Separate local dossier **ASTRA_MEDICAL_MONALEESA2_ACCESS_KIT_20261119.zip** was built and checked in the current working runtime, containing complete English protocol, manifest, dataset gate, email draft and standard-library validator: **12/12 unit tests PASS**, **12/12 optimized tests PASS**, 0 manifest violations, ZIP integrity checked. The test outputs validate the *research-request declarations only*, not clinical efficacy.

**Next external gate:** verified qualified clinical lead and authenticated formal research request through CSDR; any costs or irreversible commitments require explicit user authorization. No clinical efficacy prediction or sponsor authorization claimed.

Useful links: [official study entry](https://www.clinicalstudydatarequest.com/Posting.aspx?ID=21159), [how to request](https://clinicalstudydatarequest.com/Help/Help-How-to-Request-Data.aspx), [Novartis sponsor rules](https://www.clinicalstudydatarequest.com/Study-Sponsors/Study-Sponsors-Novartis.aspx), [Novartis transparency](https://www.novartis.com/clinicaltrials/transparency).


## Critical access gate confirmed 19 Nov 2026 — no substitute by more biomarker fishing

The official CSDR Research Proposal process is **not immediately executable** on our present facts:

- Official [CSDR how to request](https://clinicalstudydatarequest.com/Help/Help-How-to-Request-Data.aspx) requires an authenticated lead-researcher account. MONALEESA-2 is listed: select it and choose **Initiate Research Proposal** or **Ask a question about the selected study**; do **not** use the non-listed-study Enquiry.
- Official [Review of Requests](https://clinicalstudydatarequest.com/Help/Help-Review-of-Requests.aspx) **Stage 1 requires a qualified statistician** as a team member, required fields, and a plan to publish. Sponsors and the Independent Review Panel also review qualifications, scientific methodology, conflict declarations and publication plans. A fake or assumed affiliation or clinical degree would be unacceptable.
- The [Data Sharing Agreement](https://clinicalstudydatarequest.com/Help/Help-Data-Sharing-Agreement.aspx) restricts transfers of anonymized trial IPD. There is **no access approval, no signed agreement, no CSDR submission number, and no usable trial IPD in ASTRA**.
- Existing scientific contact: `Frederick.Howard@bsd.uchicago.edu`, Gmail **draft only**, not sent. A prior real sent email to `camille.stephan@irbbarcelona.org` (IRB Barcelona Bioinformatics/Biostatistics unit) was found; a **reply draft in that original thread** was prepared to seek a qualified clinical statistician/method review, **not sent**. Do not duplicate the earlier outreach or claim partner acceptance.
- The IRB Barcelona follow-up draft Gmail message ID is `1a1f439307b782f5` (draft ID `r-7794539874960400280`), corresponding to an existing sent thread, not a research proposal submission.
- No further uncontrolled exploratory gene-panel search should be labeled clinical validation. Until approved IPD or an approved partner-run aggregate validation is available, preserve the existing negative results and prioritize an actual research collaboration and a properly reviewed CSDR application.

**Status:** PASS official workflow and researcher prerequisite verification; PASS reply draft created; FAIL for access requested/submitted (no submitted application); UNVERIFIED clinical benefit individualization. No outgoing email sent and no new expenditure authorized.
