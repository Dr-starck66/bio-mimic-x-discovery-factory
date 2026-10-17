# BIO-MIMIC X — Buyer Data-Room Preparation, 17 October 2026
**Status: PREPARING; not a completed diligence package.**

## Folder index / proof already visible
| Buyer question | Evidence currently present | Status |
|---|---|---|
| Does it execute? | GitHub Actions https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/39005306559 (129 unit tests, 12 Chromium scenarios, live 18-card API run) | PASS SOFTWARE TESTS |
| Reproducibility? | `qa/repro_acomys.py`, `qa/browser-smoke.mjs`, `qa/live-browser-smoke.mjs`, workflow artifacts | PASS SOFTWARE REPLAY |
| Actual science? | `validation/PREREG-GEO-2026-10-16.md`, `reports/independent-data-validation/2026-10-16.md` | FAIL preregistered two-cohort criterion |
| Novel candidate/IP? | `docs/PRELIMINARY-PRIOR-ART-SCAN.md` (preliminary, non-legal) | UNVERIFIED |
| Prospective experimental partner? | `validation/PROSPECTIVE-LAB-PROTOCOL-2026-10-16.md` (unexecuted design) | OUTREACH INITIATED |
| Commercial traction and buyer? | `factory/commercial_evidence_registry.json` empty | UNVERIFIED |
| Existing valuation proof? | `factory/million_euro_evidence.py` fail-closed decision gates | EUR 1m asking price only |

## Mandatory diligence items not yet supported by verified paperwork
1. **Chain of title**: inventor/developer identities and contribution dates, employer obligations, assignment records, subcontractors, code generation provenance. Repository ownership is not the same as legal ownership of every component.
2. **Public-source and license position**: repository currently public with no top-level LICENSE; buyer counsel to determine rights to all material and impact of public release on exclusivity. No proprietary-rights conclusion implied by absence of LICENSE.
3. **SBOM and dependencies**: enumerate front-end dependencies, Python package imports, GitHub actions pinning, licenses, commercial redistribution restrictions and third-party scientific data licenses; produce a signed SBOM before code access.
4. **Secrets/security**: scan Git history and current tree for credentials, PII, private service URLs, dependency vulnerabilities and supply-chain provenance. Rotate compromised material if found. A scan alone cannot certify security.
5. **Data**: permissions for redistribution and caching of Europe PMC, GEO, Ensembl, Open Targets, third-party datasets and imported annotations. Do not promise transfer of third-party IP.
6. **Functionality**: a buyer-run live demo on reproducible environment, security review, uptime tests, incident logs and documented scope of autonomous pipelines.
7. **Science**: source-level methods review and independent experimental study if buyer needs biology claims; not a prerequisite to sell research software, but essential to sell a novel mechanism.
8. **Deal**: responsible seller entity, ownership structure, location/jurisdiction, tax advisor, NDA, letter of intent, purchase agreement, representations and warranties, handover/escrow, payment verification.

## Suggested transaction structure (for negotiation, not an offer)
**Route A:** EUR 1,000,000 cash on closing for an exclusive transferable asset after IP/technical audit.

**Route B:** EUR 300,000 at closing plus EUR 700,000 milestones tied to objective, independently verifiable software adoption or licensing outcomes and an agreed deadline. Higher risk of non-payment to seller; should be reviewed by legal counsel.

**Route C:** Paid technical evaluation, credited toward acquisition price if a mutually agreed acquisition proceeds. Buyer must not be given proprietary implementation or exclusive rights before contract.

No structure is committed, independently valued or accepted by a buyer.

## Independent red flags worth fixing first
- Public repository exposes substantial implementation, decreasing perceived exclusivity and potentially damaging trade-secret positions; making it private later cannot reverse prior public exposure.
- No license file identified on default branch; this is not proof of copyright assignment.
- Current front-end is not established as a buyer-accessible production domain in the scientific acceptance report.
- A scientific hypothesis in two retrospective datasets did not satisfy preregistered replication; do not hide this in outreach.
- An email outreach is not proof of interest. Only authenticated replies, signed term sheets and payments should change business states.

## Current gate status (as of 17 Oct 2026)
`CONTACTED = PASS` (Gmail sent IDs logged separately), `LABORATORY_COMMITTED = UNVERIFIED`, `BUYER_INTERESTED = UNVERIFIED`, `BINDING_OFFER_1M = UNVERIFIED`, `TRANSFERRED_AND_PAID = UNVERIFIED`.

**Share only the non-confidential teaser at first contact:** `docs/ACQUISITION-TEASER-EN-2026-10-17.md`.
