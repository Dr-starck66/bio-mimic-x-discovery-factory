# BIO-MIMIC X — Buyer-facing presentation correction

**Date:** 2026-11-02 · **Reason:** User rejected the original AI-sounding commercial page, prominent software audit labels and speculative acquisition/ROI framing.

## Same live application, not a new deployment target

- AppDeploy app ID: `bio-mimic-x-industrial-evidence-if9m9p`
- Public URL: https://bio-mimic-x-industrial-evidence-if9m9p.v2.appdeploy.ai/
- New saved snapshot version: `1793610445694`
- App status: **ready**. QA snapshot: **0 frontend errors, 0 network errors**.
- Desktop QA screenshot: https://appdeployai-v2-qa-screenshots.s3.us-east-1.amazonaws.com/bio-mimic-x-industrial-evidence-if9m9p/1793610456519/web.png
- Mobile QA screenshot: https://appdeployai-v2-qa-screenshots.s3.us-east-1.amazonaws.com/bio-mimic-x-industrial-evidence-if9m9p/1793610456519/mobile.png
- Existing **Free** account, **zero paid top-up**. Included quota remaining after inspection: `253.283124555` platform units; this does **not** guarantee permanently free hosting.

## Corrections actually deployed

1. Replaced original science acceptance language and marketing filler with a restrained English B2B research-software page.
2. Moved the scientific mapping limits, excluded cases, and citations into a technical methods section that remains publicly accessible.
3. Removed the speculative public `€1,000,000` asking price, pricing terms, ROI model and all hypothetical savings displays from the landing page.
4. Retained the **actual** HAND1 historic-locus case (28,830 matching bases in 28,853 local columns, 23 edits), evidence links, input provenance and unresolved-identity boundary.
5. Retained the verified existing contact address and a direct, non-confidential email CTA; no form backend or lead database invented.
6. Revised matching public GitHub buyer documents and the repository introduction to remove an internal seller diligence checklist from the first impression, without deleting historical experiments, negative cases or Git history.

## Read-only production audit

Independent cloud host (existing connected Floot VM) fetched the **actual public HTTPS page twice**:

- HTTP **200** both attempts; both served 19,788 HTML characters.
- Built JS **HTTP 200** (711 bytes); old ROI calculation handler absent.
- Built CSS **HTTP 200** (11,126 bytes).
- All **10** production HTML content checks passed on each GET: new headline, source-backed axolotl example, accessible technical scope, negative-source link, accurate contact, no seller price or hypothetical financial ROI, no original `Interpretation: PARTIAL` banner, and noindex preference.
- AppDeploy QA: **zero** frontend and network errors; platform produced desktop and mobile screenshots. The four updated declarative UI QA scenarios are stored in the app, but **the platform has not supplied individual scenario PASS evidence**; do not misreport these as four complete browser E2E passes.

## Source of truth

- Deployed HTML/CSS: AppDeploy's saved source for the **existing app ID**. Production is not automatically synchronized with GitHub.
- Revised non-confidential buyer document: [buyer overview](../../docs/BIO-MIMIC-X-NONCONFIDENTIAL-BUYER-FACT-SHEET-2026-11-01.md).
- Revised technical evaluation: [pilot outline](../../docs/BIO-MIMIC-X-INDUSTRIAL-PAID-PILOT-SCOPE-2026-11-02.md).
- Revised buyer-friendly repository introduction: [README](../../README.md).
- Original scientific source data and negative tests were **not changed**.

**Scientific status:** The one aligned locus supports a specific HAND1 candidate comparison; a uniquely confirmed cross-assembly identity, population-level error reduction, clinical benefit and industrial economic savings remain unverified. The webpage must not imply otherwise.

**Commercial status:** No new external buyer contacts, replies, contracts or payments were created or claimed by this page revision.
