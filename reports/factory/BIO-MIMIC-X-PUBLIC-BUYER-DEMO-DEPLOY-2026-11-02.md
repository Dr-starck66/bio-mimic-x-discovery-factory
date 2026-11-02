# BIO-MIMIC X — Actual public buyer demonstration deployment

**Deployment date:** 2026-11-02 Europe/Paris. **Status:** static public app ready; two independent read-only HTTP checks 200. **No buyer purchase or efficacy proved.**

## Durable deployment identity

- Existing owner-connected platform: **AppDeploy**, existing user account **Free**; no subscription or paid top-up.
- Frontend URL: **https://bio-mimic-x-industrial-evidence-if9m9p.v2.appdeploy.ai/**
- AppDeploy app ID: `bio-mimic-x-industrial-evidence-if9m9p`
- App type: **frontend-only**, template `html-static`; no backend, API key, data storage, lead-tracking service, AI inference or background tasks added.
- Platform reported deployment status **ready** and an accessible desktop/mobile QA screenshot with **zero frontend and network errors**.
- QA screenshot (desktop): https://appdeployai-v2-qa-screenshots.s3.us-east-1.amazonaws.com/bio-mimic-x-industrial-evidence-if9m9p/1793578303743/web.png
- QA screenshot (mobile): https://appdeployai-v2-qa-screenshots.s3.us-east-1.amazonaws.com/bio-mimic-x-industrial-evidence-if9m9p/1793578303743/mobile.png
- Source snapshot version at first deployment: `1793578287903`; AppDeploy stored source paths `index.html`, `src/main.ts`, `src/styles.css`, and `tests/tests.json` read back successfully.

## Separately executed HTTP checks

Two independent HTTPS GET requests were made from an existing authorized Floot cloud VM **after** AppDeploy reported ready:

| Probe | HTTP | Content type | HTML bytes | Evidence |
|---|---|---|---:|---|
| GET 1 | **200** | text/html | 20,636 | HAND1/HAND2 99.9203%/52.6625%, scientific PARTIAL, noindex, pilot scope link, 1 M€ seller asking-price disclaimer, mailto |
| GET 2 (after 1.25 seconds) | **200** | text/html | 20,636 | All same content checks succeeded |

- Deployed Vite JS bundle `./assets/index-DAcoReqM.js` returned **HTTP 200** (1,643 bytes), containing the real calculator event handler and invalid-input guard.
- Deployed CSS bundle returned **HTTP 200** (8,149 bytes).
- AppDeploy account verified **Free** after deployment; remaining included monthly credits `263.75773866`, top-up `0`. This consumes existing free quota, **not a billed euro payment**. No claim of permanently unlimited free hosting is made.
- The page has `<meta name="robots" content="noindex,nofollow">` by design: share privately with industrial evaluators, not seek Google indexation of a non-confidential transaction pitch.

## Real production JS bundle tests — 5/5 PASS (headless VM, not visual browser)

The exact JS binary served by the deployed HTTPS site was fetched and executed with Node's VM module and a deterministic minimal DOM-event adapter. All outputs came from the **deployed asset**, not copied source:

| Case | Expected | Observed |
|---|---|---|
| Zero known benefit / zero inputs | €0 | **€0** |
| 1,000 audits × 15 minutes × €80/hour (illustrative) | €20,000 | **€20,000** |
| Negative minutes | Invalid scenario | **Invalid scenario** |
| Fractional annual audits | Invalid scenario | **Invalid scenario** |
| Impossibly large scenario | Invalid scenario | **Invalid scenario** |

**Limit:** This VM exercise does not replace an interactive real-browser test. The platform supplied desktop/mobile screenshots and no frontend/network errors, but its five submitted UI QA scenarios are not individually reported as passed here. A persistent deployed version and two external GETs do not establish uptime indefinitely.

## Scientific and commercial truth boundaries

- NCBI HAND1 candidate alignment has 28,830 matching bases in 28,853 local alignment columns; HAND2 alternative has 2,334 in 4,432. **This does not prove a unique reciprocal mapping across the full genome.**
- Four-family screen was **PARTIAL**: eight symbolic targets, two historically distinct loci eligible, **one** complete paired alignment; an SOX3 modern reference could not be uniquely confirmed. See [original adverse dataset receipt](AXOLOTL-PARALOG-PANEL-LATEST.json) and [analysis](AXOLOTL-PARALOG-PANEL-EVIDENCE-2026-11-02.md).
- Browser calculator is for **buyer-entered hypothetical values only**. Savings, actual ROI, error reduction, clinical/therapeutic efficacy and any real buyer budget are **UNVERIFIED**.
- Indicative seller target `€1,000,000` is a **non-binding asking price**, not an externally validated valuation, acquisition offer or signed sale.
- Only mailto contact link is offered; no personally identifiable form submissions or server-side lead database is present. **No new outbound commercial messages were sent during this deployment.**

## Operational recovery and continuity

The app's **actual production source is held by AppDeploy**. The source-of-truth scientific receipts remain in this GitHub repository. These are two separate systems; **automatic GitHub → AppDeploy deployment synchronization is NOT configured or asserted.**

To inspect/update the same application without creating a duplicate, use the existing connected AppDeploy tools with the exact `app_id`: `get_app_status`, `src_glob`, `src_read`, then `deploy_app` **with the same app_id** and only changed files. Confirm status `ready`, public HTTPS and the scientific/financial disclaimers after each edit. Do not add paid functions or subscriptions without explicit approval.
