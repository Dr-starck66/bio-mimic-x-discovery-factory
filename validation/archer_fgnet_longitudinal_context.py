#!/usr/bin/env python3
"""Independent FG-NET longitudinal face/context challenge: original frozen 3 encoders.

Uses original 68 manually marked FG-NET landmarks for image alignment only.
Internal ROI is geometry-derived, NOT manually annotated pixel segmentation.
Strict age-gap (>=2 calendar years by filename) proxies different photo periods,
not verified camera/session metadata. No photographs or per-person IDs exported.
"""
from __future__ import annotations
import argparse, collections, hashlib, io, json, re, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from validation.archer_fgnet_manifest_gate import census, parse_points, KEY, IMAGE_EXT
from validation.archer_fgnet_frozen_trial import MASK, MODES, METHODS, preprocess
from validation.archer_vision_benchmark import encode

AGE = re.compile(r'(?<!\d)(?P<person>\d{3})A(?P<age>\d{1,2})(?:[a-z])?(?!\d)', re.I)
MIN_SUBJECTS = 25
MIN_TESTS = 100
MIN_AGE_GAP = 2
SEED = 20261115
EXPECTED_ZIP_SHA256 = '228acddeba96e469f2ded9475ee87f4ab16398de27a2f3ec35a266a46ef2f7fc'


def _tie_winner(scores,seed):
    vals=np.asarray(scores,dtype=np.float64)
    winners=np.flatnonzero(np.isclose(vals,vals.max(),atol=1e-11,rtol=0))
    return int(np.random.default_rng(seed).choice(winners))

def parse_age(stem: str):
    m=AGE.search(stem)
    if not m: raise ValueError('No FG-NET age label')
    age=int(m.group('age'))
    if not 0 <= age <= 100:raise ValueError('Unreasonable age label')
    return m.group('person'), age


def split_longitudinal(rows: dict, min_gap: int=MIN_AGE_GAP):
    """Frozen split: first two photos at distinct ages; test >=2 years after second."""
    selected={}; skipped=collections.Counter()
    for person,items in sorted(rows.items()):
        ordered=sorted(items,key=lambda r:(r[1],r[0]))
        if len(ordered)<3:skipped['lt_3_photos']+=1;continue
        enrollment=[];seen_age=set()
        for item in ordered:
            if item[1] not in seen_age:
                enrollment.append(item);seen_age.add(item[1])
            if len(enrollment)==2:break
        if len(enrollment)<2:skipped['lt_2_distinct_ages']+=1;continue
        first_age,last_age=enrollment[0][1],enrollment[1][1]
        if first_age==last_age:raise AssertionError('Same age enrollment forbidden')
        test=[item for item in ordered if item[1]>=last_age+min_gap]
        if not test:skipped['no_test_age_gap']+=1;continue
        enroll_hash={x[3] for x in enrollment}
        if enroll_hash & {x[3] for x in test}:raise ValueError('Leakage same raw photo')
        selected[person]={'enroll':enrollment,'test':test,'train_ages':(first_age,last_age),
                          'n_test':len(test),'first_test_age_gap':test[0][1]-last_age}
    return selected,dict(skipped)


