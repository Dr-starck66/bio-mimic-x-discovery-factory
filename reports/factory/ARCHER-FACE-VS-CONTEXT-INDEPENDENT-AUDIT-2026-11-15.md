# ASTRA ARCHER VISION Ω — FACE-VS-CONTEXT SCIENTIFIC AUDIT (15 November 2026)

**Scientific verdict: PARTIAL (face-region signal measured; face-specific, context-invariant recognition NOT demonstrated).**

## Evidence and source authentication

The 624 valid PGM photographs in UCI CMU Face Images have identical SHA-256 contents to a pinned GitHub mirror. Original UCI ZIP SHA-256 `01a8b6cc58ac2f825f72abd6cf2b393df067c6529d96f7a90b22dede71b142cc`; nested/mirror TAR SHA-256 `fee2175af429f964d51d4b13cd7c2c23afbbc309edf8d9b84c975d2c1b41e8f4`; real byte-level GitHub run https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43651677560. Neither this audit bundle nor the GitHub code contains raw face images.

## Controlled manipulation: CMU 18 eligible identities

Three immutable descriptors (pixels, HOG, ASTRA Retina-Pool) evaluated on the same 118 photographs, with two enrollment views per identity and separate test photographs. Per fold: one target, one excluded familiar foil and 16 unseen distractors = 17 choices (chance 5.88%). Core elliptical masks are geometric, selected after inspection of some CMU photos, **not anatomical facial landmark segmentation**; this is exploratory, not a registered blind confirmatory trial. Three nonzero cyclic swaps of source backgrounds provide repeated correlated tests, not three independent participant trials.

| Method | Strict center only: changed expression (36) | Strict center only: changed pose (18) | Swapped (original full-image enrollment): correct face (108) | Swapped: model picks correct background donor (108) |
|---|---:|---:|---:|---:|
| Pixels | 21 | 3 | 2 | 102 |
| HOG | 24 | 1 | 1 | 100 |
| Retina-Pool | 24 | 1 | 1 | 105 |

With the original, context-containing enrollment photos, every method systematically follows background identity. In contrast, the isolated center contains some useful signal for same-pose expression changes. All methods fail to establish robust pose-invariant recognition when only this central region is used. Broader masks improve expression counts but retain more potentially non-face information.

Original local analysis JSON SHA-256: `0958fafb102da9c8a56206f12f08b36d23a1241bdfc9397c3a9bcaca9f826697`.

## Independent corpus: AT&T/Olivetti, 40 identities

Existing algorithms and geometrical masks were frozen **before** this additional corpus was evaluated. Source documented by AT&T Laboratories Cambridge: https://cam-orl.co.uk/facedatabase.html ; scikit-learn distributed low-resolution 64x64 images via `fetch_olivetti_faces`. 400 total images = 40 persons x 10 photos, using 2 samples per identity for enrollment and 8 disjoint samples for testing (320 target trials); chance 1/40=2.5%. This is a separate corpus, not an identity-disjoint challenge where the subjects have never been enrolled. Original Cambridge file bytes are not separately cryptographically authenticated; scikit-learn provenance is not an original-file checksum proof.

| Method | Full images (320) | Strict center only (320) | Everything outside strict center (320) |
|---|---:|---:|---:|
| Pixels | 211 (65.9%) | 118 (36.9%) | 206 (64.4%) |
| HOG | 248 (77.5%) | 140 (43.8%) | 249 (77.8%) |
| Retina-Pool | 217 (67.8%) | 149 (46.6%) | 210 (65.6%) |

Random-label control 2/320 (chance 2.5%); full 400-image input hash aggregate recorded in JSON. All 3 methods x 4 modes were executed, with result schema and SHA-256 verified by independent GitHub Actions job: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43658826483 . ORL result JSON SHA-256 `d36d7d7129c9b2d7428216cfaa17ce773f69d3dabdd4a0b785ed06d319cf0951` and exact source JSON preserved on GitHub, commit SHA-1 blob `81aec537edefe38b9647ce648c0d1aebd98ee6bd`.

Even a near-uniform dark backdrop does not fix confounding: outside-only still predicts identities better than center-only. This could come from hair, head contour, ears, capture conditions or other cues. The strict central ROI could itself preserve some non-inner-face cues, and was not landmark-validated. No conclusion of pure facial-feature recognition, supremacy of retinal model, faithful fish biology or energetic gains follows.

## Tests, published code, isolation, and next gate

Local regression against authentic CMU TAR: **47/47 tests PASS** including negative/identity-leak checks and original ZIP fail-closed extraction helper. Code of the new adversarial experiment and tests was read back from the user's GitHub isolated PR #54 and its Git blob hashes matched locally executed source. Independent ORL action: **PASS on GitHub**; not a local run. PR remains DRAFT, not merged to main or deployed. Additional spend: 0 €.

**One required scientific next gate:** use a prospectively selected independent cohort with reliably registered eye/nose/mouth landmarks or consented anatomical segmentation masks and controlled or randomized hair, background, clothing and capture session, and evaluate the existing frozen models *before* any tuning on that test cohort. Preserve both favorable and unfavorable controls.