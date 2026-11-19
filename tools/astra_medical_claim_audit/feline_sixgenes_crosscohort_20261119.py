#!/usr/bin/env python3
"""ASTRA MEDICAL: negative-control replication of six NATALEE candidate genes on FELINE.
FELINE discovery GSE158724 and validation GSE211434; endpoint: 6-month tumor response (not NATALEE survival).
PRE-EXISTING exploration of all six genes in validation means NO independent validation claim.
Only patient-level pretreatment cancer cell pseudobulk, no clinical decision.
"""
import csv, gzip, json, math, hashlib, random, statistics, sys, time
from pathlib import Path
from urllib.request import urlopen, urlretrieve
from collections import Counter, defaultdict
from itertools import combinations
B="https://ftp.ncbi.nlm.nih.gov/geo/series/"
TARGETS={"CEACAM6","NOD2","GPX3","GATA3","SLC39A6","MAPT","ACTB","GAPDH"}
MIN_CELLS=100
RNG_SEED=20261119

def sample_matrix(accession,platform):
    path=f"/tmp/{accession}-{platform}_series_matrix.txt.gz"
    urlretrieve(f"{B}{accession[:6]}nnn/{accession}/matrix/{accession}-{platform}_series_matrix.txt.gz",path)
    names=[];characteristics=[]
    with gzip.open(path,"rt") as f:
        for line in f:
            if line.startswith("!Sample_title"):
                names=next(csv.reader([line],delimiter="\t"))[1:]
            elif line.startswith("!Sample_characteristics_ch1"):
                characteristics.append(next(csv.reader([line],delimiter="\t"))[1:])
    if any(len(x)!=len(names) for x in characteristics):raise ValueError("metadata column mismatch")
    samples={}
    for i,name in enumerate(names):
        fields={}
        for row in characteristics:
            if ":" in row[i]:
                k,v=row[i].split(":",1);fields[k.strip().lower()]=v.strip()
        if "patient" not in fields or "response" not in fields:raise ValueError("missing baseline metadata")
        samples[name]=fields
    return samples

def discovery():
    acc="GSE158724";matrix=sample_matrix(acc,"GPL24676")
    label={};sample={}
    for n,meta in matrix.items():
        if meta.get("days treated")!="0":continue
        arm=meta.get("treatment arm")
        outcome=meta.get("response")
        if arm not in ("A","B","C") or outcome not in ("Responder","Non-responder"):raise ValueError("invalid label")
        p=meta["patient"]
        if p in label and label[p]!=(arm,outcome):raise ValueError("conflicting patient arm")
        label[p]=(arm,outcome);sample[n]=p
    meta_path="/tmp/GSE158724_10x.cell_types.txt.gz"
    urlretrieve(f"{B}GSE158nnn/GSE158724/suppl/GSE158724_10x.cell_types.txt.gz",meta_path)
    cell={}
    with gzip.open(meta_path,"rt") as f:
        for row in csv.DictReader(f,delimiter="\t"):
            if row["Cell Type"]!="Cancer cells":continue
            name=row["Cell"];sample_id="_".join(name.split("_")[:2])
            if sample_id in sample:cell[name]=sample[sample_id]
    return label,cell,{"metadata_samples":len(sample),"metadata_source":"GSE158724-GPL24676_series_matrix.txt.gz","cell_annotation_source":"GSE158724_10x.cell_types.txt.gz"}

def validation():
    url=f"{B}GSE211nnn/GSE211434/suppl/GSE211434_cell_types.txt.gz"
    p="/tmp/GSE211434_cell_types.txt.gz";urlretrieve(url,p)
    hasher=hashlib.sha256()
    with open(p,"rb") as f:
        for data in iter(lambda:f.read(1048576),b""):hasher.update(data)
    if hasher.hexdigest()!="7d1d0e05683ee9bb2bb79011a0bdbe03daecde4c0be9197fbaff74329367e51d":
        raise ValueError("validation dataset SHA mismatch")
    labels={};cell={}
    with gzip.open(p,"rt") as f:
        for row in csv.DictReader(f,delimiter="\t"):
            if row["Day"]!="0" or row["CellType"]!="Cancer cells":continue
            pt=row["Patient"];arm="A" if row["Treatment"]=="Letrozole alone" else "R"
            response=row["ResponseYN"]
            if response not in ("Response","Non-response"):raise ValueError("invalid validation outcome")
            v=(arm,"Responder" if response=="Response" else "Non-responder")
            if pt in labels and labels[pt]!=v:raise ValueError("inconsistent validation labels")
            labels[pt]=v
            if int(row["nCount_RNA"])>0:cell[row["CellID"]]=pt
    return labels,cell,{"cell_annotations_sha256":hasher.hexdigest(),"source":"GSE211434_cell_types.txt.gz"}

