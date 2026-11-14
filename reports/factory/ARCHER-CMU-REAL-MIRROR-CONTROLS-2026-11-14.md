# ASTRA ARCHER VISION Ω — Real-image mirror experiment and adversarial audit (2026-11-14)

**Status: PARTIAL (real-image computation PASS; official UCI ZIP authentication UNVERIFIED; fish-neural mechanism UNVERIFIED).** No deployment, merge, additional emails or paid API.

## Source provenance and strict boundary
- Intended authoritative source: UCI CMU Face Images, DOI https://doi.org/10.24432/C5JC79 (UCI metadata: CC BY 4.0), original 20 people, 640 variations of which 624 are valid.
- Official ZIP source: `https://archive.ics.uci.edu/static/public/124/cmu%2Bface%2Bimages.zip`; **expected but NOT byte-verified ZIP SHA-256:** `01a8b6cc58ac2f825f72abd6cf2b393df067c6529d96f7a90b22dede71b142cc`.
- **Actual executed source:** the quarter-resolution `faces_4.tar.gz` in third-party public GitHub repository `efeerenc/face_orientation_585`, pinned at commit `25984c63f09db08cac5d8ff113bd0963af728406`. Blob SHA1 `618061bbb9563c1cf09da83ee6c106430e843f76`.
- **Mirror TAR SHA-256 computed on received bytes:** `fee2175af429f964d51d4b13cd7c2c23afbbc309edf8d9b84c975d2c1b41e8f4`, 414,060 bytes. All 624 PGMs are distinct, with original resolution 32×30 pixels. This **does not authenticate the official UCI ZIP** or establish a bit-for-bit comparison with its nested TAR.
- 118 selected PGM images, 18 complete identities. `glickman` and `mitchell` excluded because `straight_angry_open` is missing. Exclusion is entirely based on the predeclared six views, not outcomes.
- No raw portraits committed or redistributed; JSON contains hashes and aggregated metrics.

## Protocol
Two enrollment images per enrolled identity (straight neutral and happy, eyes open); other photographs reserved for testing expression, left pose and sunglasses. For every fold, one target and one foil are enrolled, remaining 16 identities serve as unseen distractors. Within each fold **none of the test image hashes are enrolled**. However, the **same identities reappear across the 18 folds**; trial outcomes are correlated and should not be treated as an independent population sample.
Three preexisting encoders: pixels (256 features), HOG (576), Retina-Pool (320). Same images and fold allocations.

## Actually measured Top-1 — real photographs from mirror
| Encoder | Frontal expression (n=36) | Pose changed (n=18) | Sunglasses (n=18) |
|---|---:|---:|---:|
| Pixels | 34/36 = 94.4% | 13/18 = 72.2% | 16/18 = 88.9% |
| HOG | 33/36 = 91.7% | **17/18 = 94.4%** | **17/18 = 94.4%** |
| Retina-Pool | **35/36 = 97.2%** | 15/18 = 83.3% | **17/18 = 94.4%** |

In the pose experiment, **HOG beats Retina-Pool**. No overall-superiority or energy claims. Chance top-1 = 1/17 ≈ 5.88%.

Two-choice trials sharing images and identities (not independent): each 36-expression or 18-pose/sunglasses episode generates 16 pairwise comparisons. See locally generated JSON for raw counts.

## Critical negative-control result (actually computed on photographs)
- **Center occlusion:** pixel region rows 9:55 and columns 12:52 (on the resized 64×64 image) replaced with image median in BOTH training and test views; hair, background and external silhouette remain. Pose-shift top-1 becomes **18/18 = 100%** for **all three encoders**, despite masked facial center. For expression, each becomes 32/36 = 88.9%. This is **evidence of substantial non-central-face cues or dataset confounding**, not proof of human-like face recognition.
- **Permuted-label negative:** for each model and condition, generate 200 random pseudo-target labels among the 16 never-enrolled distractor identities, with true target and foil excluded. Observed 5.50–6.64% depending on method and condition, around 1/16=6.25% chance. These permutations reuse photographs, thus 200 repetitions do not create 200 independent real-image trials.
- The models are **not** proven to use internal facial structures; source photos were taken under controlled conditions with possible subject-specific visual cues.

## Executed commands, retained evidence
```bash
PYTHONPATH=. python validation/archer_cmu_mirror_audit.py --mirror-tar data/CMU_FACES4_GITHUB_MIRROR.tar.gz --out reports/ARCHER-CMU-GITHUB-MIRROR-REAL-RESULTS-20261114.json
PYTHONPATH=. python validation/archer_cmu_mirror_controls.py
PYTHONPATH=. python -m unittest discover -s tests -p 'test_archer*.py' -v
```
- **Local regression: 23/23 tests PASS**, 4.467 seconds. This includes tests that reject substituted mirror bytes.
- Full real-image report SHA-256: `7e57a00c0d3086048a0081cdd48a10185c115aeea93eeabbdfd887f603ffc234`.
- Negative-control report SHA-256: `1af793fa9e8b8c4aeae4f309af5591fbf7b029a1544dd2ec95f93e6ffca3b533`.
- Unit-test log SHA-256: `303a7c7e0c03971a4ca1499ba84e7683986f08c787cb6a9cc17d68226a5af83c`.
- These hashes cover local scripts/results from the executed run. GitHub commit hashes alone do not prove that remote CI ran.

## Follow-up and independent evaluation
Four prior e-mails to UCI, CMU, Oxford and Queensland are already marked SENT in connected Gmail. A fresh inbox search on both connected accounts found **no replies** as of this audit; no duplicate outreach was sent.
**Single next prerequisite:** receive official UCI ZIP or authenticated access, compute its actual SHA-256, verify the nested `faces_4.tar.gz` against mirror content, then rerun. For valid face-discrimination claims, independent photographs with standardized/removed backgrounds or matched non-face cues are also necessary. Do not claim biological validation, clinical application or reduced energy use.
