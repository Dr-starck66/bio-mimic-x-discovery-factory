# ASTRA ARCHER VISION Ω — UCI CMU original ZIP authenticated (15 Nov 2026)

**PASS — data-source provenance**. This record refers to actual byte-level checks on a GitHub-hosted Ubuntu runner and supersedes the previous `UNVERIFIED` label for the *official ZIP only*.

## Verifiable execution
- GitHub Actions run: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43651677560
- Job ID: `132621307897`, completed successfully.
- Exact run commit: `ff9bc77785868f6de79ed3872236f0be174e7308`.
- Source URL: `https://archive.ics.uci.edu/static/public/124/cmu%2Bface%2Bimages.zip`
- **Original ZIP bytes downloaded on runner: 21,390,594.**
- Original ZIP SHA-256 (measured): `01a8b6cc58ac2f825f72abd6cf2b393df067c6529d96f7a90b22dede71b142cc`; matches independently pinned expected SHA.
- Inside the original ZIP, `faces_4.tar.gz` SHA-256: `fee2175af429f964d51d4b13cd7c2c23afbbc309edf8d9b84c975d2c1b41e8f4`.
- Pinned mirror `faces_4.tar.gz` SHA-256: same digest.
- Inner TAR and mirror: **bytewise equality TRUE**.
- PGM census **624 original / 624 mirror**; **all PGM byte hashes equal**, **0 missing**, **0 extraneous**, **0 changed**.
- Explicit machine status: `PASS_OFFICIAL_ZIP_VERIFIED`.
- Proof JSON SHA-256: `bd0729b82238093ada2f3911057fd816f112e1e311b7d7e0416fb698cfd6673d`.
- Uploaded GitHub Actions proof artifact `14135144942`; ZIP SHA-256 `e4868df516ed0845583ddc142c0ba5ef7e5d4667905a3d9425ec728c5d5b4506`; seven-day retention.
- Exact JSON now committed to `reports/factory/ARCHER-CMU-OFFICIAL-UCI-VERIFIED-2026-11-15.json`, Git blob SHA `09b38eec80840954356a8a2731d1d7c728a2a594` (matches downloaded artifact contents).

## Scientific boundary
The previous third-party mirror's 624 original quarter-size photographs are identical to those inside the official UCI ZIP, so **the prior experiment used the authentic dataset bytes**. The original ZIP was fetched in a temporary GitHub runner, not rehosted or copied into this repository. This establishes dataset provenance only.

The existing full-image results were substantially confounded by peripheral image pixels: background/border-only recognition attained 18/18 in a same-dataset pose test whereas stricter center cropping reduced accuracy. **No validated model of the fish visual system, independent generalization, facial-identity specificity, or energy efficiency has been demonstrated.**

The existing pull request remains a draft with no production merge.
