# ASTRA Scientific Network Ω — OSF registration protocol
2026-11-27 | Draft governance and reusable study worksheet, not a submitted registration or proof of a discovery.

## Existing evidence
Reuse [the original GEO protocol](../validation/PREREG-GEO-2026-10-16.md) and [its preserved negative outcome](../reports/independent-data-validation/2026-10-16.json). Do not change their historical status. Existing results are retrospective/exploratory for any new registration. The Scientific Network's signed commitments are integrity evidence, not scientific truth or independent endorsement.

## Study worksheet (complete before confirmatory access)
- Study ID, investigators and roles, title safe for disclosure, date, conflicts, funding and AI model/version/role.
- Research question, precise hypothesis and null, physical or biological mechanism, interdisciplinary method and conventional baseline; ablation to measure incremental value of the interdisciplinary contribution.
- Study stage: prospective / ongoing / retrospective. Declare prior exposure to data/results, including model selection and any contamination.
- Data provenance, licenses, independently held test sets, availability timestamps, inclusion/exclusion, sampling units, sample size/power, stopping rules, missing data and leakage barriers.
- Fixed candidate-generation budget, seeds, models, prompts, hyperparameters, selection and failure criteria. Record ALL candidates including duplicates, aborts, errors and null results.
- Primary outcome, effect direction and minimum meaningful effect, uncertainty, test, multiplicity correction, independent replication rule, negative and positive controls and sensitivity analyses. Freeze exact numerical criteria per study, not globally.
- Commit SHA, environment lock, SHA-256 manifest of exact bytes (protocol, code, inputs or dataset identifiers and split manifests); optional Ed25519 signatures with distinct signer roles. Never put secrets, private data, or undisclosed patentable details in public repositories.
- Deviations and amendments: timestamp, rationale, whether results were seen; retain original. Treat new hypotheses as exploratory and register a fresh independent test.
- Output: all outcomes, denominators, failures, exclusions, uncertainty, limitations and reproducibility instructions.

## Gates
1. DRAFT: worksheet incomplete, no confirmatory claim.
2. READY_FOR_REVIEW: all fields fixed, review data access and IP/privacy; OSF account owner explicitly approves submission and visibility. Review public metadata even under embargo. Default to no disclosure until clearance.
3. REGISTERED: record actual OSF identifier, registration URL, timestamp, approved status, version, visibility and manifest digest. Verify actual OSF record and match exact protocol before opening held-out data. A local Git commit alone is not OSF registration. No backdating.
4. RUN: use only locked protocol and log all attempts; unexpected changes cannot silently become confirmatory.
5. REPORT: PASS only for the precise endpoint satisfying registered criteria and controls; FAIL for valid rejected hypotheses; PARTIAL for incomplete evidence; UNVERIFIED for absent or invalid evidence. Separate scientific, software, deployment and replication statuses.

## Integration
Official OSF guide: https://help.osf.io/article/330-welcome-to-registrations
API: https://developer.osf.io/
Terms: https://osf.io/terms-of-use/
Prefer the OSF Preregistration template. Use an OSF draft first, then human-approved submission. No automatic public submission, no paid infrastructure. API authentication, live draft creation, identifier verification and automated gating are not implemented by this document. Do not mark as REGISTERED until an actual record is independently verified.

## Pilot selection
Select one new, independently held-out confirmatory experiment after verifying data availability and exposure. Do not repurpose the historical GEO result as a new preregistration. No study-specific threshold or claim is approved by this generic worksheet.