def gene_scan(dataset,labels,cells):
    original_cells=len(cells)
    counts=Counter(cells.values())
    selected={p for p,n in counts.items() if n>=MIN_CELLS}
    cells={k:p for k,p in cells.items() if p in selected}
    labels={p:v for p,v in labels.items() if p in selected}
    url=(f"{B}GSE158nnn/GSE158724/suppl/GSE158724_10x.counts.txt.gz" if dataset=="discovery"
         else f"{B}GSE211nnn/GSE211434/suppl/GSE211434_counts.txt.gz")
    genes={};start=time.monotonic()
    with urlopen(url,timeout=120) as response:
        with gzip.GzipFile(fileobj=response) as stream:
            header=stream.readline().strip().split(b"\t")
            offset=1 if dataset=="discovery" else 3
            expected=[b"Gene.ID"] if dataset=="discovery" else [b"Gene",b"Gene.ID",b"Gene.Symbol"]
            if header[:offset]!=expected:raise ValueError("unknown RNA count header")
            selected_columns=[(i,cells[c.decode()]) for i,c in enumerate(header) if c.decode() in cells]
            if len(selected_columns)!=len(cells):raise ValueError(f"RNA cells mismatch {len(selected_columns)} != {len(cells)}")
            for line in stream:
                parts=line.split(b"\t",offset)
                if len(parts)<offset+1:raise ValueError("malformed RNA matrix row")
                symbol=parts[0].decode() if dataset=="discovery" else parts[2].decode()
                if symbol in TARGETS:
                    fields=line.rstrip(b"\r\n").split(b"\t")
                    if len(fields)!=len(header):raise ValueError("RNA field count mismatch")
                    sums=Counter();positive=Counter()
                    for i,p in selected_columns:
                        val=int(fields[i])
                        if val<0:raise ValueError("negative expression")
                        sums[p]+=val
                        positive[p]+=val>0
                    genes[symbol]={"total":sums,"positive":positive}
                    print(f"{dataset} gene {symbol} found after {time.monotonic()-start:.1f}s",flush=True)
                    if len(genes)==len(TARGETS):break
    if set(genes)!=TARGETS:raise ValueError("missing target genes "+repr(TARGETS-set(genes)))
    profiles={}
    for p in selected:
        n=counts[p]
        actb=genes["ACTB"]["total"][p]/n
        gapdh=genes["GAPDH"]["total"][p]/n
        profiles[p]={}
        for gene in ("CEACAM6","NOD2","GPX3","GATA3","SLC39A6","MAPT"):
            avg=genes[gene]["total"][p]/n
            profiles[p][gene+"_mean_count_per_cell"]=avg
            profiles[p][gene+"_to_ACTB_ratio"]=avg/(actb+0.01)
            profiles[p][gene+"_to_GAPDH_ratio"]=avg/(gapdh+0.01)
    return labels,profiles,{"raw_cells":original_cells,"selected_cells":len(cells),"selected_patients":len(labels),"rna_url":url,"patient_outcomes_written":False}

def auc(pairs):
    yes=[s for s,y in pairs if y];no=[s for s,y in pairs if not y]
    if not yes or not no:return None
    return sum((s>t)+0.5*(s==t) for s in yes for t in no)/(len(yes)*len(no))

def exact_perm(pairs):
    n=len(pairs);yes_n=sum(y for _,y in pairs)
    if n>20:return None
    observed=auc(pairs)
    x=[score for score,_ in pairs]
    if observed is None:return None
    count=0;total=0
    for combo in combinations(range(n),yes_n):
        good=set(combo)
        value=auc([(x[i],i in good) for i in range(n)])
        count+=abs(value-0.5)>=abs(observed-0.5)-1e-12
        total+=1
    return round(count/total,7),total

def median(seq):
    a=sorted(seq);n=len(a)
    return (a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2)

def interaction(rows,threshold):
    cells={(t,h):[] for t in (0,1) for h in (0,1)}
    for s,tx,y in rows:cells[(tx,int(s>=threshold))].append(y)
    if any(not v for v in cells.values()):return None
    probs={f"{t}{h}":round(sum(v)/len(v),5) for (t,h),v in cells.items()}
    delta=(sum(cells[1,1])/len(cells[1,1])-sum(cells[0,1])/len(cells[0,1])-
          sum(cells[1,0])/len(cells[1,0])+sum(cells[0,0])/len(cells[0,0]))
    rand=random.Random(RNG_SEED);boot=[]
    for _ in range(1500):
        sample={key:[rand.choice(v) for i in range(len(v))] for key,v in cells.items()}
        diff=(sum(sample[1,1])/len(sample[1,1])-sum(sample[0,1])/len(sample[0,1])-
              sum(sample[1,0])/len(sample[1,0])+sum(sample[0,0])/len(sample[0,0]))
        boot.append(diff)
    boot.sort()
    return {"difference_of_risk_differences":round(delta,5),
            "bootstrap_CI95_exploratory":[round(boot[37],5),round(boot[1462],5)],
            "cells":[{"treated":t,"high":h,"n":len(v),"responders":sum(v)} for (t,h),v in sorted(cells.items())],
            "proportions":probs}

