#!/usr/bin/env python3
"""ASTRA ARCHER VISION Ω: adversarial swap of facial region and peripheral identity cues.

Within CMU Face Images (1997), source PGM provenance independently proven
identical to official UCI archive (GitHub Action run 43651677560).
No model weights are learned; prototypes see only the two predeclared training
photos of the test identity. Simulated composites are exploratory interventions,
NOT an independent, landmark-verified, hair-free face recognition benchmark.
"""
from __future__ import annotations
import argparse, hashlib, json, math, platform
from pathlib import Path
import numpy as np
from scipy.stats import binomtest
from validation.archer_vision_real_cmu import eligible_subjects, TRAIN_VIEWS, TEST_VIEWS
from validation.archer_vision_benchmark import encode
from validation.archer_cmu_mirror_audit import load_mirror_tar

METHODS = ('pixels', 'hog', 'retina_pool')
MASKS = {
    # Pre-specified geometrical masks based on published CMU images, not landmarks
    'inner_ellipse_strict': {'center_xy': (32., 33.), 'radius_xy': (11., 14.)},
    'inner_ellipse_broad': {'center_xy': (32., 33.), 'radius_xy': (15., 19.)},
}
SWAP_OFFSETS = (1, 3, 7)  # no data-dependent selection, cyclic derangements for n>=9
GRAY = np.float32(0.5)


def feathered_ellipse(name: str) -> np.ndarray:
    if name not in MASKS:
        raise ValueError(f'Unsupported ellipse: {name}')
    z = MASKS[name]
    cx,cy = z['center_xy']; rx,ry = z['radius_xy']
    yy,xx = np.mgrid[:64,:64]
    dist=np.sqrt(((xx-cx)/rx)**2+((yy-cy)/ry)**2)
    # Edge feathered over approximately 2px (6 * normalized distance)
    mask=np.clip((1.0-dist)*6.0,0.0,1.0).astype(np.float32)
    if not (0<np.count_nonzero(mask)<64*64) or not (0<mask.sum()<64*64):
        raise ValueError('Mask is degenerate')
    return mask


def composite(face: np.ndarray, background: np.ndarray, mask: np.ndarray) -> np.ndarray:
    f = np.asarray(face,dtype=np.float32)
    b = np.asarray(background,dtype=np.float32)
    if f.shape!=(64,64) or b.shape!=(64,64) or mask.shape!=(64,64):
        raise ValueError('Unexpected shape')
    if not np.isfinite(f).all() or not np.isfinite(b).all():
        raise ValueError('Nonfinite image values')
    if not ((mask>=0).all() and (mask<=1).all()):
        raise ValueError('Bad mask')
    return (mask*f + (1.0-mask)*b).astype(np.float32)


def _argmax_ties(scores, id_key: str, seed: int) -> int:
    v=np.asarray(scores,dtype=np.float64)
    if not np.isfinite(v).all():
        raise ValueError('Nonfinite similarity scores')
    tops=np.flatnonzero(np.isclose(v, v.max(), atol=1e-10, rtol=0))
    digest=hashlib.sha256(f'{seed}|{id_key}'.encode()).digest()
    return int(tops[int.from_bytes(digest[:8],'little')%len(tops)])


