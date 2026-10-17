# ASTRA PUBLICATION RECOVERY Ω — BIO-MIMIC X

**Date:** 2026-10-17
**Source GitHub:** `Dr-starck66/bio-mimic-x-discovery-factory`
**Immutable GREEN source:** `9bf75259a1853fe4a8efe5ce66cc9b309361a027`
**Acceptance baseline:** https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/39007588412

## Zero-additional-subscription public host

Existing, published Floot project `DUALITY X V0.3 ECO` is reused via isolated additions without changing its home page or existing endpoints. Project ID: `a80a6a97-ccdd-419f-8ce3-cc7ec73adcac`.

- **Public Control Center:** https://duality-x-eco.floot.app/_api/biomimic?path=index.html
- **Public Hunter:** https://duality-x-eco.floot.app/_api/biomimic?path=hunter.html
- Friendly route: https://duality-x-eco.floot.app/biomimic (React redirect to immutable hosted HTML; direct API URL works without this redirect).
- Existing unaffected app: https://duality-x-eco.floot.app/

Floot project files added:
- `endpoints/biomimic_GET.ts`: safelisted GET-only static-public-file gateway; serves raw GitHub files from the **GREEN SHA**, correct MIME, source SHA header and short error responses (no arbitrary proxy).
- `pages/biomimic.tsx` and `pages/biomimic.hunter.tsx`: scoped redirect entry points.

The large `data/factory/latest.json` file is fetched directly from public, immutable GitHub raw by the dashboard to avoid serverless response-size limits. All other relative HTML/CSS/JS/JSON paths are rewritten in the hosted HTML to the same scoped gateway. No secrets, new paid service, new cron or new Railway service were provisioned.

## External independent proof

On 2026-10-17, a remote Node network VM tested the Floot production URL and observed HTTP 200 and correct types for dashboard HTML, Hunter HTML, browser JS, CSS and science JSON. Floot responses advertise `x-biomimic-source-commit: 9bf75259...` and the unmodified DUALITY homepage stayed HTTP 200 with original content. The upstream assets were compared octet-for-octet to their GitHub raw counterparts. That does **not** establish independent lab validation.

The existing GitHub acceptance workflow now includes `qa/publication-live-smoke.mjs`, running real Chromium against the PUBLIC Floot URLs. A final **PASS_BROWSER_PUBLICATION** requires a completed successful run; see GitHub Actions. Chrome tests use a deliberately mocked provider fixture for replay-integrity checks and additionally assert the large dashboard JSON loads, so the result remains software-only.

## External static fallback (not guaranteed production hosting)

Immutable Cloudflare-backed source CDN:
- https://rawcdn.githack.com/Dr-starck66/bio-mimic-x-discovery-factory/9bf75259a1853fe4a8efe5ce66cc9b309361a027/public/index.html
- https://rawcdn.githack.com/Dr-starck66/bio-mimic-x-discovery-factory/9bf75259a1853fe4a8efe5ce66cc9b309361a027/public/hunter.html

The CDN serves correct MIME and HTTP 200, but browser visitors may encounter a third-party phishing-protection confirmation page; uptime/support are not guaranteed. Development-style `raw.githack.com/.../main` URLs are **not suitable for high-traffic production**. Do not replace an owned canonical domain or serve confidential assets through this fallback.

## Deployment and next releases

The Floot gateway is **pinned to the vetted source SHA**. It will not automatically promote an untested newer commit; update the gateway SHA via the connected Floot edit/publish actions **after the new exact commit has both acceptance jobs passing**. Treat `PASS_SOURCE`, `PASS_TESTS` and `PASS_PRODUCTION` independently. Monitor the public URL's correct HTML/JS/data and pinned release header. Do not claim public source auto-sync or automatic failover beyond the verified gateway.

Github Pages failure was an app authorization block to enable/create Pages (`Resource not accessible by integration`), not a browser or SHA defect. Do not retry the same 403 blindly or buy a new plan. Vercel project creation was 403 and Render new site required billing; they remain optional if future authorized free delivery capacity becomes available.
