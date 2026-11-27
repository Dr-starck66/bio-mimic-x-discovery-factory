# ASTRA CRYPTO CONSENSUS Ω — first real CometBFT receipt

Run: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/46084138689
Job: 140789651861 — completed/success.
Artifact: 15237833383 — 18 files, 43408 bytes.
SHA256: 92246ec4777a7e0d12796fa3c72a5689b2a517af99f9015e820be065646410fe
Upstream: CometBFT v0.38.26, commit 94d77f9f51a72e2b7d832798859f6222f08028f8.

- 2026-11-27T23:45:10.1490747Z: height 1, round 0, hash 6B7BD1BC97A1450D69EC610AD70187B5916D096FEC94B8CB01327E3BAADC1258.
- 23:45:11.4232505Z: killed validator E7194A6CBC3BFAB682A66EB87E51430FE5ABFBD4, observed height 3.
- 23:45:19.337Z: height 7, round 0, proposal timeout.
- 23:45:20.541Z: height 7, round 1, new proposer 03003B3410FCEEAA2BDAA0C46E39E8CAF26191E2.
- 23:45:20.963Z: state committed, height 7.
- 23:45:22.4851770Z: verified height 7 round 1 hash 41CA1A742FB4C5D960A85344A5658D1814B637466604BC71776E3DCA485669CB.
- Six surviving peers returned the same signed commit.

Independent Python Ed25519 verification using public keys extracted from all seven validator logs: 8/8 certificate files, 49 signature checks (includes repeated certificates). Six local negative controls rejected: altered hash, round, chain ID, signature, duplicate signer and insufficient quorum. Equal-power rotation reconstructed from observed proposers at heights 1–6 identifies stopped validator as expected round-zero proposer at height 7; direct round-zero identity was not logged. The genesis file was not included in the exported artifact, so independent trust-anchor verification remains incomplete. Upstream verifier used genesis in runner. Reference kvstore app only, classical Ed25519 consensus, all seven processes on one VM. No ASTRA v0.5 application integration or multi-host test claimed. Artifact expires 2026-12-04; retain downloaded archive separately.
