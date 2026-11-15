# ASTRA ARCHER VISION Ω — gate for truly semantic face-vs-context validation (15 Nov 2026)

**STATUS PARTIAL: software checks PASS, actual semantic-mask biometric experiment NOT RUN.**

## Source and scientific gating
- Official CelebAMask-HQ (Lee et al., CVPR 2020): 30,000 portraits, manual 19-class 512x512 semantic masks for facial parts, hair, cloth and accessories, https://mmlab.ie.cuhk.edu.hk/projects/CelebA/CelebAMask_HQ.html .
- Authoritative CelebA identity annotations are furnished **upon research request**, https://mmlab.ie.cuhk.edu.hk/projects/CelebA.html . Identity labels and independently authenticated camera/session metadata were **not available** to this run. Original dataset licence is **non-commercial research**, source photos/masks must not be redistributed.
- Existing frozen descriptors **unchanged**: `validation/archer_vision_benchmark.py`, blob `0d152b6ecf16c84fcb293d5cc1d00ec8cc88a300`, local SHA-256 `bba639c52bdbf58cfce5d802b8634603a4da7f48f2d9b3c5bbda1c02fdaa4e51`.
- Prepared standalone local *fail-closed* research harness `archer_semantic_mask_gate.py` (SHA-256 `78d78801ab7c0d270b3aa5dc71cec08ea451666fb78e7375dddf26b1e425edd1`) and `test_archer_semantic_mask_gate.py` (SHA-256 `131c1ef0815e22b27abed102e67364aff5d25bfcef6d248b440abeaf7dc5543d`); **14/14 software tests PASS** on synthetic non-personal inputs, 0.391 seconds. Not yet committed as Python modules on this branch; files delivered in the chat ZIP, and hashes retained here.
- Strict input gate checks authorized image-to-original identity mapping, *true* session annotation source, individual picture + discrete mask SHA-256, image deduplication, correct class IDs, and no cross-session sample reuse. Default minimum 25 eligible identities, 100 holdout images. Without required metadata it returns `FAIL_CLOSED_*` rather than inventing scores.
- Fixed conditions: full image; **inner facial structures** (skin, nose, both eyes/eyebrows, mouth/lips; deliberately excluding hair, clothing, background, ears and accessories); exterior only; center from target + context from different donor; uniform negative. No model fitting, no identity-level output or portraits.
- In software, `session_metadata_orthogonally_authenticated` remains explicitly **FALSE**, because an unverified manifest string cannot establish original camera/session provenance.

## Evidence and conclusions
- No actual CelebAMask-HQ images, original identity labels or session annotations were acquired in the authorized computing environment. Therefore **no results on real CelebAMask-HQ individuals are claimed**.
- Earlier FG-NET negative finding retained: internal-only face region was *less* predictive than external context; pure geometric-mask and age-gap results do not prove internal-face recognition.
- Rechecked two Gmail accounts for responses from existing research contacts; primary account had no relevant replies. No duplicate messages sent.
- A **new targeted email** was sent to the official CelebAMask-HQ author contact **chenghan.lee@utexas.edu**, Gmail message `1a1dd121e5912efa`, status `SENT`. Requested appropriate research access to authorized identity linkage, authentic capture sessions, and a defensible protocol. No delivery, permission or response was inferred.
- **Next unique decision gate:** obtain actual authorized identity mapping and reliable session metadata, then run the fully frozen benchmark once under the documented original splits. Do not merge PR or claim fish visual-neural validity from software tests.

**ZERO paid services, ZERO production site changes.**
