#!/usr/bin/env python3
"""FG-NET exploratory frozen-encoder recognition, manual landmarks; aggregate only.

No training or adaptation of pixels, HOG, retina_pool; two enrolled photos per
person, all remaining photos held out. Research-only, no raw images exported.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from validation.archer_fgnet_manifest_gate import census,parse_points,KEY,IMAGE_EXT
from validation.archer_vision_benchmark import encode

SEED=20261115
MODES=("aligned_full","inner_face_only","outside_inner_face","uniform_negative")
METHODS=("pixels","hog","retina_pool")
MIN_PERSONS=25

def inner_mask():
    ys,xs=np.mgrid[0:64,0:64]
    mask=np.zeros((64,64),dtype=np.float32)
    for x,y,rx,ry in [(20,25,7,5),(44,25,7,5),(32,37,7,9),(32,49,11,5)]:
        d=((xs-x)/rx)**2+((ys-y)/ry)**2
        mask=np.maximum(mask,np.clip((1.2-d)*5,0,1))
    if not 100<mask.sum()<2000:raise ValueError("mask area invalid")
    return mask
MASK=inner_mask()

def preprocess(im:np.ndarray,pts:np.ndarray):
    import cv2
    if im.ndim!=2 or pts.shape!=(68,2) or not np.isfinite(pts).all():
        raise ValueError("Bad photo/landmarks")
    left=pts[27:32].mean(axis=0);right=pts[32:37].mean(axis=0)
    if left[0]>right[0]:left,right=right,left
    dx,dy=right-left
    dist=float(np.hypot(dx,dy))
    if not 8<dist<max(im.shape)*.8:raise ValueError("Eye gap implausible")
    u=np.array([dx,dy],dtype=np.float64)/dist
    R=np.array([[u[0],u[1]],[-u[1],u[0]]])*24/dist
    center=(left+right)/2
    t=np.array([32,25])-R@center
    nose=R@pts[41]+t
    mouth=R@pts[57]+t
    if not(18<nose[0]<46 and 29<nose[1]<47 and 35<mouth[1]<64
           and mouth[1]>nose[1]):raise ValueError("Eye-nose-mouth geometry implausible")
    M=np.concatenate([R,t[:,None]],axis=1).astype(np.float32)
    x=cv2.warpAffine(im.astype(np.float32),M,(64,64),flags=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT,borderValue=.5)
    x=np.clip(x,0,1)
    bg=np.full_like(x,.5)
    return {"aligned_full":x,"inner_face_only":MASK*x+(1-MASK)*bg,
            "outside_inner_face":(1-MASK)*x+MASK*bg,"uniform_negative":bg}

def tie_winner(scores,seed):
    s=np.asarray(scores,dtype=np.float64)
    tied=np.flatnonzero(np.isclose(s,s.max(),atol=1e-11,rtol=0))
    return int(np.random.default_rng(seed).choice(tied))

def evaluate(zip_bytes:bytes):
    manifest=census(zip_bytes)
    if manifest["status"]!="PASS_ACCESS_AND_ANNOTATION_GATE":
        raise ValueError("Annotation integrity gate failure")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        pairs=collections.defaultdict(dict)
        for member in z.infolist():
            path=Path(member.filename)
            if not KEY.search(path.stem):continue
            ext=path.suffix.lower()
            if ext in IMAGE_EXT:pairs[path.stem.upper()]["image"]=member.filename
            if ext==".pts":pairs[path.stem.upper()]["points"]=member.filename
        processed=collections.defaultdict(list)
        rejected=collections.Counter()
        raw_hashes=set()
        for stem,entry in sorted(pairs.items()):
            if "image" not in entry or "points" not in entry:continue
            blob=z.read(entry["image"])
            digest=hashlib.sha256(blob).hexdigest()
            if digest in raw_hashes:
                rejected["duplicate_photo_sha256"]+=1;continue
            raw_hashes.add(digest)
            pts=np.asarray(parse_points(z.read(entry["points"])),dtype=np.float32)
            if pts.shape!=(68,2):
                rejected["wrong_pts_shape"]+=1;continue
            with Image.open(io.BytesIO(blob)) as pic:
                a=np.asarray(pic.convert("L"),dtype=np.float32)/255.
            try:modes=preprocess(a,pts)
            except ValueError:
                rejected["geometric_rejection"]+=1;continue
            p=KEY.search(stem).group("id")
            processed[p].append((stem,modes))
    people=sorted(p for p,items in processed.items() if len(items)>=3)
    report={"schema":"ASTRA_FGNET_ANATOMICAL_CONTEXT_FROZEN_V1",
            "dataset_source":manifest["source_url"],"dataset_zip_sha256":manifest["zip_sha256"],
            "annotations_source":"68 manually annotated points, FG-NET research copy",
            "landmark_index_map":"FGNET-specific: eyes indices 27:32 and 32:37, nose 41, mouth 57 (zero-based)",
            "landmark_index_map_evidence":"1002-sample normalized geometry audit, run 43666239077",
            "landmark_indices_assumed_ibug68":False,"landmark_semantics_independently_verified":False,
            "min_eligible_subjects_preregistered":MIN_PERSONS,"eligible_subjects":len(people),
            "photos_passing_geometry":sum(len(v) for v in processed.values()),
            "rejected":dict(rejected),"methods_frozen":list(METHODS),"modes":list(MODES),
            "enrollment":"first 2 photos by filename (same identity, no test photo training)",
            "same_identities_enrolled_and_tested":True,"identities_not_independent_images":True,
            "no_hair_leakage_guarantee":False,
            "no_portrait_export":True,"commercial_license":"UNVERIFIED",
            "chance_top1":round(1/max(len(people),1),6),"results":{}, "status":"UNVERIFIED"}
    if len(people)<MIN_PERSONS:
        report["status"]="FAIL_CLOSED_INSUFFICIENT_ANATOMICALLY_ALIGNED_SUBJECTS"
        return report
    for method in METHODS:
        report["results"][method]={}
        for mode in MODES:
            prototypes=[]
            for person in people:
                items=sorted(processed[person])
                proto=np.mean([encode(imgs[mode],method) for _,imgs in items[:2]],axis=0)
                prototypes.append(proto/max(float(np.linalg.norm(proto)),1e-9))
            matrix=np.stack(prototypes)
            hits=total=0
            score_hash=hashlib.sha256()
            for p in people:
                for stem,imgs in sorted(processed[p])[2:]:
                    v=encode(imgs[mode],method)
                    scores=matrix@v
                    score_hash.update(np.asarray(scores,dtype="<f4").tobytes())
                    seed=int(hashlib.sha256(f"{SEED}|{mode}|{method}|{stem}".encode()).hexdigest()[:12],16)
                    choice=tie_winner(scores,seed)
                    hits+=int(people[choice]==p)
                    total+=1
            report["results"][method][mode]={"hits":hits,"total":total,
                    "accuracy":round(hits/total,6),"score_sha256":score_hash.hexdigest()}
    report["test_images"]=sum(len(processed[p])-2 for p in people)
    report["status"]="EXPLORATORY_REAL_MANUALLY_ANNOTATED_FACES_EVALUATED_NO_BIOLOGICAL_VALIDATION"
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--zip",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    r=evaluate(a.zip.read_bytes())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":r["status"],"subjects":r["eligible_subjects"],
                      "tests":r.get("test_images"),"rejected":r["rejected"],
                      "results":r["results"]},indent=2))
    if r["status"].startswith("FAIL"):raise SystemExit(3)

if __name__=="__main__":main()
