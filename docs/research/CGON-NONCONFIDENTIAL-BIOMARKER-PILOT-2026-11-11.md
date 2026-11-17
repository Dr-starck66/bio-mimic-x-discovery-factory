# Independent bladder-cancer immunotherapy biomarker evidence audit — non-confidential summary

**BIO-MIMIC X / ASTRA Ω | Public-data research demonstration | 11 November 2026**

## Potential relevance to CG Oncology
Early biomarker hypotheses can look promising in small discovery analyses but fail across different cohorts and clinical outcomes. We are offering an **independent computational feasibility evaluation** that preserves negative results and audits whether apparent tumor / immune signatures survive source, patient, control-group, and multiple-testing checks.

We **do not claim** to be affiliated with CG Oncology, to have analyzed any cretostimogene-treated patient records, or to have discovered a validated predictive marker for its trials.

## Demonstrated, not proposed
- An authentic RNA expression matrix from GSE244895 (35 samples, 12 paired patients), strict SHA-256 source audit, 12 unit tests and cross-language effect/p/q recalculation.
- In a **separate public BCG responder/nonresponder cohort GSE176178**, actual featureCounts matrix for **40 patients** (17 durable responders, 23 others) processed reproducibly, with three exploratory two-gene immune signatures selected following the earlier GSE244895 analysis, 20,000 global/sex-stratified label permutations per signature and 2,000 bootstrap replicates.
- **Negative evidence:** none of three CD8, chemokine or macrophage RNA proxies was significant after sex-stratified BH correction (all q≈0.978). Outcomes and assays differ between datasets: these cannot be presented as direct cross-cohort replication of the same biomarker endpoint.

Reproducible method + source-provenanced results: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/45

## Narrow proposal for a feasibility discussion
A 20–30-minute scientific scoping call to determine whether an **independent, non-confidential replication and false-discovery audit** could help your research teams. A possible small pilot would be defined around one study question, an approved dataset, pre-specified molecular endpoints, patient-wise splits, baseline models and negative controls; full methodology, failures and reproducibility logs delivered as reviewable artifacts.

**What we would need from a sponsor**: agreement on the scientific question and endpoints; a suitably de-identified, legally shareable dataset with clinical outcomes under relevant governance, or approval to use public data only. We would not handle identifiable patient data or run biological/viral experiments.

**Not offered or asserted:** patient-specific treatment advice, molecular prediction of cretostimogene outcomes, regulatory evidence, validated cancer therapy enhancement, intellectual-property ownership over public data, or commercial valuations.

Contact channel confirmed by the company: **bd@cgoncology.com**. **On 11 November 2026 an introductory scientific scoping email was sent**; no human expression of interest, reply, permission to use additional data, partnership, or contract has yet been verified. Two separate independent methodological review requests were also sent to relevant academic research contacts. These outbound contacts do not imply collaboration or endorsement.

## Proposed study-scope authorization gate (draft — NOT AUTHORIZED)

This section is a *nonbinding draft questionnaire for potential partners*. It is not an approved protocol, signed scope of work, data-use agreement, ethics determination or sponsor contract. Any checked conditions below must be **affirmatively confirmed in writing by a named authorized institution representative** before being treated as accepted.

| Gate | Proposed written record required | Status |
|---|---|---|
| Interested scientific contact | Name, role, institution, explicit response willing to evaluate proposal | **UNVERIFIED** |
| Research question | One falsifiable NMIBC/BCG endpoint and intended patient population | **NOT AGREED** |
| Permitted dataset | Explicit public GEO accession(s) and permitted reuse, or separately executed DUA / sponsor authorization | **NOT AGREED** |
| Individual-level governance | Public de-identified data only until approved; no clinical identifiers or private sample transfers | **NOT AGREED** |
| Endpoint / statistical plan | Response definition, covariates incl. sex, age, tumor grade/stage, sampling time, cohort split and exclusions | **NOT AGREED** |
| Comparator and controls | Null permutations, negative gene-set controls, pre-established baseline; preserve unfavorable outcomes | **NOT AGREED** |
| Reproducibility artifacts | Version-pinned analysis, source hashes, results, failures and independent re-check | **PROPOSED** |
| Reporting/IP/publication | Who can see outputs, ownership of newly written code, disclosure of negative findings, publication approval | **NOT AGREED** |
| Human research / compliance | Institutional ethics and lawful data processing determination by data controller where applicable | **NOT AGREED** |
| Funding / legal identity | Parties and authority to sign, separate written budget/contract; no cost or paid pilot assumed | **NOT AGREED** |

### Tight proposed pilot definition for discussion

**Working title:** "NMIBC BCG immune-marker reproducibility and false-discovery audit (public-data first)".

**Initial data scope:** public `GSE244895` and `GSE176178` only, with source citations and license/consent checks before republication or sharing of patient-level derived data. They address different clinical questions; **do not treat their differential effects as the same endpoint**.

**Primary useful outcome:** a transparent determination whether a *partner-predeclared* fixed candidate biomarker or small panel demonstrates a consistent, above-baseline association with an explicitly defined BCG response endpoint on suitable external datasets. A documented **negative result is an acceptable outcome**. Current three two-gene proxies did not achieve BH q < 0.05 in GSE176178.

**What can be delivered:** read-only source and quality-control manifest, preregistered contrast, patient-aware test code, negative-control and confounder sensitivity report, precise non-significance statement, and replayable checksums in a non-confidential report.

**Excluded:** cretostimogene-treated or sponsor trial data without separate authorization; treatment optimization; direct patient guidance; clinical use; wet-lab work; regulated device claims; intervention design; a claim of accuracy, efficacy, IP exclusivity or minimum economic value.

**Only after written acceptance of the scope** should a priced service or separate contract be discussed. Email contact alone, public dataset access, a completed technical test, and a speculative "interested" inference are NOT evidence of signed scope or procurement.

### Suggested acceptance language (must be completed by partner)

> We are interested in a preliminary BIO-MIMIC X scientific evaluation of **[specific question]** using only **[approved dataset names]** under **[data governance terms]**. The output is **[defined report and criteria]**. We confirm **[permitted use of public materials / governing agreement]** and nominate **[authorized scientific contact]**. This message does **not** authorize access to private patient data, clinical interventions, public claims of endorsement, or paid services.

**Acceptance status: NOT RECEIVED.** No fields should be completed or inferred by BIO-MIMIC X.
