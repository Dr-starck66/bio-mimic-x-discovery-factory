#!/usr/bin/env python3
"""Pre-registered retrospective external experimental GEO reanalysis.

Does not claim novel wet-lab work, human therapeutic efficacy, or IP.
Protocol: validation/PREREG-GEO-2026-10-16.md (earlier separate commit).
Datasets: GSE74387 microarray and GSE113081 RNA-seq.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import re
import urllib.request
from pathlib import Path

import numpy as np

BASE = "https://ftp.ncbi.nlm.nih.gov/geo/series/"
URLS = {
 "array": BASE+"GSE74nnn/GSE74387/matrix/GSE74387_series_matrix.txt.gz",
 "aco": BASE+"GSE113nnn/GSE113081/suppl/GSE113081_aco_per_se_genes_counts_matrix.txt.gz",
 "mus": BASE+"GSE113nnn/GSE113081/suppl/GSE113081_mus_per_se_genes_counts_matrix.txt.gz",
}
ROOT = Path("validation/cache")
OUT = Path("validation/results")
ROOT.mkdir(exist_ok=True, parents=True)
OUT.mkdir(exist_ok=True, parents=True)
SEED = 20261016
BOOT = 1000
PERM = 100

def download(key: str):
    url = URLS[key]
    path = ROOT/(key+".gz")
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent":"BIO-MIMIC-X/validation academic RNAseq study"})
        with urllib.request.urlopen(req,timeout=60) as r:
            path.write_bytes(r.read(50_000_000))
    raw = path.read_bytes()
    if not raw.startswith(b"\x1f\x8b"):
        raise ValueError("Not a gzip: "+key)
    return path, hashlib.sha256(raw).hexdigest()

def parse_matrix(path, is_geo_array=False):
    titles, sample_ids, matrix_names, rows = None, None, None, []
    vals = []
    started = not is_geo_array
    with gzip.open(path, "rt", encoding="utf8",errors="replace") as stream:
        for line in stream:
            line=line.rstrip("\r\n")
            if not line.strip():
                continue
            if is_geo_array:
                if line.startswith("!Sample_title"):
                    titles=next(csv.reader([line],delimiter="\t"))[1:]
                if line.startswith("!Sample_geo_accession"):
                    sample_ids=next(csv.reader([line],delimiter="\t"))[1:]
                if line=="!series_matrix_table_begin":
                    started=True
                    continue
                if line=="!series_matrix_table_end":
                    break
                if not started or line.startswith("!"):
                    continue
            else:
                if line.startswith("#") or line.startswith("!"):
                    continue
            fields = next(csv.reader([line],delimiter="\t"))
            if not fields or len(fields)<3:
                continue
            if matrix_names is None:
                matrix_names = fields[1:]
                continue
            if len(fields)!=len(matrix_names)+1:
                continue
            try:
                arr=np.fromiter((float(x) for x in fields[1:]),dtype=float,count=len(matrix_names))
            except (ValueError,TypeError):
                continue
            rows.append(fields[0])
            vals.append(arr)
    if not vals:
        raise ValueError("No expression features found: "+str(path))
    x=np.stack(vals)
    if is_geo_array:
        assert sample_ids is not None and titles is not None, "Missing sample annotations"
        mapping={gsm:title for gsm,title in zip(sample_ids,titles)}
        labels=[mapping.get(name,"") for name in matrix_names]
    else:
        labels=matrix_names
    return rows, x, labels

def groups_from(labels,kind):
    groups={}
    for j,label in enumerate(labels):
        if kind=="array":
            match=re.search(r"^(Aco|Mus)\s*-\s*Day\s*(0|7|14)\b",label,re.I)
        else:
            match=re.search(r"^(Acomys|mus)day(0|7|14)[_ .]",label,re.I)
        if not match:
            raise ValueError("Unrecognized sample label "+repr(label))
        sp= "Acomys" if match[1].lower() in {"aco","acomys"} else "Mus"
        groups.setdefault((sp,int(match[2])),[]).append(j)
    return groups

def normalized_counts(x):
    if not np.isfinite(x).all() or np.min(x)<0:
        raise ValueError("RNAseq counts invalid")
    totals=np.sum(x,axis=0)
    if np.min(totals)<=0:
        raise ValueError("Zero library size")
    cpm=x / totals[np.newaxis,:] * 1_000_000
    retained=np.sum(cpm>1,axis=1)>=3
    # Drop rows without RNAseq expression and read counts for strong baseline contrasts
    y=np.log2(cpm[retained]+1)
    return y,int(np.count_nonzero(retained))

def prepare(data, labels,kind):
    groups=groups_from(labels,kind)
    if kind=="array":
        if not np.isfinite(data).all():
            raise ValueError("Microarray has missing expression")
        q50=float(np.median(data))
        q99=float(np.percentile(data,99))
        if not (0<q50<20 and q99<30):
            raise ValueError(f"Microarray logged intensity scale is UNVERIFIED: median={q50}, p99={q99}")
        y=data
    else:
        y,_=normalized_counts(data)
    idx={d:np.asarray(groups[("Acomys" if kind=="aco" else "Mus",d)],dtype=int) for d in [0,7,14]}
    if any(len(v)<3 for v in idx.values()):
        raise ValueError("Under 3 independent biological samples in cell")
    if y.shape[0]<1000:
        raise ValueError("Fewer than 1000 measured features")
    return y,idx

def score(y,groups):
    means=[np.mean(y[:,groups[d]],axis=1) for d in (0,7,14)]
    d7=np.abs(means[1]-means[0])
    d14=np.abs(means[2]-means[0])
    qualified=d7>=0.25
    eligible=int(np.count_nonzero(qualified))
    if eligible<1000: raise ValueError("Fewer than 1000 responsive features")
    return float(np.mean(d14[qualified]<d7[qualified])),eligible

def one_cohort(xa,ga,xm,gm,label,hashes):
    rnga=np.random.default_rng(SEED+len(label))
    rngm=np.random.default_rng(SEED+len(label)+1)
    initiala,features_a=score(xa,ga)
    initialm,features_m=score(xm,gm)
    d=float(initiala-initialm)
    delta=np.zeros(BOOT)
    for b in range(BOOT):
        ia={t:rnga.choice(ga[t],len(ga[t]),replace=True) for t in (0,7,14)}
        im={t:rngm.choice(gm[t],len(gm[t]),replace=True) for t in (0,7,14)}
        delta[b]=score(xa,ia)[0]-score(xm,im)[0]
    ci=[float(v) for v in np.percentile(delta,[2.5,97.5])]
    null=np.zeros(PERM)
    for b in range(PERM):
        pa=np.concatenate([ga[7],ga[14]])
        pm=np.concatenate([gm[7],gm[14]])
        pa=rnga.permutation(pa)
        pm=rngm.permutation(pm)
        qa={0:ga[0],7:pa[:len(ga[7])],14:pa[len(ga[7]):]}
        qm={0:gm[0],7:pm[:len(gm[7])],14:pm[len(gm[7]):]}
        null[b]=score(xa,qa)[0]-score(xm,qm)[0]
    p=(1+int(np.count_nonzero(null>=d)))/(PERM+1)
    status="PASS_PRE_REGISTERED" if d>=0.05 and ci[0]>0 else "FAIL_PRE_REGISTERED"
    return {
       "cohort":label, "input_sha256":hashes, "status":status,
       "samples_per_cell_Acomys":{str(t):len(ga[t]) for t in (0,7,14)},
       "samples_per_cell_Mus":{str(t):len(gm[t]) for t in (0,7,14)},
       "all_measured_features_Acomys":int(xa.shape[0]),
       "all_measured_features_Mus":int(xm.shape[0]),
       "day7_responsive_features_Acomys":features_a,
       "day7_responsive_features_Mus":features_m,
       "response_resolution_fraction_Acomys":initiala,
       "response_resolution_fraction_Mus":initialm,
       "delta":d,"biological_sample_bootstrap_95ci":ci,
       "negative_control_time_label_permutation_p_descriptive":p,
       "bootstrap_iterations":BOOT,"negative_permutations":PERM
    }

def main():
    matrices={}
    hashes={}
    for key in ("array","aco","mus"):
        path,hashes[key]=download(key)
        matrix=parse_matrix(path,is_geo_array=(key=="array"))
        matrices[key]=matrix
        print("SOURCE",key,"features",matrix[1].shape[0],"samples",matrix[1].shape[1],"sha256",hashes[key],flush=True)

    rows,arr,labels=matrices["array"]
    ga=groups_from(labels,"array")
    xa=arr[:,np.asarray([j for j,k in enumerate(labels) if k.startswith("Aco")])]
    xm=arr[:,np.asarray([j for j,k in enumerate(labels) if k.startswith("Mus")])]
    la=[k for k in labels if k.startswith("Aco")]
    lm=[k for k in labels if k.startswith("Mus")]
    ya,ga=prepare(xa,la,"array") # groups_from array returns Acomys; prepare expects Acomys for both: see below
    # Use direct array-specific index in each species rather than inferred label species in Mus.
    ym,gm=prepare_mus_array(xm,lm)
    r1=one_cohort(ya,ga,ym,gm,"GSE74387_microarray",{"GSE74387":hashes["array"]})
    print("REAL_GEO_RESULT",json.dumps(r1,sort_keys=True),flush=True)

    _,ac,acl=matrices["aco"]
    _,mus,musl=matrices["mus"]
    ya,ga=prepare(ac,acl,"aco")
    ym,gm=prepare(mus,musl,"mus")
    r2=one_cohort(ya,ga,ym,gm,"GSE113081_RNAseq",{"GSE113081_aco":hashes["aco"],"GSE113081_mus":hashes["mus"]})
    print("REAL_GEO_RESULT",json.dumps(r2,sort_keys=True),flush=True)

    quality=all(r["status"]=="PASS_PRE_REGISTERED" for r in [r1,r2])
    report={
        "study":"Retrospective independent experimental data reanalysis",
        "preregistration":"validation/PREREG-GEO-2026-10-16.md",
        "status":"PASS_REPLICATED_OBSERVATIONAL_ENDPOINT" if quality else "FAIL_PRE_REGISTERED_HYPOTHESIS",
        "results":[r1,r2],
        "scientific_scope":"expression temporal-response statistical signature, not a new biological experiment",
        "original_novelty":"UNVERIFIED",
        "causal_validation":"NOT_PERFORMED",
        "external_independent_lab_validation":"NOT_PERFORMED",
        "clinical_efficacy":"NOT_TESTED",
        "ip_valuation":"NOT_ESTABLISHED",
        "code_revision":os.getenv("GITHUB_SHA","LOCAL"),
    }
    output=OUT/"geo-validation.json"
    output.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
    print("FINAL_GEO_VALIDATION",report["status"],"json",output,flush=True)

def prepare_mus_array(x,labels):
    g=groups_from(labels,"array")
    idx={t:np.asarray(g[("Mus",t)],dtype=int) for t in (0,7,14)}
    if any(len(x)<3 for x in idx.values()):raise ValueError("Insufficient Mus array biological samples")
    if not np.isfinite(x).all(): raise ValueError("Non-finite expression")
    if not (0<float(np.median(x))<20 and float(np.percentile(x,99))<30):
        raise ValueError("Unrecognized Mus array normalization")
    return x,idx

if __name__=="__main__":
    try: main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("FINAL_GEO_VALIDATION FAIL_PRECONDITION",type(e).__name__,str(e),flush=True)
        raise