def read_real_archive(raw: bytes):
    inv=census(raw)
    if inv['status']!='PASS_ACCESS_AND_ANNOTATION_GATE':raise ValueError('FG-NET landmark inventory FAIL')
    if inv['zip_sha256']!=EXPECTED_ZIP_SHA256:raise ValueError('FG-NET authentic SHA-256 mismatch')
    rows=collections.defaultdict(list);rejected=collections.Counter();raw_sha=set()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=collections.defaultdict(dict)
        for m in z.infolist():
            stem=Path(m.filename).stem.upper()
            if not AGE.search(stem):continue
            ext=Path(m.filename).suffix.lower()
            if ext in IMAGE_EXT:
                if 'image' in entries[stem]: raise ValueError('Duplicate image stem')
                entries[stem]['image']=m.filename
            elif ext=='.pts':
                if 'points' in entries[stem]:raise ValueError('Duplicate annotation stem')
                entries[stem]['points']=m.filename
        for stem,files in sorted(entries.items()):
            if 'image' not in files or 'points' not in files:
                rejected['missing_photo_or_annotation']+=1;continue
            blob=z.read(files['image']);digest=hashlib.sha256(blob).hexdigest()
            if digest in raw_sha:
                rejected['duplicate_raw_photo']+=1;continue
            raw_sha.add(digest)
            points=np.asarray(parse_points(z.read(files['points'])),dtype=np.float32)
            if points.shape!=(68,2):rejected['invalid_landmarks']+=1;continue
            with Image.open(io.BytesIO(blob)) as pic:
                pixels=np.asarray(pic.convert('L'),dtype=np.float32)/255
            try:aligned=preprocess(pixels,points)
            except ValueError:rejected['geometry']+=1;continue
            person,age=parse_age(stem)
            rows[person].append((stem,age,aligned,digest))
    return rows,inv,dict(rejected)


