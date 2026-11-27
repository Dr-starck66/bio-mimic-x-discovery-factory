# ASTRA SCIENTIFIC NETWORK Ω — deployment audit, 2026-11-26

Vercel: deployment dpl_FUP55qh6ATisVdWDXuGnZHQPRYAP, project prj_WcC3rgz1MH0d25aQWssvYDu5sxKP. New isolated production project on the previously used Hobby team, no paid setting requested. READY, region iad1. Endpoint https://astra-scientific-network-omega.vercel.app/api/verify returned HTTP 200 through the authenticated Vercel fetch connector at 22:08:14 UTC, cache MISS. Report: VERIFIED_HISTORICAL, REJECT, signatures [4,4,4], opening_verified=false, rmse_recomputed=false, bootstrap_recomputed=false, independent_authority=false. Public anonymous access not verified: direct web fetch unavailable; local resolver could not resolve hostname. Error/fatal log query covering the test returned no records. No ongoing monitoring. No proof of new independent attestations or scientific discovery.

Three uploaded source files were fetched from the existing branch and matched local Git object hashes: verifier.mjs 31c76cd11f9fd1cc665840055dadb88852b7b192, capsule.json 26cb15df768f015372d7f8c24cad6ae74bc8d6dc, api/verify.mjs 959ba0c6029720cd0d0b4d0343df01683fc4c6a3. Local API test: six assertions passed.

Cloudflare: WebCrypto adapter tested on Node.js 22, seven assertions passed, including three negative controls. Runtime on Cloudflare not tested. No authorized Workers deployment connector found. No signing key or credentials published.

Hugging Face: authenticated read access, jobs permission; no repo write scope. No paid compute jobs launched. Existing Space lookup for Dr-Starck/hf-zero-worker not found or authentication required; search tool failed. No Space deployment verified.

Render abandoned. Main branch and other production projects untouched. No new subscription purchased. Hosting billing/quota future usage not independently verified. Next: authorized Cloudflare Workers Free deployment and anonymous HTTP check; preserve read-only historical audit mode.
