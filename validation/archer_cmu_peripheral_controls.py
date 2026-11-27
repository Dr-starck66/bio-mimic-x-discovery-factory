#!/usr/bin/env python3
"""Controlled within-dataset diagnostic of central vs peripheral visual cues.

Research-only: central rectangle was chosen after visual inspection of the
source dataset; it is NOT a landmark-verified face crop or a prospective test.
No individual identities, photos, or embeddings are exported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from validation.archer_vision_benchmark import encode
from validation.archer_vision_real_cmu import TRAIN_VIEWS, TEST_VIEWS, eligible_subjects
from validation.archer_cmu_mirror_audit import load_mirror_tar, MIRROR_SHA256

# Fixed after inspection of a small set of source faces. Encodes eyes, nose,
# and mouth on *many*, but not geometrically registered, portraits.
CORE = (slice(14, 50), slice(17, 47))  # 64 x 64, [row, column]
METHODS = ("pixels", "hog", "retina_pool")
MODES = ("full", "central_only", "central_crop", "central_contrast", "peripheral_only", "border_only", "all_constant")
CONST = np.float32(0.5)


def preprocess(img: np.ndarray, mode: str) -> np.ndarray:
    if mode not in MODES:
        raise ValueError("Unknown mode")
    x = np.asarray(img, dtype=np.float32)
    if x.shape != (64, 64) or not np.isfinite(x).all():
        raise ValueError("Invalid image")
    if mode == "full":
        return x.copy()
    if mode == "all_constant":
        return np.full_like(x, CONST)
    if mode == "central_only":
        out = np.full_like(x, CONST)
        out[CORE] = x[CORE]
        return out
    if mode in ("central_crop", "central_contrast"):
        a = x[CORE]
        if mode == "central_contrast":
            mean = float(a.mean())
            sd = max(float(a.std()), .02)
            a = np.clip(0.5 + (a - mean) / (4.0 * sd), 0, 1)
        return np.array(Image.fromarray(np.uint8(np.round(a * 255))).resize(
            (64, 64), resample=Image.Resampling.BILINEAR), dtype=np.float32) / 255.
    if mode == "peripheral_only":
        out = x.copy()
        out[CORE] = CONST
        return out
    if mode == "border_only":
        out = np.full_like(x, CONST)
        b = 9
        out[:b, :] = x[:b, :]
        out[-b:, :] = x[-b:, :]
        out[:, :b] = x[:, :b]
        out[:, -b:] = x[:, -b:]
        return out
    raise AssertionError(mode)


def _winner(scores: np.ndarray, seed: int) -> int:
    """Uniformly break exact ties; fixed random tie-break, not target-first."""
    vals = np.asarray(scores, dtype=np.float64)
    top = np.flatnonzero(np.isclose(vals, vals.max(), atol=1e-12, rtol=0))
    return int(np.random.default_rng(seed).choice(top))


def evaluate(images: dict, checksums: dict, *, seed: int=20261114) -> dict:
    people, missing = eligible_subjects(images)
    if len(people) < 4:
        raise ValueError("Not enough complete identities")
    if len(checksums) != len(images) or len(set(checksums.values())) != len(checksums):
        raise ValueError("Duplicated or missing raw hashes")
    train=set(TRAIN_VIEWS)
    test=set(sum(TEST_VIEWS.values(),()))
    if train & test:
        raise ValueError("Overlapping views")
    for p in people:
        if {checksums[(p,v)] for v in train} & {checksums[(p,v)] for v in test}:
            raise ValueError("Train/test pixel leakage")
    out = {
        "schema": "ASTRA_ARCHER_CMU_CONTEXT_CONTROL_V1",
        "status": "REAL_MIRROR_EXPLORE_NON_PRESPECIFIED_ROI",
        "source_zip_uci_verified": False,
        "source_mirror_tar_sha256_expected": MIRROR_SHA256,
        "n_complete_subjects": len(people),
        "n_images": len(images),
        "exclusions": missing,
        "training_views": list(TRAIN_VIEWS),
        "test_views": {k:list(v) for k,v in TEST_VIEWS.items()},
        "n_distractors_per_fold": len(people)-2,
        "candidate_count": len(people)-1,
        "chance_top1": round(1/(len(people)-1),6),
        "core_roi_64x64": {"row_start":14,"row_end_exclusive":50,"col_start":17,"col_end_exclusive":47},
        "roi_is_facial_landmarks_verified": False,
        "roi_selected_after_dataset_inspection": True,
        "constant_outside_core": float(CONST),
        "folds_subject_reused": True,
        "methods": {},
        "negative_controls": {},
        "seed": seed,
    }
    for method in METHODS:
        out["methods"][method] = {}
        for mode in MODES:
            embeddings = {k:encode(preprocess(v, mode),method)
                          for k,v in images.items() if k[0] in people}
            results = {}
            for cond,views in TEST_VIEWS.items():
                records = []
                for idx,target in enumerate(people):
                    foil = people[(idx+1) % len(people)]
                    distractors = [p for p in people if p not in (target,foil)]
                    train_feats = np.stack([embeddings[(target,v)] for v in TRAIN_VIEWS])
                    proto = train_feats.mean(axis=0)
                    proto /= max(float(np.linalg.norm(proto)),1e-12)
                    for view in views:
                        # Predefined order ensures target isn't artificially favored
                        # in an all-constant-image negative control.
                        trial_seed = int(hashlib.sha256(
                            f"{seed}|{idx}|{view}".encode()).hexdigest()[:12],16)
                        candidates = [target,*distractors]
                        indices = np.random.default_rng(trial_seed).permutation(len(candidates))
                        candidates = [candidates[j] for j in indices]
                        scores = np.array([float(embeddings[(p,view)] @ proto)
                                           for p in candidates])
                        winner = _winner(scores,trial_seed+1)
                        records.append(int(candidates[winner]==target))
                n=len(records); hits=sum(records)
                results[cond] = {
                    "correct":hits,
                    "total":n,
                    "top1":round(hits/n,6),
                    "per_subject_correct":records[::2] if len(views)==1 else None,
                    "by_fold": [int(sum(records[i*len(views):(i+1)*len(views)]))
                                for i in range(len(people))],
                    "views_per_fold":len(views),
                }
            out["methods"][method][mode] = results
    # Independent simulated labels do not use model scores. They should be
    # contrasted with the all-constant feature negative control.
    rng=np.random.default_rng(seed+17)
    for cond,views in TEST_VIEWS.items():
        n=len(people)*len(views)
        out["negative_controls"][cond]={"random_hits":int(np.sum(rng.integers(0,len(people)-1,n)==0)),
                                           "n":n,"chance":round(1/(len(people)-1),6)}
    # Paired, subject-cluster bootstrap for *descriptive* method contrasts.
    rng=np.random.default_rng(seed+37)
    n_subject=len(people)
    sample=rng.integers(0,n_subject,size=(2000,n_subject))
    for method in METHODS:
        for cond in TEST_VIEWS:
            full=np.array(out["methods"][method]["full"][cond]["by_fold"])/len(TEST_VIEWS[cond])
            core=np.array(out["methods"][method]["central_crop"][cond]["by_fold"])/len(TEST_VIEWS[cond])
            peripheral=np.array(out["methods"][method]["peripheral_only"][cond]["by_fold"])/len(TEST_VIEWS[cond])
            out["methods"][method]["full"][cond]["exploratory_paired_difference_vs_central_crop"] = {
                "mean_full_minus_core":round(float(np.mean(full-core)),6),
                "bootstrap_subject_cluster95": [round(float(x),6) for x in np.quantile((full-core)[sample].mean(axis=1), [.025,.975])],
                "bootstrap_reps":2000,
                "not_confirmatory":True,
            }
            out["methods"][method]["full"][cond]["exploratory_paired_difference_core_minus_periphery"] = {
                "mean":round(float(np.mean(core-peripheral)),6),
                "bootstrap_subject_cluster95": [round(float(x),6) for x in np.quantile((core-peripheral)[sample].mean(axis=1), [.025,.975])],
                "bootstrap_reps":2000,
                "not_confirmatory":True,
            }
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mirror-tar",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    imgs,sha,provenance=load_mirror_tar(args.mirror_tar)
    report=evaluate(imgs,sha)
    report["source"]={k:v for k,v in provenance.items() if k!="rejected"}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    args.out.write_text(payload,encoding="utf-8")
    print(json.dumps({"status":report["status"],
                      "source_sha256":provenance["mirror_tar_sha256"],
                      "report_sha256":hashlib.sha256(payload.encode()).hexdigest(),
                      "summary":{m:{mode:{c:round(v["top1"],3) for c,v in conds.items()}
                                    for mode,conds in modes.items()}
                                 for m,modes in report["methods"].items()}},indent=2))

if __name__=="__main__":main()