def evaluate_longitudinal(zip_bytes:bytes):
    rows,meta,rejected=read_real_archive(zip_bytes)
    selected,exclusions=split_longitudinal(rows)
    people=sorted(selected)
    all_tests=[(p,item) for p in people for item in selected[p]['test']]
    report={'schema':'ASTRA_ARCHER_FGNET_LONGITUDINAL_CONTEXT_V1',
            'dataset_source':meta['source_url'], 'source_sha256_measured':meta['zip_sha256'],
            'status':'FAIL_CLOSED', 'methods_frozen':list(METHODS),
            'models_not_refit_or_hyperparameter_tuned':True,
            'mask':'inner eyes/nose/mouth soft geometry; based on 68 manually labelled landmarks',
            'manual_semantic_skin_hair_clothing_masks_available':False,
            'hair_or_background_guaranteed_absent':False,
            'enrollment':'earliest two photographs with distinct age labels per subject',
            'test':'later photos >=2 age-label years after second enrollment photograph',
            'minimum_age_gap_years':MIN_AGE_GAP,'photo_session_ids_present':False,
            'distinct_photo_periods_inferred_from_age_labels':True,
            'source_sessions_verified_by_capture_date':False,
            'nonredistributive_images':True, 'no_identity_disclosure':True,
            'n_eligible_identities':len(people),'n_heldout_test_photos':len(all_tests),
            'minimum_subjects_preregistered':MIN_SUBJECTS, 'minimum_test_images_preregistered':MIN_TESTS,
            'chance_top1':round(1/max(len(people),1),6),
            'rejections':rejected,'subject_exclusions':exclusions,
            'results':{},'context_swaps':{},'seed':SEED,
            'face_specific_recognition_proven':False,
            'binary_outcome_for_claim':'NOT_VALIDATED',
            'original_encoder_file_sha256':hashlib.sha256(Path('validation/archer_vision_benchmark.py').read_bytes()).hexdigest()}
    if len(people)<MIN_SUBJECTS or len(all_tests)<MIN_TESTS:return report
    # Precompute encoder vectors once, with original encoder only.
    order = [(p,stem,age,modes) for p in people for stem,age,modes,_ in
             sorted(selected[p]['enroll']+selected[p]['test'],key=lambda row:(row[1],row[0]))]
    n=len(people)
    per_mode_cache={}
    # One donor test photograph per test sample, different identity, fixed before looking at scores.
    donor_images={}
    for p,item in all_tests:
        seed=int(hashlib.sha256(f'{SEED}:{p}:{item[0]}:donor'.encode()).hexdigest()[:12],16)
        options=[x for x in people if x!=p]
        donor=options[seed%len(options)]
        donor_options=selected[donor]['test']
        donor_photo=donor_options[(seed//len(options))%len(donor_options)]
        donor_images[(p,item[0])]=(donor,donor_photo[2]['aligned_full'])
    for method in METHODS:
        features={mode:{} for mode in MODES}
        for person,stem,age,modes in order:
            for mode in MODES:
                features[mode][stem]=encode(modes[mode],method)
        report['results'][method]={}
        full_prototypes=None
        for mode in MODES:
            protos=[]
            for p in people:
                e=selected[p]['enroll']
                prot=np.mean([features[mode][x[0]] for x in e],axis=0)
                prot=prot/max(float(np.linalg.norm(prot)),1e-12)
                protos.append(prot)
            protos=np.asarray(protos)
            if mode=='aligned_full':full_prototypes=protos
            hits=0;by_subject=[];score_sha=hashlib.sha256()
            for i,p in enumerate(people):
                local=0
                for item in selected[p]['test']:
                    scores=protos@features[mode][item[0]]
                    score_sha.update(np.asarray(scores,dtype='<f4').tobytes())
                    tie=int(hashlib.sha256(f'{SEED}|{method}|{mode}|{item[0]}'.encode()).hexdigest()[:12],16)
                    local+=int(_tie_winner(scores,tie)==i)
                hits+=local
                by_subject.append([local,len(selected[p]['test'])])
            report['results'][method][mode]={'hits':hits,'total':len(all_tests),
                 'accuracy':round(hits/len(all_tests),6),'model_score_sha256':score_sha.hexdigest()}
            per_mode_cache[(method,mode)]=by_subject
        # Synthetic counterfactual background transplantation; all donor portraits come from different people.
        assert full_prototypes is not None
        target=donor_hits=other=0;score_sha=hashlib.sha256()
        for p,item in all_tests:
            donor,background=donor_images[(p,item[0])]
            original=item[2]['aligned_full']
            swapped=MASK*original+(1-MASK)*background
            feats=encode(swapped,method)
            scores=full_prototypes@feats
            score_sha.update(np.asarray(scores,dtype='<f4').tobytes())
            tie=int(hashlib.sha256(f'{SEED}|SWAP|{method}|{item[0]}'.encode()).hexdigest()[:12],16)
            pred=people[_tie_winner(scores,tie)]
            target+=int(pred==p);donor_hits+=int(pred==donor)
            other+=int(pred not in (p,donor))
        report['context_swaps'][method]={
            'n_correlated_swaps':len(all_tests),
            'correct_face_owner':target,'followed_context_donor':donor_hits,'predicted_other_identity':other,
            'n_faces_from_other_subject':len(all_tests),
            'models_enrolled_on_full_images':True,
            'fixed_donor_before_scores':True,
            'model_score_sha256':score_sha.hexdigest()}
    # Paired cluster bootstrap across subjects; exploratory, no claim of null/independence.
    rng=np.random.default_rng(SEED+123)
    draws=rng.integers(0,len(people),(2000,len(people)))
    for method in METHODS:
        a=np.array(per_mode_cache[(method,'inner_face_only')],dtype=float)
        b=np.array(per_mode_cache[(method,'outside_inner_face')],dtype=float)
        per_subject=(a[:,0]-b[:,0])/np.maximum(a[:,1],1)
        ci=np.quantile(per_subject[draws].mean(axis=1),[.025,.975])
        report['results'][method]['inner_vs_outside_subject_bootstrap']={
            'mean_subject_difference':round(float(np.mean(per_subject)),6),
            'interval_95pct_exploratory':[round(float(x),6) for x in ci],
            'number_subjects':len(people),'number_resamples':2000,
            'claim_preregistered':'inner_face_only should outperform outside_inner_face',
            'passed_directional_claim':bool(np.mean(per_subject)>0),
            'validation_of_face_specificity':False}
    report['status']='PASS_REAL_AGE_GAP_EVALUATION_PARTIAL_FACE_SPECIFICITY'
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--zip',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    result=evaluate_longitudinal(args.zip.read_bytes())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    args.out.write_text(data,encoding='utf-8')
    print(json.dumps({'status':result['status'],'identities':result['n_eligible_identities'],
                      'test_photos':result['n_heldout_test_photos'],
                      'results':result['results'],'counterfactual':result['context_swaps'],
                      'report_sha256':hashlib.sha256(data.encode()).hexdigest()},indent=2))
    if result['status'].startswith('FAIL'):raise SystemExit(3)
if __name__=='__main__':main()
