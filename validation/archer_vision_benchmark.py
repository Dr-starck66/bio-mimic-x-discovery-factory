#!/usr/bin/env python3
"""ASTRA ARCHER VISION Ω: offline synthetic, face discrimination benchmark.

Fish-inspired is an engineering analogy (retinal contrast + orientation filters +
spatial pooling), NOT a biologically validated model of Toxotes neural circuits.
All portraits are procedurally generated and contain no personal/biometric data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter, sobel

N_NOVEL = 44
N_CHOICES = N_NOVEL + 1
SIZE = 64
METHODS = ("pixels", "hog", "retina_pool")
CONDITIONS = ("matched", "shifted")


def _identity_traits(identity: int, seed: int) -> np.ndarray:
    """Stable morphology; all geometry comes from a separate identity seed."""
    if not (0 <= identity < N_NOVEL + 2):
        raise ValueError("identity out of range")
    rng = np.random.default_rng(np.random.SeedSequence([seed, 71, identity]))
    return rng.uniform(-1, 1, size=12)


def make_portrait(identity: int, seed: int, view: int, *, condition: str = "matched",
                  identity_override: int | None = None) -> np.ndarray:
    """Return 64x64 synthetic grayscale portrait. No photo or dataset download."""
    if condition not in CONDITIONS:
        raise ValueError("unknown condition")
    if view < 0:
        raise ValueError("negative view")
    t = _identity_traits(identity if identity_override is None else identity_override, seed)
    rng = np.random.default_rng(np.random.SeedSequence([seed, 331, identity, view,
                                                         1 if condition == "shifted" else 0]))
    im = Image.new("L", (SIZE, SIZE), 58)
    d = ImageDraw.Draw(im)
    cx, cy = 32, 33
    halfwidth = 17 + 3.2*t[0]
    halfheight = 23 + 2.8*t[1]
    complexion = int(165 + 16*t[2])
    d.ellipse((cx-halfwidth, cy-halfheight, cx+halfwidth, cy+halfheight), fill=complexion,
              outline=110, width=2)
    # Hair silhouette, ears and facial proportions vary independently by identity.
    d.arc((cx-halfwidth+1, cy-halfheight+1, cx+halfwidth-1, cy+halfheight-2),
          180, 359, fill=int(55+22*t[4]), width=int(3+2*(t[4]+1)))
    d.ellipse((cx-halfwidth-4, cy-3, cx-halfwidth+1, cy+7), fill=complexion)
    d.ellipse((cx+halfwidth-1, cy-3, cx+halfwidth+4, cy+7), fill=complexion)
    eye_y = int(27 + 3*t[5])
    eye_dx = 7 + 3*t[6]
    eye_r = 2.0 + 0.9*(t[7]+1)/2
    for sign in (-1,1):
        ex = cx + sign*eye_dx
        d.ellipse((ex-eye_r,eye_y-eye_r,ex+eye_r,eye_y+eye_r),fill=35)
        by = eye_y-5-2*t[8]
        d.line((ex-4,by+sign*t[9],ex+4,by-sign*t[9]),fill=70,width=2)
    nose_len = 6.2 + 3*t[10]
    d.line((cx+1,eye_y+2,cx-1,eye_y+nose_len),fill=97,width=2)
    mouth_y = int(43 + 3*t[11])
    mouth_top=mouth_y-2*t[9]
    mouth_bottom=max(mouth_top+1,mouth_y+3+2*t[10])
    d.arc((cx-7-2*t[8],mouth_top,cx+7+2*t[8],mouth_bottom),
          5,175,fill=82,width=2)
    im = im.filter(ImageFilter.GaussianBlur(0.55))
    if condition == "shifted":
        angle = float(rng.uniform(-10,10))
        im = im.rotate(angle,resample=Image.Resampling.BILINEAR,fillcolor=58)
    # Distinct seeds for training (views < 1000) and test (views >= 1000).
    max_shift = 1 if condition == "matched" else 5
    dx,dy = rng.integers(-max_shift,max_shift+1,size=2)
    im = Image.fromarray(np.roll(np.roll(np.asarray(im),int(dx),axis=1),int(dy),axis=0))
    a = np.asarray(im,dtype=np.float32) / 255.0
    if condition == "shifted":
        x = np.linspace(-1.0, 1.0, SIZE, dtype=np.float32)[None,:]
        a = a * float(rng.uniform(0.65,1.32)) + float(rng.uniform(-0.12,0.12))
        a = a + float(rng.uniform(-0.2,0.2))*x
    a = np.clip(a+rng.normal(0,0.025 if condition == "shifted" else 0.012,a.shape),0,1)
    return a.astype(np.float32)


def _l2(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a,dtype=np.float32).ravel()
    norm = np.linalg.norm(a)
    return a / max(norm,1e-9)


def _hist_gradient(im: np.ndarray, bins: int = 9) -> np.ndarray:
    """Conventional non-learned HOG reference, 8x8 cells (not a fitted model)."""
    gx=sobel(im,axis=1,mode="reflect")
    gy=sobel(im,axis=0,mode="reflect")
    direction = np.mod(np.arctan2(gy,gx),np.pi)
    magnitude = np.hypot(gx,gy)
    result = np.zeros((8,8,bins),dtype=np.float32)
    for row in range(8):
        for col in range(8):
            aa=direction[row*8:(row+1)*8,col*8:(col+1)*8].ravel()
            ww=magnitude[row*8:(row+1)*8,col*8:(col+1)*8].ravel()
            result[row,col] = np.histogram(aa,bins=bins,range=(0,np.pi),weights=ww)[0]
    # Cell-local contrast normalization prevents one bright region dominating.
    result /= np.maximum(np.linalg.norm(result,axis=2,keepdims=True),1e-8)
    return _l2(result)


def _retina_pool(im: np.ndarray) -> np.ndarray:
    """Engineering-inspired center/surround -> orientation selectivity -> pooling.

    Deliberately lightweight fixed filters; no artificial claims of a real
    fish visual-connectome reconstruction or energy efficiency.
    """
    center=gaussian_filter(im,sigma=0.7,mode="reflect")
    surround=gaussian_filter(im,sigma=2.5,mode="reflect")
    contrast=center-surround
    gx=sobel(contrast,axis=1,mode="reflect")
    gy=sobel(contrast,axis=0,mode="reflect")
    channels=[]
    for theta in (0,np.pi/4,np.pi/2,3*np.pi/4):
        signal=np.abs(np.cos(theta)*gx+np.sin(theta)*gy)
        # Local pooling onto two spatial scales; 8x8 grids retain face geometry.
        for cells in (8,4):
            block=SIZE//cells
            pooled=signal.reshape(cells,block,cells,block).mean(axis=(1,3))
            channels.append(pooled.ravel())
    return _l2(np.concatenate(channels))


def encode(im: np.ndarray, method: str) -> np.ndarray:
    if im.shape != (SIZE,SIZE) or not np.isfinite(im).all():
        raise ValueError("invalid image")
    if method == "pixels":
        # Equal input resolution but fewer dimensions; a strong simple reference.
        smooth=gaussian_filter(im,sigma=1.0,mode="reflect")
        return _l2(smooth.reshape(16,4,16,4).mean(axis=(1,3))-smooth.mean())
    if method == "hog":
        return _hist_gradient(im)
    if method == "retina_pool":
        return _retina_pool(im)
    raise ValueError("unsupported method")


def _score(candidates: np.ndarray, target: np.ndarray, method: str) -> np.ndarray:
    proto=np.mean(np.stack([encode(a,method) for a in target]),axis=0)
    proto=_l2(proto)
    embeddings=np.stack([encode(a,method) for a in candidates])
    return embeddings@proto


def _wilson(successes:int, total:int, z:float=1.96) -> list[float]:
    if total <= 0:
        return [0,1]
    p=successes/total
    denom=1+z*z/total
    middle=(p+z*z/(2*total))/denom
    radius=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denom
    return [round(middle-radius,6),round(middle+radius,6)]


def benchmark(*,seed:int=20261114,episodes:int=24,shots:int=6, identity_ablated:bool=False) -> dict:
    if episodes < 2 or shots < 1 or seed < 0:
        raise ValueError("invalid configuration")
    started=time.perf_counter()
    output={"schema":"ASTRA_ARCHER_VISION_V1", "status":"SOFTWARE_BENCHMARK_ONLY",
            "seed":seed,"episodes_per_condition":episodes,"shots":shots,
            "source":"procedural synthetic portraits", "real_faces":False,"identity_ablated":identity_ablated,
            "train_ids":[0,1],"novel_test_ids":list(range(2,46)),
            "identities_total":46,"choices_per_episode":45,"chance_45way":1/45,"chance_2afc":0.5,
            "disjoint_train_test_view_ranges":True,"methods":{},"negative_controls":{},
            "dependencies":{"numpy":np.__version__,"python":platform.python_version()}}
    # Distinct portrait viewing contexts for learned target 0 and familiar foil 1.
    # Foil is explicitly rendered for protocol provenance; target-only matching
    # uses neither the foil prototype nor any novel-subject data for fitting.
    train=np.stack([make_portrait(0,seed,i,identity_override=0 if identity_ablated else None) for i in range(shots)])
    familiar=np.stack([make_portrait(1,seed,i,identity_override=0 if identity_ablated else None) for i in range(shots)])
    output["training_images"]={"target":len(train),"familiar_foil":len(familiar)}
    rng = np.random.default_rng(np.random.SeedSequence([seed,993]))
    for condition in CONDITIONS:
        # Precompute test views: exactly one target + 44 never-before-seen distractor identities.
        test_episodes=[]
        for episode in range(episodes):
            ids=np.arange(46,dtype=int)[np.r_[0,np.arange(2,46)]]
            rng.shuffle(ids)
            test_episodes.append((ids,make_portrait(1,seed,1000+episode,condition=condition,identity_override=0 if identity_ablated else None),np.stack([
                make_portrait(int(identity),seed,1000+episode,condition=condition,identity_override=0 if identity_ablated else None)
                for identity in ids
            ])))
        for method in METHODS:
            tic=time.perf_counter()
            predicted=[]; margins=[]; ranks=[]; score_hash=hashlib.sha256()
            select_counts=[]; avoid_counts=[]
            prototype=_l2(np.mean(np.stack([encode(a,method) for a in train]),axis=0))
            foil_prototype=_l2(np.mean(np.stack([encode(a,method) for a in familiar]),axis=0))
            for ids,foil_image,images in test_episodes:
                feats=np.stack([encode(im,method) for im in images])
                scores=feats@prototype
                true_index=int(np.flatnonzero(ids==0)[0])
                choice=int(np.argmax(scores))
                order=np.argsort(-scores,kind="stable")
                predicted.append(int(ids[choice])==0)
                ranks.append(int(np.flatnonzero(order==true_index)[0])+1)
                margins.append(float(scores[true_index]-max(np.delete(scores,true_index))))
                score_hash.update(np.asarray(scores,dtype="<f4").tobytes())
                novel_scores=scores[ids!=0]
                select_counts.append(int(np.sum(scores[true_index] > novel_scores)))
                foil_test_score=float(encode(foil_image,method)@foil_prototype)
                unseen_foil_scores=feats[ids!=0]@foil_prototype
                avoid_counts.append(int(np.sum(foil_test_score > unseen_foil_scores)))
            wins=sum(predicted)
            output["methods"].setdefault(method,{})[condition]={
                "correct":wins,"total":episodes,"top1_accuracy":round(wins/episodes,6),
                "wilson95":_wilson(wins,episodes),"mean_target_rank":round(float(np.mean(ranks)),3),
                "mean_target_margin":round(float(np.mean(margins)),6),
                "score_sha256":score_hash.hexdigest(),
                "two_choice_select_familiar_correct":sum(select_counts),
                "two_choice_select_familiar_accuracy":round(sum(select_counts)/(episodes*N_NOVEL),6),
                "two_choice_avoid_familiar_correct":sum(avoid_counts),
                "two_choice_avoid_familiar_accuracy":round(sum(avoid_counts)/(episodes*N_NOVEL),6),
                "two_choice_total_pairs":episodes*N_NOVEL,
                "two_choice_chance":0.5,
                "feature_dim":len(prototype),
                "elapsed_seconds":round(time.perf_counter()-tic,3)}
        # Negative control: permute assignment of the true index without using score values.
        # This is *not* a biological result and should approach the 1/45 null only
        # with enough episodes; it is included to expose accidental label leakage.
        null_correct=sum(int(rng.integers(0,N_CHOICES)==0) for _ in range(episodes))
        output["negative_controls"][condition]={
            "random_uniform_choices_correct":null_correct,
            "total":episodes,"top1_accuracy":round(null_correct/episodes,6),
            "expected_chance":1/N_CHOICES,
            "random_2afc_correct":int(rng.binomial(episodes*N_NOVEL,0.5)),
            "two_choice_total_pairs":episodes*N_NOVEL,"expected_2afc_chance":0.5}
    output["total_elapsed_seconds"]=round(time.perf_counter()-started,3)
    return output


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed",type=int,default=20261114)
    ap.add_argument("--episodes",type=int,default=24)
    ap.add_argument("--shots",type=int,default=6)
    ap.add_argument("--out",type=Path,default=Path("reports/factory/ARCHER-VISION-LATEST.json"))
    ap.add_argument("--identity-ablation",action="store_true")
    args=ap.parse_args()
    result=benchmark(seed=args.seed,episodes=args.episodes,shots=args.shots,identity_ablated=args.identity_ablation)
    payload=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(payload,encoding="utf-8")
    print(json.dumps({"status":result["status"],"report":str(args.out),
                      "sha256":hashlib.sha256(payload.encode()).hexdigest(),
                      "methods":result["methods"],"negative_controls":result["negative_controls"]},
                     indent=2))

if __name__=="__main__":
    main()
