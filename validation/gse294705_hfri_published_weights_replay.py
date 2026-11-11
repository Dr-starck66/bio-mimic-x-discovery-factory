#!/usr/bin/env python3
"""BIO-MIMIC X — published HfRI 75-gene replay on public GSE294705.
No training, cutoff optimization, trial-data access, or medical claim.
Requires numpy, public NCBI gzip, and reviewed manifest in repo.
"""
from __future__ import annotations
import argparse, gzip, hashlib, io, json, sys, urllib.request
from pathlib import Path
import numpy as np

BASE="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE294nnn/GSE294705/"
COUNTS=BASE+"suppl/GSE294705_CBNUH_n94_NMIBC_counts.txt.gz"
META=BASE+"matrix/GSE294705_series_matrix.txt.gz"
COUNTS_SHA="f5ca68e03d0547cc9faad8940f75181640f1d99dbdbc6119faf85da8c49729ce"
META_SHA="15c06e2554466f65f43cbf38238eeaaf089cd650440b9b2f18dcf76c958e8212"
DOCX_SHA="7a2f33a66ca2f024be6e15019682a2f697d3dbb91715fc4c63d9946b1077a7a4"
SEED=20261111
rng=np.random.default_rng(SEED)

def fetch(url, sha):
    req=urllib.request.Request(url,headers={"User-Agent":"BIO-MIMIC-X published HfRI audit, public GEO"})
    with urllib.request.urlopen(req, timeout=45) as response:
        data=response.read(60_000_000)
    assert data.startswith(b"\x1f\x8b") and hashlib.sha256(data).hexdigest()==sha, "GEO SHA mismatch"
    return gzip.decompress(data).decode("utf-8")

def fields(lines, prefix):
    vals=[]
    for row in lines:
        if row.startswith(prefix+"\t"):
            vals.append([x.strip('"') for x in row.split("\t")[1:]])
    return vals

def get_meta(raw):
    lines=raw.splitlines()
    titles=fields(lines,"!Sample_title")[0]
    cs=fields(lines,"!Sample_characteristics_ch1")
    assert len(titles)==94 and len(set(titles))==94 and all(len(x)==94 for x in cs)
    def key(k):
        v=[x for x in cs if all(a.startswith(k+": ") for a in x)]
        assert len(v)==1, "metadata missing "+k
        return [a[len(k)+2:] for a in v[0]]
    outcome=key("recurrence(2>=)")
    assert outcome.count("Yes")==16 and outcome.count("No")==78
    return dict(names=[x.replace("NMIBC_","",1) for x in titles],
                outcome=outcome,sex=key("tissue"),stage=key("cell type"),
                grade=key("grade"),eortc=np.array(list(map(float,key("eortc-recur score")))))

def load_counts(raw, meta):
    lines=raw.splitlines()
    header=lines[0].split("\t")
    assert header[0]=="geneID" and len(header)==95 and len(lines)==63242, "GEO shape mismatch"
    names=header[1:]
    assert len(set(names))==94 and set(names)==set(meta["names"])
    columns=[names.index(s) for s in meta["names"]]
    ids=[line.split("\t",1)[0] for line in lines[1:]]
    assert len(ids)==63241 and len(set(ids))==63241
    # Preserve distinct integers and full gene library counts; no gene selection on outcomes.
    values=np.loadtxt(io.StringIO(raw),dtype=np.float64,delimiter="\t",skiprows=1,usecols=range(1,95))
    assert values.shape==(63241,94) and np.all(np.isfinite(values)) and np.min(values)>=0
    assert np.all(values==np.floor(values)), "non-integer raw counts"
    values=values[:,columns]
    lib=np.sum(values,axis=0)
    assert np.all(lib>0)
    cpm=1_000_000*values/lib[None,:]
    # Paper filters genes at cohort-wide mean CPM <1; do not use outcome labels.
    retain=np.mean(cpm,axis=1)>=1
    return [name for name, keep in zip(ids,retain) if keep],np.log2(1+cpm[retain]),int(np.sum(retain)),lib

def quantile_normalize(x):
    """Between-sample quantile normalization; preserve equal-value ties."""
    indexes=np.argsort(x,axis=0,kind="mergesort")
    sorted_values=np.take_along_axis(x,indexes,axis=0)
    target=np.mean(sorted_values,axis=1)
    prefix=np.r_[0,np.cumsum(target)]
    rows, cols=x.shape
    output=np.empty_like(x)
    for j in range(cols):
        values=sorted_values[:,j]
        starts=np.r_[0,np.flatnonzero(np.diff(values)!=0)+1]
        ends=np.r_[starts[1:],rows]
        mapped=np.empty(rows)
        for a,b in zip(starts,ends):
            mapped[a:b]=(prefix[b]-prefix[a])/(b-a)
        output[indexes[:,j],j]=mapped
    return output

