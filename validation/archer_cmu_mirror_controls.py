"""Actual-model negative controls on real (mirror-sourced) photographs.

Never uses official UCI ZIP provenance flag. No photographic pixels exported.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
from validation.archer_vision_benchmark import encode
from validation.archer_vision_real_cmu import eligible_subjects, TRAIN_VIEWS, TEST_VIEWS
from validation.archer_cmu_mirror_audit import load_mirror_tar

METHODS = ("pixels", "hog", "retina_pool")


def mask_center(a):
    """Remove central rectangular area, keep outer hair/background (not pure background)."""
    b = a.copy()
    b[9:55, 12:52] = float(np.median(a))
    return b


def controls(images, seed=20261114, repetitions=200):
    eligible, _ = eligible_subjects(images)
    rng = np.random.default_rng(seed)
    result = {
        "schema": "ARCHER_CMU_MIRROR_CONTROLS_V1",
        "seed": seed,
        "repetitions": repetitions,
        "n_subjects": len(eligible),
        "method_results": {},
        "null_design": "pseudo-target uniformly shuffled among novel untrained identities; true target and familiar foil absent",
        "occlusion_design": "center rows 9:55 columns 12:52 replaced with each image's median; outer pixels retained, not a pure background measure",
    }
    for method in METHODS:
        feats = {k: encode(v, method) for k, v in images.items() if k[0] in eligible}
        occluded = {
            k: encode(mask_center(v), method)
            for k, v in images.items() if k[0] in eligible
        }
        stats = {}
        for condition, views in TEST_VIEWS.items():
            total = null_hits = occluded_hits = full_hits = 0
            for i, target in enumerate(eligible):
                foil = eligible[(i + 1) % len(eligible)]
                novel = [p for p in eligible if p not in (target, foil)]
                prototype = np.mean([feats[(target, v)] for v in TRAIN_VIEWS], axis=0)
                prototype /= max(np.linalg.norm(prototype), 1e-12)
                masked_prototype = np.mean(
                    [occluded[(target, v)] for v in TRAIN_VIEWS], axis=0
                )
                masked_prototype /= max(np.linalg.norm(masked_prototype), 1e-12)
                for view in views:
                    candidates = [target, *novel]
                    scores = np.array([
                        float(feats[(p, view)] @ prototype) for p in candidates
                    ])
                    masked_scores = np.array([
                        float(occluded[(p, view)] @ masked_prototype)
                        for p in candidates
                    ])
                    full_hits += int(np.argmax(scores) == 0)
                    occluded_hits += int(np.argmax(masked_scores) == 0)
                    wrong_scores = np.array([
                        float(feats[(p, view)] @ prototype) for p in novel
                    ])
                    pseudo_labels = rng.integers(0, len(novel), size=repetitions)
                    null_hits += int(np.sum(pseudo_labels == np.argmax(wrong_scores)))
                    total += 1
            stats[condition] = {
                "trials": total,
                "original_top1": round(full_hits / total, 6),
                "face_center_occluded_top1": round(occluded_hits / total, 6),
                "face_center_occluded_correct": occluded_hits,
                "randomized_labels_control_trials": total * repetitions,
                "randomized_labels_control_hits": null_hits,
                "randomized_labels_control_top1": round(
                    null_hits / (total * repetitions), 6
                ),
                "randomized_labels_chance": round(1 / (len(eligible) - 2), 6),
                "closed_set_chance": round(1 / (len(eligible) - 1), 6),
            }
        result["method_results"][method] = stats
    return result


if __name__ == "__main__":
    source = Path("data/CMU_FACES4_GITHUB_MIRROR.tar.gz")
    images, _, meta = load_mirror_tar(source)
    report = controls(images)
    report["real_image_source_sha256"] = meta["mirror_tar_sha256"]
    report["official_zip_verified"] = False
    output = Path("reports/factory/ARCHER-CMU-MIRROR-NEGATIVE-CONTROLS-20261114.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    output.write_text(payload)
    print("report_sha256", hashlib.sha256(payload.encode()).hexdigest())
    print(json.dumps(report["method_results"], indent=2))
