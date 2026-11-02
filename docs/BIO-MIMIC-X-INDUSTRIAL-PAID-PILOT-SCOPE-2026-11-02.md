# BIO-MIMIC X — Industrial pilot evaluation / acquisition-screening package

**Revision:** 2026-11-02 · **Status:** non-binding seller proposal; **no buyer budget, LOI or payment confirmed**.

## Business problem, stated narrowly

A biotechnology or regenerative-medicine R&D team can lose analyst time and downstream experimental money when historic gene annotations, paralog labels or assembly IDs are treated as exact matches without sequence provenance. BIO-MIMIC X proposes a traceable **gene-identity quality assurance / reject-the-unsupported** workflow. A therapeutic discovery, clinical efficacy or unique invention is **not** established.

**One measured source case:** Historic axolotl `AMEX60DD030069` had an ambiguous `HAND1 [nr]|HAND2 [hs]` tag. An Edlib local alignment against the new NCBI assembly found HAND1 at **28,830/28,853 matching aligned columns (99.9203%; 23 edits)** versus HAND2 at **2,334/4,432 (52.6625%; 2,098 edits)**. The local query lengths differ and this is not a genome-wide reciprocal confirmation. Evidence: [original JSON](../reports/factory/HAND1-HAND2-ALIGNMENT-LATEST.json) and [experiment note](../reports/factory/HAND1-HAND2-ALIGNMENT-EVIDENCE-2026-11-01.md). Negative observations are retained.

## What an industrial reviewer should request

1. **Independent inputs and truth:** Buyer selects blinded gene mappings from old/new assemblies, including known paralog confusions and genuinely unrelated negative controls. Only public/licensed datasets; avoid confidential or patient data in the initial screen.
2. **Independent standard baseline:** A competent analyst runs a documented NCBI/Ensembl/BLAST-based protocol. BIO-MIMIC X runs on exactly the same held-out cases; no changing target genes, thresholds or sequence windows after labels are revealed.
3. **Decision metrics:** Numerator and denominator for validated mappings, incorrect positive mappings, appropriate abstentions, unresolved cases, wall-clock and human analyst minutes (instrumented), machine time and cost (measured), failure/retry counts and audit-replay success. Report **both** tool-only and full analyst-in-the-loop outcomes.
4. **Success/kill rule:** Buyer pre-registers acceptable confidence and practical improvement before opening results. An apparent improvement based on one HAND1 case, synthetic substitutions or a wrong baseline is insufficient. Preserve regressions, inaccessible sources and negative results.
5. **Commercial authorization:** Identify the named technical sponsor and actual budget owner, procurement channel, agreed IP/third-party license scope, legal entity and signed paid order before coding against private buyer data. No source or patent exclusivity is asserted without counsel's verification.

## Small first paid pilot — draft scope only

- **Acceptance specimen:** Buyer-selected representative subset; target 50–200 independently annotated loci after a small, no-cost feasibility check of access, size and legal rights. This is a **proposed sample-size range**, not a dataset already obtained or evidence of performance.
- **Delivery:** Executable reproducibility instructions, source/provenance ledger with SHA256, baseline-vs-product error table with denominators, failure log, and security/IP risk summary.
- **Time & money:** Duration, start, pilot fee and payment terms **to be negotiated** with the budget owner; do not infer from this memo that any company has approved spending. A subsequent exclusive licence or asset purchase at a seven-figure seller asking price is **conditional**, not a binding offer or valuation.
- **Excluded claims:** No validated human limb regeneration, human efficacy, experimentally confirmed biological target, patented novelty, assured returns or guaranteed savings.

## Seller-facing hard stops

**STOP without external signoff** if partner cannot prove payment authority, refuses to provide holdout annotations or consents, demands transfer of third-party IP, requests a clinical claim, or relies solely on browser screenshots/GitHub test passes as scientific validation.

## Qualification questions for Integra or a similar industrial team

- Does R&D / technology scouting **buy external computational analysis tools or software IP**?
- Which named person is authorized to sponsor a **paid feasibility/pilot** and who controls procurement funds?
- Is the team willing to share a representative *non-sensitive* blinded sample and the baseline procedure before reviewing output?
- Would they accept a non-confidential 20-minute demonstration and a written pilot evaluation proposal?
- Is there a genuine discretionary budget for **potential** software licence or acquisition, including possible seven-figure transactions, and what diligence is required?

**Source-of-truth rule:** Actual replies and offers belong in the authenticated commercial evidence registry, not a self-asserted JSON entry. Three external requests sent 2026-11-01; as of drafting, no verified response or contract is recorded.
