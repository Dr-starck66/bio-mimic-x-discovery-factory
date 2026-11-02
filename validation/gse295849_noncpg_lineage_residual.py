#!/usr/bin/env python3
"""BIO-MIMIC X: estimate fate-dependence from clock-EXCLUDED public DNAm CpGs.

This is an exploratory **same-assay negative/sensitivity control**. It is NOT
orthogonal RNA evidence, NOT a causal intervention, NOT an estimate of aging
independent of lineage. Source and clock weights are hash-pinned.

Use:
  --part 1/2/3 --out artifacts/partN.json.gz   [public NCBI FTP shards]
  --join artifacts/part1.json.gz ... --out report.json [hold-donor-out proxy]

Only public GSE295849 DNA methylation arrays are read; no dbGaP RNA files.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import sys
import urllib.request
import zipfile
from pathlib import Path
from statistics import mean, median

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from validation.gse295849_real_qc import audit_remote
AGES=ROOT/"reports/factory/GSE295849-ALL-60-PAIRED-HORVATH2018-2026-11-02.json"
MODEL_URL="https://huggingface.co/pyaging/skinandblood/resolve/main/skinandblood.pt"
MODEL_SHA="56f8ce6567170ce5427f24803d30a2f0e3f6d3735b44100af02521fcd7c18027"
PART_SHA={
 "1":"c13d9efcb094e57d8f69f819440620de671bd398b45e8c24c29194aa7f228d32",
 "2":"4ca091cef1128ddcea24e6c2b349c038ae1de8dc4eb302f7f218304e17479fcd",
 "3":"fa92b4124a5bd7c69a878ae4557d2def91b1698203fc975fe63003de27640f2d",
}
PART_SAMPLES={"1":39,"2":13,"3":8}
PART_ROWS={"1":866091,"2":866238,"3":866091}
PAT_CPG=re.compile(r"^cg[0-9]{8}$")
PAT_CHIP=re.compile(r"^[0-9]{12}_R[0-9]{2}C[0-9]{2}$")
SELECT_MODULUS=128
FEATURE_COUNT=200

def selected_probe(probe:str):
    return (PAT_CPG.fullmatch(probe) is not None and
            int.from_bytes(hashlib.sha256(probe.encode()).digest()[:2],"big")%SELECT_MODULUS ==0)

def clock_probes_from_pinned_model(data:bytes):
    if hashlib.sha256(data).hexdigest()!=MODEL_SHA:
        raise ValueError("trusted clock model SHA changed")
    if len(data)!=17613:
        raise ValueError("trusted clock model byte length changed")
    with zipfile.ZipFile(io.BytesIO(data)) as zipped:
        pkl=[x for x in zipped.namelist() if x.endswith("/data.pkl")]
        if len(pkl)!=1:
            raise ValueError("no unique model pickle metadata")
        txt=zipped.read(pkl[0])
    # Inspect only literal identifiers, never deserialize an untrusted pickle.
    features=[x.decode("ascii") for x in re.findall(rb"cg[0-9]{8}",txt)]
    if len(features)!=391 or len(set(features))!=391 or features[0]!="cg12140144":
        raise ValueError("391 clock features could not be safely retrieved")
    return set(features)

def download_clock_probes():
    request=urllib.request.Request(MODEL_URL,headers={"User-Agent":"BIO-MIMIC-X-nonclock-sensitivity/1"})
    with urllib.request.urlopen(request,timeout=45) as response:
        model_bytes=response.read(20000)
    return clock_probes_from_pinned_model(model_bytes)

def shard_extract(filename:Path, exclude:set[str],part:str):
    samples=None
    selected={}
    rows=0
    with gzip.open(filename,"rt",encoding="utf-8-sig",newline="") as f:
        rd=csv.reader(f,delimiter="\t")
        for row in rd:
            if not row or row[0].startswith(("#","!")):continue
            if samples is None:
                if row[-1]=="" and all(PAT_CHIP.fullmatch(v) for v in row[:-1]):
                    samples=row[:-1]
                elif all(PAT_CHIP.fullmatch(v) for v in row):
                    samples=row
                elif len(row)>1 and all(PAT_CHIP.fullmatch(v) for v in row[1:]):
                    samples=row[1:]
                else:
                    raise ValueError("unrecognized sample header")
                if len(samples)!=PART_SAMPLES[part] or len(set(samples))!=len(samples):
                    raise ValueError("incorrect sample count for source")
                continue
            rows+=1
            if len(row)!=len(samples)+1:
                raise ValueError("unexpected beta probe row width")
            probe=row[0]
            if not selected_probe(probe) or probe in exclude:continue
            if probe in selected:
                raise ValueError("duplicate selected CpG")
            values=[]
            missing=False
            for x in row[1:]:
                try:v=float(x)
                except ValueError:
                    missing=True
                    break
                if not math.isfinite(v) or not (0<=v<=1):
                    missing=True
                    break
                values.append(round(v,8))
            if not missing:selected[probe]=values
    if rows!=PART_ROWS[part] or len(selected)<3200:
        raise ValueError(f"unexpected GEO probe counts: all={rows}, selected={len(selected)}")
    return {"schema":"BIO-MIMIC-X/NONCLOCK-PROBE-SHARD/1",
            "study":"GSE295849","part":part,"source_sha256":PART_SHA[part],
            "model_sha256":MODEL_SHA,"sample_chips":samples,
            "n_rows_checked":rows,"n_selected_probes":len(selected),
            "n_explicit_clock_probes_excluded":len(exclude),
            "nonclock_probes":selected}

def create_shard(part,out):
    clocks=download_clock_probes()
    storage={}
    def on_file(path,audit):
        if audit.get("compressed_sha256")!=PART_SHA[part]:
            raise ValueError("GSE295849 SHA differs from published report")
        data=shard_extract(path,clocks,part)
        storage.update(data)
        out.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(out,"wt",encoding="utf-8") as fp:
            json.dump(data,fp,separators=(",",":"),sort_keys=True)
        return {"part":part,"probe_count":data["n_selected_probes"],"SHA256":PART_SHA[part]}
    qc=audit_remote(part,timeout=120,on_file=on_file,attempts=3)
    if not storage:
        raise ValueError("no real CpG data extracted")
    return {"part":part,"samples":len(storage["sample_chips"]),"probes":storage["n_selected_probes"],
            "source_sha256":qc["compressed_sha256"],"gzip_crc":"PASS"}

def merge_parts(parts:list[dict],ages:list[dict]):
    if len(parts)!=3 or sorted(x["part"] for x in parts)!=["1","2","3"]:
        raise ValueError("requires original three verified shards")
    samples={}
    probes=None
    expected={x["chip_sample_id"] for x in ages}
    for p in parts:
        part=p["part"]
        if p["source_sha256"]!=PART_SHA[part] or p["model_sha256"]!=MODEL_SHA:
            raise ValueError("source/model SHA not pinned")
        chips=p["sample_chips"]
        if len(chips)!=PART_SAMPLES[part] or len(set(chips))!=len(chips):
            raise ValueError("invalid sample chip list")
        if set(samples)&set(chips):raise ValueError("duplicated chip across shards")
        for i,chip in enumerate(chips):samples[chip]=(p,i)
        ids=set(p["nonclock_probes"])
        probes=ids if probes is None else probes&ids
    if set(samples)!=expected or len(samples)!=60:
        raise ValueError("not the same exact 60 public methylation samples")
    if probes is None or len(probes)<3000:
        raise ValueError("fewer than 3000 common nonclock CpGs")
    return samples,sorted(probes)

def sample_vector(chip,samples,probe_names):
    shard,index=samples[chip]
    return [shard["nonclock_probes"][p][index] for p in probe_names]

def gate_report(shards,age_report):
    ages=age_report["sample_level_ages"]
    samples,probes=merge_parts(shards,ages)
    # Transpose ~6k × 60 original matrix to sample vectors (still tiny memory).
    sample_betas={x["chip_sample_id"]:sample_vector(x["chip_sample_id"],samples,probes) for x in ages}
    by_donor={}
    for x in ages:by_donor.setdefault(x["donor_genotype"],[]).append(x)
    reference_donors=[]
    for donor,rows in by_donor.items():
        EPC=[x for x in rows if x["cell_type"]=="EPC" and x["stage"]=="D0" and x["treatment"]=="None"]
        smNPC=[x for x in rows if x["cell_type"]=="smNPC" and x["stage"]=="LP" and x["treatment"]=="None"]
        if len(EPC)==len(smNPC)==1:
            reference_donors.append((donor,EPC[0],smNPC[0]))
    if len(reference_donors)!=9:raise ValueError("must have 9 donor-matched EPC-to-smNPC identity training pairs")
    target=[]
    reference_holdout=[]
    for donor,rows in sorted(by_donor.items(),key=lambda a:int(a[0])):
        D14=[x for x in rows if x["cell_type"]=="iNSC" and x["stage"]=="D14" and x["treatment"]=="None"]
        LP=[x for x in rows if x["cell_type"]=="iNSC" and x["stage"]=="LP" and x["treatment"]=="None"]
        if not D14 or not LP:continue
        if len(D14)!=1:raise ValueError("one D14 per donor expected")
        train=[(d,a,b) for d,a,b in reference_donors if d!=donor]
        # Train only on other donors and without using ANY Horvath clock CpGs.
        means_E=[]
        paired_differences=[]
        for i,p in enumerate(probes):
            before=[sample_betas[a["chip_sample_id"]][i] for _,a,b in train]
            after=[sample_betas[b["chip_sample_id"]][i] for _,a,b in train]
            means_E.append(mean(before))
            paired_differences.append(mean([n-e for e,n in zip(before,after)]))
        chosen=sorted(range(len(probes)),key=lambda i:-abs(paired_differences[i]))[:FEATURE_COUNT]
        coeff=[paired_differences[i] for i in chosen]
        norm=sum(w*w for w in coeff)
        if norm<1e-9:raise ValueError("reference epigenomic identity signature non-discriminative")
        def identity(x):
            vector=sample_betas[x["chip_sample_id"]]
            return sum((vector[i]-means_E[i])*paired_differences[i] for i in chosen)/norm
        d0=identity(D14[0])
        lp=mean(identity(x) for x in LP)
        age0=D14[0]["clock_age_years"]
        ageLP=mean(x["clock_age_years"] for x in LP)
        target.append({"genotype":donor,"n_train_reference_donors":len(train),
                       "CpGs_used":len(chosen),
                       "D14_identity_proxy":round(d0,5),
                       "LP_identity_proxy":round(lp,5),
                       "delta_identity_proxy_LP_minus_D14":round(lp-d0,5),
                       "delta_Horvath_years":round(ageLP-age0,5),
                       "D14_GSM":D14[0]["gsm"],
                       "LP_GSMs":[x["gsm"] for x in LP]})
        if any(d==donor for d,a,b in reference_donors):
            ref=[(a,b) for d,a,b in reference_donors if d==donor][0]
            reference_holdout.append({"genotype":donor,
                "EPC_identity_score":round(identity(ref[0]),5),
                "smNPC_identity_score":round(identity(ref[1]),5)})
    if len(target)!=6:raise ValueError("six within-donor D14 LP experiments required")
    xx=[v["delta_identity_proxy_LP_minus_D14"] for v in target]
    yy=[v["delta_Horvath_years"] for v in target]
    avgx,avgy=mean(xx),mean(yy)
    varx=sum((x-avgx)**2 for x in xx)
    if varx<1e-8:
        residual={"status":"UNIDENTIFIABLE_CONSTANT_IDENTITY_SHIFTS"}
    else:
        slope=sum((x-avgx)*(y-avgy) for x,y in zip(xx,yy))/varx
        intercept=avgy-slope*avgx
        residual={"status":"DESCRIPTIVE_SENSITIVITY_ONLY",
                  "slope_age_years_per_proxy_unit":round(slope,5),
                  "intercept_at_zero_identity_change":round(intercept,5),
                  "zero_change_observed_within_data_range":min(xx)<=0<=max(xx),
                  "intercept_interpretation":("OBSERVATIONALLY_INTERPOLATED_NOT_CAUSAL" if min(xx)<=0<=max(xx) else "EXTRAPOLATED_NOT_IDENTIFIABLE"),
                  "slope_and_intercept_pooled_n_independent_donors":6}
    return {"schema":"BIO-MIMIC-X/GSE295849-LEAVE-DONOR-OUT-NONCLOCK-LINEAGE-PROXY/1",
            "status":"PASS_REAL_PUBLIC_DNAM_SAME_ASSAY_SENSITIVITY_ONLY",
            "source":"GSE295849 60 genuine public methylation beta arrays hash pinned",
            "clock":"Horvath2018 Skin & Blood 391 CpGs hash pinned excluded",
            "RNA_2026_expressions_loaded":False,
            "orthogonal_transcriptomics":"UNVERIFIED_PROTECTED_ACCESS",
            "cell_fate_independent_rejuvenation":"UNVERIFIED",
            "n_public_methylation_chips":len(samples),
            "n_common_preselected_clock_excluded_CpGs":len(probes),
            "sampling_rule":"sha256(cpg_id) first 16 bits mod 128 == 0, excluding all 391 Horvath model probes",
            "lineage_proxy_training":"for each test donor, 8 or 9 other donors' EPC D0 vs smNPC LP methylation; 200 largest paired CpG differences; projected identity score (EPC=0 smNPC=1 approximately); NOT lineage-specific transcriptional measurement, age confounded",
            "reference_training_donors":len(reference_donors),
            "n_actual_paired_D14_LP_donors":len(target),
            "pairs":target,
            "held_out_reference_EPC_vs_smNPC_checks":reference_holdout,
            "observed_Horvath_change_mean_years":round(avgy,5),
            "identity_proxy_shift_mean":round(avgx,5),
            "n_identity_shifts_towards_mature_neural_reference":sum(v>0 for v in xx),
            "statistical_identity_correction":residual,
            "limitations":[
                "CpGs outside clock but SAME methylation assay are not RNA; independent model coordinates do not establish biological clock-independence.",
                "Training on EPC vs smNPC contrasts conflates cell fate, reprogramming, chronological age and cell culture.",
                "Only six donor pairs; no causal randomized intervention or independent donor replication.",
                "Time since reprogramming, oxygen and transgene expression co-vary with stage.",
                "Small n makes identity-adjusted intercept unstable; zero-identity extrapolation must not be described as causal proof.",
                "Negative biological clock-age predictions for some other donor stages remain nonphysical.",
                "No license to infer organismal rejuvenation, therapeutic efficacy or axolotl transfer."
            ],
            "negative_control_GSE74387":"FAIL_RETAINED"}

def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--part",choices=["1","2","3"])
    group.add_argument("--join",nargs=3,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    if args.part:
        result=create_shard(args.part,args.out)
        print("GSE295849_REAL_NONCLOCK_SHARD "+json.dumps(result,sort_keys=True))
    else:
        parts=[]
        for p in args.join:
            with gzip.open(p,"rt",encoding="utf-8") as fh:parts.append(json.load(fh))
        report=json.loads(AGES.read_text(encoding="utf-8"))
        result=gate_report(parts,report)
        args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        summary={k:v for k,v in result.items() if k not in ("pairs","held_out_reference_EPC_vs_smNPC_checks","limitations")}
        print("GSE295849_REAL_NONCLOCK_IDENTITY "+json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
