# BIO-MIMIC X — ASTRA ARCHER VISION Ω

## Final scope of this experiment (15 November 2026)

**PASS (execution)**: three fixed descriptors ran on 118 genuine CMU face photographs (18 complete identities). The UCI original ZIP fingerprint, the nested `faces_4.tar.gz`, and the complete set of 624 PGM files were verified bit-for-bit in a previous independent GitHub Actions run [43651677560](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43651677560). During this local run, the same fingerprint-pinned TAR was reloaded and its SHA-256 recomputed.

**PARTIAL (scientific conclusion)**: no robust face-only recognition under pose changes has been demonstrated. CMU photographs were originally 32×30 pixels; the two **fixed geometrical ellipses are NOT facial landmark segmentations**, and can retain residual hair/shape cues. Their parameters were chosen after inspection of some CMU pictures; the evaluation is exploratory and is not a blind confirmatory hold-out. Face and background composite interventions do not create newly acquired natural photographs.

## Experimental controls

- No retraining or tuning: same fixed encoders `pixels`, `hog`, `retina_pool` used across all modes.
- Strict ellipse: central `(32,33)`, radius `(11,14)` within 64×64 bilinear resized images, with feathered 2px boundary. Broader ellipse: radius `(15,19)`.
- Two enrollment images per target identity (neutral/happy frontal); disjoint unseen evaluation photographs (sad/angry frontal, left pose, sunglasses).
- For each of 18 identity folds, one already familiar foil identity excluded, and 16 untrained distractors; 17 candidates, chance 5.88%.
- Same neutral gray background assigned to all images in enrollment/testing (`neutral_flat`), or one **common donor** background (`shared_background`). Thus the pixels outside the mask are identical for candidates, although seam effects and residual hair in mask remain.
- Adversarial background swaps: replace outside-mask pixels for every candidate with background from another identity; cyclic shift offsets 1/3/7 ensure **no candidate retains its own background**. Count whether chosen candidate's central face matches target versus whether its background donor matches target. Compare old full-image enrollment to gray-background enrollment.
- Negative baseline: random identity selection; no photographs or embeddings redistributed.
- Repeated identity folds, pairs, and three swaps are correlated; do not treat 108 trials as 108 independent people.

## Exact measured results (strict central ellipse)

| Method | Face-only gray, expressions | Face-only gray, pose | Face-only gray, sunglasses | Full-enrollment adversarial face hits (expressions) | Adversarial background-following hits (expressions) |
|--|--:|--:|--:|--:|--:|
| Pixels | 21/36 | 3/18 | 4/18 | 2/108 | 102/108 |
| HOG | 24/36 | 1/18 | 8/18 | 1/108 | 100/108 |
| Retina-Pool | 24/36 | 1/18 | 5/18 | 1/108 | 105/108 |

When backgrounds are permuted, the old full-image templates overwhelmingly follow **the other person's background** rather than the target face. Under strict gray-background enrollment, 108 correlated swapped-expression tests give face-owner hits 18 (Pixels), 18 (HOG), 12 (Retina-Pool), while old full-image training gives 2, 1, 1. This shows that changing the **training** image protocol matters; it does not solve pose robustness.

The broad mask gives higher expression scores (25/36 Pixels, 29/36 HOG, 27/36 Retina-Pool), but retains more hair/background edge cues by construction. With the strict ellipse and pose change, HOG and Retina-Pool achieve only 1/18 (5.6%), indistinguishable descriptively from chance (1/17≈5.88%).

## Reproducibility and evidence

- Local complete Python `unittest` suite: **47/47 PASS** (includes nine new counterfactual tests and two new ZIP extraction safety tests).
- SHA-256 of result JSON: `0958fafb102da9c8a56206f12f08b36d23a1241bdfc9397c3a9bcaca9f826697`.
- Verified source TAR SHA-256: `fee2175af429f964d51d4b13cd7c2c23afbbc309edf8d9b84c975d2c1b41e8f4`.
- Published official ZIP SHA-256 (originally verified in GitHub runner): `01a8b6cc58ac2f825f72abd6cf2b393df067c6529d96f7a90b22dede71b142cc`.
- GitHub files and locally executed code checked with Git blob SHA-1: `validation/archer_cmu_counterfactual_faces.py` = `6e9523730faceac40af965471e49fd6e5864d8f0`, `tests/test_archer_cmu_counterfactual_faces.py` = `7cdb3cfcc6b3f5f80bbd139e5b93c7c786306e50`.
- Run from an existing repository checkout with source TAR **not committed**:

```bash
python -m unittest discover -s tests -p 'test_archer*.py' -v
python -m validation.archer_cmu_counterfactual_faces --mirror-tar data/CMU_FACES4_GITHUB_MIRROR.tar.gz --out reports/factory/ARCHER-FACE-VS-CONTEXT-20261115.json
```

With an original UCI ZIP already downloaded, run the checked extract helper first:

```bash
python -m validation.archer_cmu_extract_official_tar --official-zip data/cmu+face+images.zip --out data/CMU_FACES4_GITHUB_MIRROR.tar.gz
```

Neither this bundle nor the Github commits contain photographic bytes. All scores are **research-only**, not biometric identification performance claims for deployment or comparisons with fish neural circuitry.

## Decision

**Factual conclusion:** the models exploit non-face peripheral cues on CMU. There is measurable discrimination of some fixed central image content under expression changes, but anatomical facial specificity and invariance to pose have **NOT** been shown. The decisive next scientific experiment is an independent, pre-registered, multi-session image set where hair, background, clothing and capture device are controlled and true facial landmarks or consented segmentation masks are available.