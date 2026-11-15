#!/usr/bin/env python3
"""ASTRA ARCHER: frozen-descriptor evaluation on an INDEPENDENT Olivetti/AT&T dataset.

Do not distribute portrait pixels. 40 persons * 10 images, fixed 2 enrollment
and 8 held-out test views per person. This tests within-dataset image
discrimination, NOT perfect anatomical hair/background elimination.
"""
import hashlib, json, platform, time
from pathlib import Path
import numpy as np
from sklearn.datasets import fetch_olivetti_faces
from validation.archer_vision_benchmark import encode
from validation.archer_cmu_counterfactual_faces import feathered_ellipse, composite

METHODS=('pixels','hog','retina_pool')
MODES=('original','strict_center','broad_center','outside_strict')
EXPECTED=(400,64,64)

def preprocess(x,mode,masks):
    gray=np.full((64,64),0.5,dtype=np.float32)
    if mode=='original':return x.copy()
    if mode=='strict_center':return composite(x,gray,masks['inner_ellipse_strict'])
    if mode=='broad_center':return composite(x,gray,masks['inner_ellipse_broad'])
    if mode=='outside_strict':return composite(gray,x,masks['inner_ellipse_strict'])
    raise ValueError(mode)

def run(data,labels):
    data=np.asarray(data,dtype=np.float32)
    labels=np.asarray(labels,dtype=np.int64)
    if data.shape!=EXPECTED or labels.shape!=(400,):raise ValueError('wrong dataset shape')
    if set(labels.tolist())!=set(range(40)):raise ValueError('wrong 40 subject labels')
    if any(np.sum(labels==i)!=10 for i in range(40)):raise ValueError('subject counts not 10')
    if not np.isfinite(data).all():raise ValueError('non-finite pixels')
    hashes=[hashlib.sha256(np.round(x*255).astype(np.uint8).tobytes()).hexdigest() for x in data]
    if len(set(hashes))!=len(hashes):raise ValueError('duplicate photographs')
    subjects=[np.where(labels==i)[0] for i in range(40)]
    train=np.array([idx for inds in subjects for idx in inds[:2]],dtype=np.int64)
    test=np.array([idx for inds in subjects for idx in inds[2:]],dtype=np.int64)
    if set(train)&set(test):raise ValueError('sample leakage')
    masks={k:feathered_ellipse(k) for k in ('inner_ellipse_strict','inner_ellipse_broad')}
    out={'status':'AT_T_OLIVETTI_INDEPENDENT_DATASET_EVALUATED','source':'scikit-learn fetch_olivetti_faces; original images AT&T Laboratories Cambridge',
         'source_page':'https://cam-orl.co.uk/facedatabase.html','dataset_reference':'https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_olivetti_faces.html',
         'license_note':'AT&T site requests attribution; non-commercial research evaluation, no photos redistributed',
         'subject_count':40,'samples_count':400,'train_examples_per_subject':2,'test_examples_per_subject':8,
         'test_count':320,'chance_top1':0.025,'subject_train_test_same_id_different_photographs':True,
         'source_bytes_download_hash_not_officially_authenticated':True,
         'ROI_is_not_landmark_verified':True,'ROI_frozen_before_external_dataset':True,
         'no_parameter_tuning_on_test':True,'source_raw_image_sha256_aggregate':hashlib.sha256(''.join(hashes).encode()).hexdigest(),
         'methods':{},'negative_controls':{}}
    for method in METHODS:
        out['methods'][method]={}
        for mode in MODES:
            feats=np.stack([encode(preprocess(x,mode,masks),method) for x in data],axis=0)
            centers=np.stack([np.mean(feats[ix[:2]],axis=0) for ix in subjects])
            centers/=np.maximum(np.linalg.norm(centers,axis=1,keepdims=True),1e-9)
            scores=feats[test]@centers.T
            true=labels[test]
            guess=scores.argmax(axis=1)
            hits=int(np.sum(guess==true))
            by_person=[int(np.sum(guess[labels[test]==i]==i)) for i in range(40)]
            out['methods'][method][mode]={'correct':hits,'trials':len(test),'top1':round(hits/len(test),6),'by_subject_hits':by_person}
    # Null: all identities have identical constant images, subject label ties
    rng=np.random.default_rng(20261115)
    out['negative_controls']['random_label_baseline']={'correct':int(np.sum(rng.integers(0,40,size=320)==labels[test])),
                      'trials':320,'chance':1/40}
    return out

if __name__=='__main__':
    tic=time.perf_counter()
    d=fetch_olivetti_faces(shuffle=False,download_if_missing=True,data_home='data/orl_faces')
    result=run(d.images,d.target)
    result['elapsed_seconds']=round(time.perf_counter()-tic,2)
    dest=Path('reports/factory/ARCHER-OLIVETTI-INDEPENDENT-20261115.json')
    dest.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(result,sort_keys=True,indent=2)+'\n'
    dest.write_text(payload)
    print(json.dumps({'status':result['status'],'json_sha256':hashlib.sha256(payload.encode()).hexdigest(),
                      'methods':{m:{k:(v['correct'],v['trials']) for k,v in modes.items()} for m,modes in result['methods'].items()},
                      'negative_controls':result['negative_controls']},indent=2))
