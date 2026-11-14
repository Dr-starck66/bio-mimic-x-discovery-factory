#!/usr/bin/env python3
"""ASTRA ARCHER VISION Ω — leak-audited real-image benchmark (UCI CMU Faces).

This research-only benchmark never trains an identity model on test images.
Identity enrollment (2 subjects per fold) necessarily has DIFFERENT photographs
of the same identities at test time. Other 18 identities are entirely unseen.

Does not assert animal-neuroscience validation or suitability for surveillance.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import platform
import tarfile
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

try:
    from validation.archer_vision_benchmark import encode
except ModuleNotFoundError:
    from archer_vision_benchmark import encode

DATASET_URL = "https://archive.ics.uci.edu/static/public/124/cmu%2Bface%2Bimages.zip"
DATASET_SHA256 = "01a8b6cc58ac2f825f72abd6cf2b393df067c6529d96f7a90b22dede71b142cc"
DATASET_DOI = "10.24432/C5JC79"
LICENSE = "CC BY 4.0 (UCI metadata); CMU original explicitly grants free educational use with attribution"
SUBJECTS = (
    "an2i", "at33", "boland", "bpm", "ch4f", "cheyer", "choon", "danieln",
    "glickman", "karyadi", "kawamura", "kk49", "megak", "mitchell",
    "night", "phoebe", "saavik", "steffi", "sz24", "tammo",
)
TRAIN_VIEWS = ("straight_neutral_open", "straight_happy_open")
TEST_VIEWS = {
    "frontal_expression": ("straight_sad_open", "straight_angry_open"),
    "pose_shift": ("left_neutral_open",),
    "sunglasses": ("straight_neutral_sunglasses",),
}
METHODS = ("pixels", "hog", "retina_pool")


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def images_from_zip(path: Path, *, verify_sha: bool = True) -> tuple[dict, dict]:
    """Return only 6 disjoint quarter-resolution photos/subject; fail closed.

    UCI ZIP contains faces_4.tar.gz. Entries are decoded in memory and never
    redistributed. Source verification uses the published UCI ZIP fingerprint.
    """
    blob = path.read_bytes()
    fingerprint = sha256(blob)
    if verify_sha and fingerprint != DATASET_SHA256:
        raise ValueError(f"Official UCI archive SHA-256 mismatch: {fingerprint}")
    imgs, checksums = {}, {}
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = [x for x in archive.namelist() if x.split("/")[-1] == "faces_4.tar.gz"]
        if len(names) != 1:
            raise ValueError(f"Expected exactly one faces_4.tar.gz, got {names}")
        raw_tar = archive.read(names[0])
    with tarfile.open(fileobj=io.BytesIO(raw_tar), mode="r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            base = Path(member.name).name
            if not base.endswith("_4.pgm") or base.endswith(".bad"):
                continue
            person = Path(member.name).parent.name
            if person not in SUBJECTS:
                continue
            for view in TRAIN_VIEWS + sum(TEST_VIEWS.values(), ()):
                if base != f"{person}_{view}_4.pgm":
                    continue
                data = tar.extractfile(member).read()
                label = (person, view)
                if label in imgs:
                    raise ValueError(f"Duplicate sample path for {label}")
                # Actual source image is 32x30; resize 64x64 for all original features.
                with Image.open(io.BytesIO(data)) as im:
                    if im.size != (32, 30):
                        raise ValueError(f"Unexpected PGM dimensions: {member.name}: {im.size}")
                    pixels = np.asarray(im.convert("L").resize((64,64), Image.Resampling.BILINEAR),
                                        dtype=np.float32) / 255.0
                if not np.isfinite(pixels).all():
                    raise ValueError("Non-finite pixel values")
                imgs[label] = pixels
                checksums[label] = sha256(data)
    source = {"url":DATASET_URL, "doi":DATASET_DOI, "license":LICENSE,
              "archive_sha256":fingerprint, "archive_sha_verified": fingerprint == DATASET_SHA256,
              "raw_images_in_selected_views":len(imgs), "quarter_resolution": [32,30],
              "processed_size":[64,64]}
    return imgs, {"source":source, "sha256_by_sample":checksums}


def eligible_subjects(imgs: dict) -> tuple[list[str], dict]:
    selected, exclusions = [], {}
    required = TRAIN_VIEWS + sum(TEST_VIEWS.values(), ())
    for person in SUBJECTS:
        missing = [v for v in required if (person,v) not in imgs]
        if missing:
            exclusions[person] = missing
        else:
            selected.append(person)
    return selected, exclusions


def wilson(correct: int, n: int, z: float=1.96) -> list[float]:
    if n <= 0: return [0,1]
    p=correct/n
    d=1+z*z/n
    m=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return [round(m-h,6),round(m+h,6)]


def compare(*, images: dict, checksums: dict, seed: int=20261114, verified_source: bool=False) -> dict:
    rng = np.random.default_rng(seed)
    eligible, exclusions = eligible_subjects(images)
    if len(eligible) < 4:
        raise ValueError(f"Insufficient complete real identities: {len(eligible)} (<4)")
    if len(set(checksums.values())) != len(checksums):
        raise ValueError("Duplicate raw images detected; leakage/near-duplicate audit required")
    # No photographed image may be simultaneously enrolled and evaluated.
    for person in eligible:
        tr = {checksums[(person,v)] for v in TRAIN_VIEWS}
        te = {checksums[(person,v)] for v in sum(TEST_VIEWS.values(),())}
        if tr & te:
            raise ValueError(f"Train/test leakage for identity {person}")
    if set(TRAIN_VIEWS) & set(sum(TEST_VIEWS.values(),())):
        raise ValueError("View-level train/test leakage")

    # Pre-extract once per input image. 2 enrolled identities per fold. The
    # remaining identities are never in that fold's training set.
    vectors = {method:{key:encode(image,method) for key,image in images.items() if key[0] in eligible}
               for method in METHODS}
    out={"schema":"ASTRA_ARCHER_CMU_REAL_V1", "status":"REAL_DATA_PASS" if verified_source else "FIXTURE_ONLY",
         "dataset":"CMU Face Images, UCI dataset 124", "dataset_doi":DATASET_DOI,
         "source_verified":verified_source,"methods":{},"eligible_identities":len(eligible),
         "subjects_total_in_source":20,"excluded_incomplete_subjects":exclusions,
         "train_views":list(TRAIN_VIEWS),"test_views":{k:list(v) for k,v in TEST_VIEWS.items()},
         "folds":len(eligible),"novel_identities_per_fold":len(eligible)-2,
         "closed_set_choices":len(eligible)-1,"chance_closed_set":1/(len(eligible)-1),
         "chance_2afc":0.5,"folds_reference":"2 enrolled, all others unseen per fold",
         "train_test_split":"disjoint source filenames AND disjoint image SHA-256",
         "all_input_sha256_unique":True,"negative_controls":{},
         "software":{"python":platform.python_version(),"numpy":np.__version__}}
    for method in METHODS:
        feats=vectors[method]
        by_condition={}
        for condition,views in TEST_VIEWS.items():
            rows=[]
            for i,target in enumerate(eligible):
                foil=eligible[(i+1)%len(eligible)]
                novel=[p for p in eligible if p not in (target,foil)]
                target_proto = np.mean([feats[(target,v)] for v in TRAIN_VIEWS],axis=0)
                target_proto /= max(float(np.linalg.norm(target_proto)),1e-12)
                foil_proto = np.mean([feats[(foil,v)] for v in TRAIN_VIEWS],axis=0)
                foil_proto /= max(float(np.linalg.norm(foil_proto)),1e-12)
                for view in views:
                    # The target's test photo was not used in the prototype.
                    scores=np.array([float(feats[(p,view)] @ target_proto) for p in [target,*novel]])
                    # Rank of learned face among n-1 unseen persons.
                    rank = 1+int(np.sum(scores[1:]>=scores[0]))
                    select_correct=int(np.sum(scores[0]>scores[1:]))
                    foil_scores=np.array([float(feats[(p,view)] @ foil_proto) for p in [foil,*novel]])
                    # Avoid foil: lower similarity to the learned foil is desirable.
                    avoid_correct=int(np.sum(foil_scores[0]>foil_scores[1:]))
                    rows.append({"fold":i,"view":view,"rank":rank,"select_correct":select_correct,
                                 "avoid_correct":avoid_correct,"top1":int(rank==1),
                                 "pairs":len(novel)})
            n=len(rows); k=sum(r["top1"] for r in rows)
            pairs=sum(r["pairs"] for r in rows)
            select=sum(r["select_correct"] for r in rows)
            avoid=sum(r["avoid_correct"] for r in rows)
            by_condition[condition]={"episodes":n, "top1_correct":k,
                  "top1_accuracy":round(k/n,6),"top1_wilson95_exploratory":wilson(k,n),
                  "two_choice_pairs_correlated":pairs,
                  "select_familiar_correct":select,"select_familiar_accuracy":round(select/pairs,6),
                  "avoid_familiar_correct":avoid,"avoid_familiar_accuracy":round(avoid/pairs,6),
                  "mean_rank":round(float(np.mean([r["rank"] for r in rows])),4),
                  "per_subject_top1":[round(float(np.mean([r["top1"] for r in rows if r["fold"]==f])),4)
                                        for f in range(len(eligible))]}
        out["methods"][method]=by_condition
    # Negative control: independent simulated coin flips for 2AFC and randomly
    # permuted target indices for multi-choice; not models' predictive output.
    for cond,views in TEST_VIEWS.items():
        episodes=len(eligible)*len(views)
        pairs=episodes*(len(eligible)-2)
        out["negative_controls"][cond]={"null_top1_hits":int(sum(rng.integers(len(eligible)-1)==0 for _ in range(episodes))),
                                        "null_two_choice_hits":int(rng.binomial(pairs,0.5)),
                                        "episodes":episodes,"pairs":pairs,
                                        "expected_top1":1/(len(eligible)-1),
                                        "expected_2afc":0.5}
    return out


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,default=Path("data/cmu+face+images.zip"))
    parser.add_argument("--download",action="store_true",help="Allow fetch of official public UCI archive")
    parser.add_argument("--seed",type=int,default=20261114)
    parser.add_argument("--out",type=Path,default=Path("reports/factory/ARCHER-CMU-REAL-LATEST.json"))
    args=parser.parse_args()
    if not args.archive.exists() and args.download:
        args.archive.parent.mkdir(parents=True,exist_ok=True)
        with urllib.request.urlopen(DATASET_URL,timeout=60) as response:
            content=response.read(32*1024*1024+1)
        if len(content)>32*1024*1024:
            raise ValueError("Archive unexpectedly large")
        if sha256(content)!=DATASET_SHA256:
            raise ValueError("Official archive fingerprint failed; refusing to cache")
        args.archive.write_bytes(content)
    if not args.archive.exists():
        raise FileNotFoundError("REAL_DATA_UNAVAILABLE: official zip absent; specify --archive or --download")
    images,meta=images_from_zip(args.archive,verify_sha=True)
    out=compare(images=images,checksums=meta["sha256_by_sample"],seed=args.seed,verified_source=True)
    out["provenance"]=meta["source"]
    out["archive_user_supplied"]=not args.download
    args.out.parent.mkdir(parents=True,exist_ok=True)
    report=json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    args.out.write_text(report,encoding="utf-8")
    print(json.dumps({"status":out["status"],"report":str(args.out),
                     "sha256":sha256(report.encode()),"identities":out["eligible_identities"]},indent=2))

if __name__=="__main__":main()