def score(x,ids,manifest,normalization="quantile"):
    weights=manifest["weights"]
    assert len(weights)==75 and len(set(w["gene"] for w in weights))==75
    ix={s:i for i,s in enumerate(ids)}
    missing=[w["gene"] for w in weights if w["ensembl"] not in ix]
    if missing:raise ValueError("Missing weighted rows after CPM filter: "+",".join(missing))
    normalized=quantile_normalize(x) if normalization=="quantile" else x
    selected=np.stack([normalized[ix[w["ensembl"]],:] for w in weights],axis=0)
    mean=np.mean(selected,axis=1,keepdims=True)
    std=np.std(selected,axis=1,ddof=0,keepdims=True)
    if np.any(std==0):raise ValueError("Zero-variance required gene")
    z=(selected-mean)/std
    coeff=np.array([w["weight"] for w in weights],dtype=float)
    return coeff@z

def auc(scores,positive):
    a=np.asarray(scores)[positive]
    b=np.asarray(scores)[~positive]
    return float(np.mean((a[:,None]>b[None,:])+.5*(a[:,None]==b[None,:])))

def permute(labels,groups,rng):
    shuffled=labels.copy()
    for g in np.unique(groups):
        ix=np.where(groups==g)[0]
        shuffled[ix]=rng.permutation(labels[ix])
    return shuffled

def perm_p(scores,labels,groups,iters=10000):
    observed=abs(float(np.mean(scores[labels])-np.mean(scores[~labels])))
    exceed=0
    for _ in range(iters):
        p=permute(labels,groups,rng)
        diff=abs(float(np.mean(scores[p])-np.mean(scores[~p])))
        exceed+=diff+1e-12>=observed
    return (exceed+1)/(iters+1)

def test():
    x=np.array([[1,2,5],[3,1,3],[1,1,8],[4,5,3]],float)
    z=quantile_normalize(x)
    assert z.shape==x.shape and np.allclose(np.sort(z,axis=0),np.sort(z,axis=0)[:,[0]])
    assert auc([0,1,3,4],[False,False,True,True])==1
    p=np.array([True,False,True,False])
    g=np.array(["M","M","F","F"])
    for _ in range(30):
        v=permute(p,g,rng)
        assert v[:2].sum()==1 and v[2:].sum()==1
    assert hashlib.sha256(b"abc").hexdigest().startswith("ba7816")
    print(json.dumps({"tests":5,"status":"PASS","scope":"nonclinical math & integrity checks"}))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=False,default="research/cretostimogene/hfri_published_75_gene_weights_hgnc_2026-11-11.json")
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:
        test();return 0
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if manifest["source_sha256"]!=DOCX_SHA:raise ValueError("published coefficients source digest mismatch")
    meta=get_meta(fetch(META,META_SHA))
    genes,x,retained,lib=load_counts(fetch(COUNTS,COUNTS_SHA),meta)
    labels=np.array([s=="Yes" for s in meta["outcome"]])
    site=np.array([s.split("_")[0] for s in meta["names"]])
    strata=np.array([a+"/"+b+"/"+c for a,b,c in zip(meta["sex"],meta["stage"],site)])
    scores_qn=score(x,genes,manifest,"quantile")
    scores_raw=score(x,genes,manifest,"logCPM")
    out={"dataset":"GSE294705","doi":"10.1186/s12916-026-04745-8",
         "method":"Published Table S2 75-gene coefficients; CPM >=1 filter; log2(1+CPM); between-sample quantile normalization with ties; per-gene cohort z-standardization; weighted sum; no fitting / direction flip.",
         "not_identical_to_published_protocol_warning":"Full published analysis may use additional normalization/censoring and an HfRI high/low decision threshold. This is an independent approximate quantitative implementation; not proof of exact original HfRI reproduction.",
         "patients":94,"events_ge_2_recurrence":16,"genes_after_cpm_filter":retained,
         "weight_gene_count":len(manifest["weights"]),
         "baseline_eortc_auc_descriptive":round(auc(meta["eortc"],labels),8),
         "source_sha256":{"counts":COUNTS_SHA,"metadata":META_SHA,"published_docx":DOCX_SHA},
         "results":{}}
    for name,s in [("quantile_normalized",scores_qn),("logCPM_without_quantile_sensitivity",scores_raw)]:
        out["results"][name]={"auc_in_sample":round(auc(s,labels),8),
                   "mean_yes_minus_no":round(float(np.mean(s[labels])-np.mean(s[~labels])),8),
                   "permutation_p_sex_stage_site":round(perm_p(s,labels,strata,10000),8),
                   "orientation":"higher HfRI means higher recurrence risk, weights fixed a priori"}
    out["scientific_status"]="EXPLORATORY_PUBLISHED_SCORE_REPLAY_NOT_CLINICALLY_VALIDATED"
    print("ASTRA_PUBLISHED_HFRI_REPORT_START"+json.dumps(out,sort_keys=True)+"ASTRA_PUBLISHED_HFRI_REPORT_END")
    return 0

if __name__=="__main__":sys.exit(main())
