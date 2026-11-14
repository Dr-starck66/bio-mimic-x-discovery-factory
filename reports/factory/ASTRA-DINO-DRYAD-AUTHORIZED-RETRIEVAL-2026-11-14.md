# ASTRA DINO Ω — Original Dryad access / verification (2026-11-14)

## Objective / result
Get the **three exact original files** from doi:10.5061/dryad.3ffbg79w8 (version 402749), source-verify, join finch individual records, and scan ALX1/HMGA2 without substituting inferred observations.

**Result: PARTIAL — 0/3 original file bodies obtained.**

Two connected Gmail accounts were checked for new replies from the study's corresponding author and Dryad helpdesk on 14 Nov 2026: no matching incoming reply. Two previously sent requests were already confirmed SENT. Do not send duplicate follow-ups without a new reason.

Official Dryad public API supports metadata read access; however, public file endpoints /api/v2/files/{id}/download returned **401** without an API token and /downloads/file_stream/{id} returned **403** in this environment. Searches found no independently verifiable public mirror of these *exact* bytes; scientific PRJNA1261677 SRA reads are an alternative raw-data source but not a verified replacement for the processed VCF or phenotype/sample crosswalk. No access challenge was bypassed.

## Verified official original-file constraints
- Morphometrics.txt — ID 4416574 — 5,295 B — SHA256 4722f565feeda8290d3985b4a65d9e0c4e91690270264cfc931d26f24cc51555
- pPCAeigen.txt — ID 4416577 — 6,421 B — SHA256 d615bd8dd3fd22091b971b20f18a49832d1f2afaf390a30ea3465f6a276b5bff
- Prun64_3miss2mafNoZ_1.vcf.gz — ID 4416598 — 59,719,262 B — SHA256 471db73a5eb65a8bb6af8f25872a5a2d0bc0115556203250f69eb61988163d34

Formal SHA manifest: data/astra_dino_dryad2025_official_sha256_manifest.json.

## Authorized zero-cost access route
Dryad official help:
- https://datadryad.org/help/account/login — account creation uses ORCID and email verification;
- https://datadryad.org/help/account/management — My account → Create a Dryad API account (token lifetime ~10 hours);
- https://github.com/datadryad/dryad-app/blob/main/documentation/apis/api_accounts.md — documentation explicitly requires bearer tokens for API file downloads.

This route **requires the data user's own secure login or an authorized project API account**. A secret must never be pasted in a conversation, email, repository, or artifact. An API token has not been obtained or used in this session. A locally available connected browser requiring prepaid credits was unavailable; we did not buy credits.

## New reusable implementation on the isolated BIO-MIMIC X branch
- validation/astra_dino_dryad_authorized_fetch.py
- tests/test_astra_dino_dryad_authorized_fetch.py

Python standard library only. Streaming downloads; no raw token logging; HTTPS-only redirects; strips authorization on cross-origin redirects; enforces exact file size and SHA-256; refuses tampered files and deletes partial downloads. Requires the user's authorized DRYAD_TOKEN environment variable only for downloads. Has a --verify-only option for already downloaded files. Existing auditor: validation/astra_dino_dryad2025_audit.py.

Local tests on the **exact GitHub blob content**: **10/10 PASS**, blob hashes:
- script adc2301d9a122de4e8a89de1f2bcdfe30238fbb7
- tests d3b972c2b8e8bb9c85fb99f71f3956090ccc1823

Actual download call without token: **FAIL_CLOSED: DRYAD_API_TOKEN_REQUIRED** (expected). No authenticated real-download execution was performed.

## Scientific status
- Official metadata, digests and sources: PASS.
- Secure download and rejection software tests: PASS LOCAL.
- Authorized file retrieval: BLOCKED / NOT DONE.
- Original sample identity joins: UNVERIFIED.
- Original VCF variants in ALX1 or HMGA2: UNVERIFIED.
- Full independent genotype–phenotype model: UNVERIFIED.

**Single next external dependency**: receive an authorized download route from Dryad or authors, or perform user-authorized ORCID/Dryad login to create a free API account. Once originals are acquired, verify all 3 SHA-256 first and execute the existing auditor with assembly-pinned ALX1/HMGA2 coordinates; do not claim a PASS before then.