def analyse(dataset,labels,profiles,provenance):
    report={"cohort":dataset,"sample_n":len(labels),"original_data":provenance,
            "method":"baseline malignant pseudobulk unnormalized counts/cell, detection fraction, ACTB/GAPDH sensitivity; patient-level only",
            "features":{},"treatment":{"letrozole":0,"ribociclib_plus_letrozole":0},"fail_open":False}
    for arm,outcome in labels.values():report["treatment"]["letrozole" if arm=="A" else "ribociclib_plus_letrozole"]+=1
    for feature in sorted(next(iter(profiles.values())).keys()):
        res={}
        for grp in ("ribociclib","letrozole"):
            pts=[p for p in sorted(labels) if (labels[p][0]!="A")==(grp=="ribociclib")]
            pairs=[(profiles[p][feature],labels[p][1]=="Responder") for p in pts]
            perf=auc(pairs)
            p_exact=exact_perm(pairs)
            res[grp]={"n_patients":len(pairs),"responders":sum(out for _,out in pairs),
                      "AUROC":round(perf,6) if perf is not None else None,
                      "exact_perm_p":p_exact[0] if p_exact else None,
                      "n_permutations":p_exact[1] if p_exact else None}
        allrows=[(profiles[p][feature],int(labels[p][0]!="A"),int(labels[p][1]=="Responder")) for p in labels]
        res["exploratory_interaction_median_split"]=interaction(allrows,median([r[0] for r in allrows]))
        report["features"][feature]=res
    report["selection_bias_notice"]="GSE211434 validation had already been explored for six NATALEE genes. Discovery analysis is post hoc external replication, not prospective blinded validation."
    report["not_clinical"]="FELINE short-term response differs from NATALEE survival; biomarker×randomized-arm on tiny cell-sequenced subset, no clinical use"
    return report

def self_test():
    assert auc([(2,True),(1,False)])==1
    assert auc([(1,True),(2,False)])==0
    assert auc([(2,True),(2,False)])==0.5
    assert exact_perm([(2,True),(1,False)])==(1,2)
    assert abs(interaction([(2,1,1),(2,0,0),(1,1,0),(1,0,0)],1.5)["difference_of_risk_differences"] - 1.0)<1e-12
    assert median([1,2,3,4])==2.5
    assert len(TARGETS)==8
    assert {"CEACAM6","NOD2","GPX3","GATA3","SLC39A6","MAPT"}<=TARGETS
    print("UNIT_TESTS_PASS 8/8",flush=True)

def main():
    self_test()
    output={"date":"2026-11-19","protocol":"pre-treatment patient-level analysis, discovery and validation independent",
            "dataset":"FELINE","outcome":"response 6 months, not NATALEE death",
            "separate_arms":{"GSE158724":["A","B","C"],"GSE211434":["letrozole","ribociclib_combination"]},
            "cohorts":{}}
    for name,get in [("discovery",discovery),("validation",validation)]:
        labels,cells,info=get()
        labels,profiles,detail=gene_scan(name,labels,cells)
        output["cohorts"][name]=analyse(name,labels,profiles,{**info,**detail})
        print("COHORT_AGGREGATE "+json.dumps({
            "cohort": name,
            "n":len(labels),
            "selected_cells": detail["selected_cells"],
            "ribo_n": output["cohorts"][name]["treatment"]["ribociclib_plus_letrozole"],
            "control_n": output["cohorts"][name]["treatment"]["letrozole"],
            "mean_expression": {
                g:{arm:output["cohorts"][name]["features"][g+"_mean_count_per_cell"][arm]
                for arm in ("ribociclib","letrozole")}
                for g in ("CEACAM6","NOD2","GPX3","GATA3","SLC39A6","MAPT")
            },
            "interactions": {
                g: output["cohorts"][name]["features"][g+"_mean_count_per_cell"]["exploratory_interaction_median_split"]
                for g in ("CEACAM6","NOD2","GPX3","GATA3","SLC39A6","MAPT")
            },
        },sort_keys=True),flush=True)
        print(f"COHORT_DONE {name} {len(labels)} patients",flush=True)
    with open("/tmp/astra_feline_sixgenes_crosscohort_20261119.json","w") as f:json.dump(output,f,sort_keys=True,indent=2)
    print("AGGREGATE_REPORT_SUMMARY "+json.dumps({
        "cohort_n": {k:v["sample_n"] for k,v in output["cohorts"].items()},
        "discovery_ribo_auc":{g:output["cohorts"]["discovery"]["features"][g+"_mean_count_per_cell"]["ribociclib"]["AUROC"] for g in ("CEACAM6","NOD2","GPX3","GATA3","SLC39A6","MAPT")},
        "validation_ribo_auc":{g:output["cohorts"]["validation"]["features"][g+"_mean_count_per_cell"]["ribociclib"]["AUROC"] for g in ("CEACAM6","NOD2","GPX3","GATA3","SLC39A6","MAPT")},
        "n_GEO_genes":len(TARGETS),"method":"pretreatment cell aggregation","clinical_selection":"UNVERIFIED"
    },sort_keys=True),flush=True)

if __name__=="__main__": main()
