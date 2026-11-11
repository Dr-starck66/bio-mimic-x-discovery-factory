# BIO-MIMIC X — Fixed-scope biomarker evidence audit (non-binding offer)
**Version:** 2026-11-11 · **Status:** PROPOSED / NOT ACCEPTED · **Audience:** biotech business development, translational science, precision diagnostics.

## One-sentence value proposition

An independent, reproducible **false-discovery and data-integrity audit** for an explicitly defined bladder-cancer molecular biomarker hypothesis, with the same rigorous reporting whether it reproduces or fails.

This is **not** a proposal to design or improve an oncolytic virus, provide clinical guidance, certify a diagnostic, or claim a validated cretostimogene or UGN-501 predictor.

## Real evidence already produced (at no additional infrastructure spend)

| Source | What was executed | Result |
|---|---|---|
| [GSE244895](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE244895) | 35 public NMIBC samples, 12 patient-matched BCG pre/post comparisons, SHA-pinned QC, 8 gene tests and 3 two-gene proxies | All FDR q > 0.05; strict one-row malformed terminal source quarantine documented |
| [GSE176178](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE176178) | 40 public NMIBC tumors, 17 vs 23 durable BCG outcome labels, sex-stratified permutation controls (20k per signature), male-only sensitivity | Three selected proxies **all sex-stratified BH q≈0.978**; AUCs 0.491, 0.412, 0.496 — **no predictor established** |

Replicable evidence: [PR #45](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/45), specifically [GSE244895 execution audit](../research/GSE244895-REAL-EXECUTION-AUDIT-2026-11-11.md) and [GSE176178 responder audit](../research/GSE176178-EXTERNAL-RESPONSE-VALIDATION-2026-11-11.md). Existing GitHub repository is public; lack of a repository-wide declared license means **no blanket permission to redistribute code, transfer IP, or grant exclusive rights should be inferred**.

## Proposed narrow commercial pilot (illustrative, no commitment)

**Illustrative fee: €2,900 excluding applicable taxes** for **one** hypothesis evaluation in **one** legally usable public or duly authorized *de-identified* molecular cohort. Pricing is **unapproved, non-binding and subject to the identity and invoicing authority of the contracting provider**, signed scope, actual data quality, and applicable taxes. No invoice, purchase order, client, funding, revenue or contract currently exists.

*Included only after acceptance of a written Statement of Work:*

1. **Protocol lock:** client and analyst agree one population, one clinical outcome, up to three predetermined biomarker signatures, measurable null and baseline criteria, and which sample is the independent unit.
2. **Data and rights intake:** written confirmation of a public GEO accession or expressly permitted de-identified dataset; count patients, annotations, missingness and leakage risks; preserve input fingerprints and data provenance.
3. **Analysis:** one cohort, exploratory/validation analysis according to suitability; group-wise or patient-wise statistics, one appropriate baseline, an explicit negative control, multiplicity correction, and prespecified limitations. If the dataset cannot answer the endpoint, the report states **NOT EVALUABLE**, not a fabricated accuracy.
4. **Independent reproducibility review:** runnable code, frozen version/fingerprints, replay log, negative-result retention; calculation cross-check in a second implementation where feasible.
5. **Delivery and review:** one concise PDF or Markdown scientific audit (scope, exact denominators, methods, failures, adverse findings), machine-readable JSON or CSV outputs, and one remote review meeting with the named client scientist.

**Acceptance means delivery completeness, not a statistically significant biomarker.** A properly demonstrated null, non-reproducibility, data-quality failure, or uncertain result is a valid scientific deliverable.

### Out of scope

- Clinical-trial records, confidential sponsor data, identifiable personal data, tissue samples, virus design, wet-lab/biological intervention, medical decision-making, clinical diagnostic validation, product regulatory submissions, formal certification, or claims of treatment efficacy.
- Large-scale discovery, patient-specific inference, therapeutic-response optimization, multiple cohorts, proprietary data licensing, and ongoing monitoring without a separately accepted scope.
- Promises of commercial return, scientific novelty, company valuation, minimum diagnostic AUC or regulatory acceptance.

### Written approval gates before any paid work

A named authorized counterpart must confirm **all** of: scientific question and endpoint; appropriate dataset rights/DUA/ethics clearance where needed; fixed signatures and validity conditions; deliverables; reviewing contact; access/security; permitted publication of negative results; confidentiality and IP; contracting entities; fee/taxes; and purchase-order/payment terms.

No expression of interest, email delivery or request for a meeting is treated as such an approval.

## Prospect conversation script (optional)

“We have already published a small but real, reproducible NMIBC/BCG case study, including negative results. We are not selling a new bladder-cancer biomarker. Would a tightly constrained, fixed-fee independent audit of one molecular claim be valuable to your translational team? If yes, please name a scientist and dataset owner so we can lock the endpoint, legal permissions, failure criteria and deliverables in a short written scope.”

**No prospect has accepted this offer as of creation on 2026-11-11.** This file is internal commercial planning content in a public research branch; it is not a contract or a blanket offer to unidentified parties.