def evaluate(images:dict, checksums:dict, seed:int=20261115, masks:tuple[str,...]=('inner_ellipse_strict','inner_ellipse_broad'),
             swap_offsets:tuple[int,...]=SWAP_OFFSETS) -> dict:
    subjects, excluded=eligible_subjects(images)
    n=len(subjects)
    if n<9: raise ValueError('Need >=9 independently described identities for 7-step derangement')
    req=set(TRAIN_VIEWS + sum(TEST_VIEWS.values(),()))
    if len(checksums)!=len(images) or len(set(checksums.values()))!=len(checksums):
        raise ValueError('Source image duplicate/missing hashes')
    if set(TRAIN_VIEWS) & set(sum(TEST_VIEWS.values(),())):
        raise ValueError('Overlapping enrollment and evaluation views')
    for person in subjects:
        if len({checksums[(person,v)] for v in req})!=len(req):
            raise ValueError('Same photo in training and test')
    n_choices=n-1
    if any(o% n_choices==0 for o in swap_offsets):raise ValueError('Background donors must be deranged')
    if len(set(swap_offsets))!=len(swap_offsets):raise ValueError('Duplicate swap offsets')
    out={'schema':'ASTRA_ARCHER_FACE_VS_CONTEXT_COUNTERFACTUAL_V1',
         'status':'EXPLORATORY_WITHIN_DATASET_CONFOUNDS_NOT_LANDMARK_VALIDATED',
         'subjects_eligible':n,'excluded_subjects':excluded,'selected_photo_count':len(images),
         'source_real_images':True,'official_PGM_provenance':{'verified_elsewhere':True,
           'independent_GitHub_run_id':43651677560,
           'note':'Verification is from prior GitHub run, not repeated here; input TAR SHA checked by loader'},
         'train_views':list(TRAIN_VIEWS),'test_views':TEST_VIEWS,
         'test_candidate_count':n_choices,'chance_top1':round(1/n_choices,7),
         'heldout_test_view_images_exclusive':True,'subject_folds_correlated':True,
         'ROI_not_anatomically_landmark_annotated':True,'ROI_data_inspection_occurred_before_experiment':True,
         'masks':MASKS,'background_swap_offsets':list(swap_offsets),
         'methods':{},'negative_controls':{},'seed':seed,
         'python_version':platform.python_version()}
    masks_data={name:feathered_ellipse(name) for name in masks}
    flat=np.full((64,64),GRAY,dtype=np.float32)
    # Unmodified enrollment/reference images for full/background-conflict tests.
    for method in METHODS:
        original_features={k:encode(a,method) for k,a in images.items() if k[0] in subjects}
        for mask_name,mask in masks_data.items():
            flat_cached={k:encode(composite(a,flat,mask),method) for k,a in images.items() if k[0] in subjects}
            for condition,views in TEST_VIEWS.items():
                key=f'{condition}/{mask_name}'
                mode_acc={m:[] for m in ('neutral_flat','shared_background','swapped_background_with_full_enrollment','swapped_background_with_neutral_enrollment')}
                background_acc={m:[] for m in ('swapped_background_with_full_enrollment','swapped_background_with_neutral_enrollment')}
                for fold,target in enumerate(subjects):
                    foil=subjects[(fold+1)%n]
                    # all candidates drawn from test images, with target and n-2 untrained people
                    candidates=[target,*[p for p in subjects if p not in (target,foil)]]
                    # Stable canonical sort, NEVER target-first in tie cases.
                    candidates=sorted(candidates)
                    assert len(candidates)==n_choices
                    donor_person=subjects[(fold+2)%n]
                    assert donor_person not in (target,foil)
                    common=images[(donor_person,'straight_neutral_open')]
                    train_original=np.mean([original_features[(target,v)] for v in TRAIN_VIEWS],axis=0)
                    train_original/=max(float(np.linalg.norm(train_original)),1e-12)
                    train_flat=np.mean([flat_cached[(target,v)] for v in TRAIN_VIEWS],axis=0)
                    train_flat/=max(float(np.linalg.norm(train_flat)),1e-12)
                    train_common=np.mean([encode(composite(images[(target,v)],common,mask),method) for v in TRAIN_VIEWS],axis=0)
                    train_common/=max(float(np.linalg.norm(train_common)),1e-12)
                    for view in views:
                        # Every candidate receives same neutral background. Difference is central patch.
                        flat_features=[flat_cached[(p,view)] for p in candidates]
                        shared_features=[encode(composite(images[(p,view)],common,mask),method) for p in candidates]
                        def winner(feats,proto,tag):
                            scores=np.array([float(x@proto) for x in feats])
                            return candidates[_argmax_ties(scores,f'{fold}|{condition}|{view}|{mask_name}|{tag}',seed)]
                        mode_acc['neutral_flat'].append(int(winner(flat_features,train_flat,'flat')==target))
                        mode_acc['shared_background'].append(int(winner(shared_features,train_common,'common')==target))
                        for offset in swap_offsets:
                            # Permute backgrounds across all candidates with no fixed points.
                            donors=[candidates[(i+offset)%n_choices] for i in range(n_choices)]
                            assert all(p!=d for p,d in zip(candidates,donors))
                            swapped_features=[encode(composite(images[(p,view)],images[(d,view)],mask),method)
                                              for p,d in zip(candidates,donors)]
                            true_background_index=donors.index(target)
                            for mod,proto in (('swapped_background_with_full_enrollment',train_original),
                                              ('swapped_background_with_neutral_enrollment',train_flat)):
                                scores=np.array([float(x@proto) for x in swapped_features])
                                win=_argmax_ties(scores,f'{fold}|{condition}|{view}|{mask_name}|{mod}|{offset}',seed)
                                mode_acc[mod].append(int(candidates[win]==target))
                                background_acc[mod].append(int(win==true_background_index))
                result={}
                for mode,v in mode_acc.items():
                    count=int(sum(v)); trials=len(v)
                    item={'face_owner_correct':count,'trials':trials,'face_owner_accuracy':round(count/trials,6),
                          'note':'trials are correlated, include repeated identities/background permutations'}
                    if mode in background_acc:
                        bg=int(sum(background_acc[mode]));item.update({'background_owner_correct':bg,
                             'background_owner_accuracy':round(bg/trials,6),
                             'background_in_conflict_with_face':True})
                    result[mode]=item
                out['methods'].setdefault(method,{})[key]=result
    # Null control: all candidates share exactly one constant image; should have only chance via tie randomization.
    rng=np.random.default_rng(seed)
    for cond,views in TEST_VIEWS.items():
        trials=n*len(views)
        null_hits=int(np.sum(rng.integers(0,n_choices,size=trials)==0))
        out['negative_controls'][cond]={'random_label_hits':null_hits,'trials':trials,'chance':1/n_choices}
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mirror-tar',type=Path,default=Path('data/CMU_FACES4_GITHUB_MIRROR.tar.gz'))
    ap.add_argument('--out',type=Path,default=Path('reports/factory/ARCHER-FACE-VS-CONTEXT-20261115.json'))
    args=ap.parse_args()
    imgs,hashes,prov=load_mirror_tar(args.mirror_tar)
    result=evaluate(imgs,hashes)
    result['mirror_SHA256_from_actual_bytes']=prov['mirror_tar_sha256']
    text=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+'\n'
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(text,encoding='utf-8')
    print(json.dumps({'status':result['status'],'report':str(args.out),'SHA256':hashlib.sha256(text.encode()).hexdigest(),
                      'pose_shift':{m:{k:v['face_owner_accuracy'] for k,results in body.items()
                                       if k.startswith('pose_shift/') for k,v in results.items()}
                                    for m,body in result['methods'].items()}},indent=2))
if __name__=='__main__':main()
