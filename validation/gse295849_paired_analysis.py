#!/usr/bin/env python3
"""One-donor-one-vote paired DNAm analysis of GSE295849 public samples.

The primary estimand is mean DNAm age of an individual's untreated iNSCs at
low passage minus that same individual's untreated EPC D0 DNAm age. Different
chip samples from the same genotype are NOT independent donors. No claims
of clinical rejuvenation or cross-species transfer are permitted.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from statistics import mean, median, stdev

ROOT=Path(__file__).resolve().parents[1]
CROSSWALK=ROOT/"reports/factory/GSE295849-REAL-SAMPLE-CROSSWALK-2026-11-02.json"
MODEL_SHA="56f8ce6567170ce5427f24803d30a2f0e3f6d3735b44100af02521fcd7c18027"
SOURCES={
 "1":"c13d9efcb094e57d8f69f819440620de671bd398b45e8c24c29194aa7f228d32",
 "2":"4ca091cef1128ddcea24e6c2b349c038ae1de8dc4eb302f7f218304e17479fcd",
 "3":"fa92b4124a5bd7c69a878ae4557d2def91b1698203fc975fe63003de27640f2d",
}

def source_ages(path,part):
    raw=json.loads(Path(path).read_text(encoding="utf-8"))
    if part=="3" and "computed_ages_years" in raw:
        rows=raw["computed_ages_years"]
        sha=raw["source_sha256"]
        model=raw["model_sha256"]
        source_count=raw["sample_columns"]
    else:
        rows=raw.get("samples") or []
        sha=raw.get("source_sha256")
        model=raw.get("model_sha256")
        source_count=raw.get("source_sample_count")
        if raw.get("status")!="PASS_INDEPENDENT_CLOCK_ESTIMATION_UNGROUPED":
            raise ValueError("clock part "+part+" not independently successful")
    if sha!=SOURCES[part] or model!=MODEL_SHA:
        raise ValueError("pinned GEO source/model hash mismatch part "+part)
    if len(rows)!=source_count:
        raise ValueError("sample count does not match source")
    output={}
    for row in rows:
        key=row["chip_sample_id"]
        age=row.get("age_years")
        if key in output or not isinstance(age,(int,float)) or not math.isfinite(age):
            raise ValueError("invalid or duplicate sample age")
        output[key]=age
    return output

def analyze_crosswalk(crosswalk,age_by_chip):
    samples=crosswalk["samples"]
    if len(samples)!=60 or len(age_by_chip)!=60 or len(set(age_by_chip))!=60:
        raise ValueError("requires full 60 real samples and 60 unique clock results")
    ids=[s.get("chip_sample_id") for s in samples]
    gsms=[s.get("gsm") for s in samples]
    if len(set(ids))!=60 or len(set(gsms))!=60 or set(ids)!=set(age_by_chip):
        raise ValueError("GEO sample-to-clock mapping is not bijective")
    by_donor={}
    for sample in samples:
        donor=sample.get("donor_genotype")
        state=sample.get("cell_type")
        stage=sample.get("harvest_stage")
        treat=sample.get("treatment")
        if not donor or not state or not stage or not treat:
            raise ValueError("missing mandatory biological descriptor")
        record={"gsm":sample["gsm"],"chip_sample_id":sample["chip_sample_id"],
                "cell_type":state,"stage":stage,"treatment":treat,
                "epigenetic_age_years":round(age_by_chip[sample["chip_sample_id"]],5)}
        by_donor.setdefault(donor,[]).append(record)
    primary=[]
    secondary=[]
    excluded=[]
    for donor,rows in sorted(by_donor.items(),key=lambda x:int(x[0])):
        baseline=[r for r in rows if r["cell_type"]=="EPC" and r["stage"]=="D0" and r["treatment"]=="None"]
        if len(baseline)!=1:
            excluded.append({"genotype":donor,"reason":"missing or non-unique untreated EPC D0"})
            continue
        b=baseline[0]["epigenetic_age_years"]
        untreated_lp=[r for r in rows if r["cell_type"]=="iNSC" and r["stage"]=="LP" and r["treatment"]=="None"]
        if not untreated_lp:
            excluded.append({"genotype":donor,"reason":"missing untreated iNSC LP"})
            continue
        lp=mean(r["epigenetic_age_years"] for r in untreated_lp)
        # EPC age may be close to zero in newborns: do not invent ratios.
        pct=None if b<=0 else round(100*(1-lp/b),3)
        primary.append({"genotype":donor,"baseline_gsm":baseline[0]["gsm"],"baseline_EPC_D0_years":round(b,5),
                        "untreated_LP_gsms":[r["gsm"] for r in untreated_lp],
                        "n_untreated_LP_chips":len(untreated_lp),"untreated_LP_mean_years":round(lp,5),
                        "difference_LP_minus_D0_years":round(lp-b,5),"reduction_pct_of_EPC_clock_age":pct})
        for row in rows:
            if row==baseline[0]:continue
            secondary.append({"genotype":donor,"gsm":row["gsm"],
                              "cell_type":row["cell_type"],"stage":row["stage"],
                              "treatment":row["treatment"],"age_years":row["epigenetic_age_years"],
                              "delta_from_same_donor_EPC_D0":round(row["epigenetic_age_years"]-b,5)})
    if not primary:
        return {"status":"UNVERIFIED_NO_VALID_DONOR_PAIRS","excluded":excluded}
    deltas=[r["difference_LP_minus_D0_years"] for r in primary]
    return {"status":"PASS_DESCRIPTIVE_WITHIN_DONOR_PAIRED_CLOCK_COMPARISON",
            "donor_count":len(primary),"sample_count":len(samples),"primary_contrasts":primary,
            "secondary_exploratory_not_primary":secondary,
            "excluded_genotypes":excluded,
            "aggregate":{"one_vote_per_donor":True,"paired_mean_delta_years":round(mean(deltas),5),
                         "paired_median_delta_years":round(median(deltas),5),
                         "n_negative_deltas":sum(x<0 for x in deltas),
                         "n_positive_deltas":sum(x>0 for x in deltas),
                         "sd_across_donors":round(stdev(deltas),5) if len(deltas)>1 else None},
            "effect_is":"change in DNA-methylation-clock predicted age after changing cell fate",
            "chronological_donor_ages":"NOT_IN_THE_COMPACT_GEO_METADATA",
            "no_claim":"No organismal age reversal; cannot equate a clock-age change to clinical therapy, nor infer human limb regeneration",
            "negative_controls":{"GSE74387":"FAIL_RETAINED","lineage_confounded_by_programming":True,
                                 "treated_LP_excluded_from_primary":True,
                                 "smNPC_excluded_from_primary":True},
            "independent_wet_lab_replication":"UNVERIFIED"}

def main():
    ap=argparse.ArgumentParser()
    for i in ("1","2","3"):ap.add_argument("--part"+i,required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    output={"schema":"BIO-MIMIC-X/GSE295849-PAIRED-DNAM-AGES/1",
            "status":"PARTIAL_SOURCE_FAILURE"}
    code=1
    try:
        combined={}
        for i in ("1","2","3"):
            part=source_ages(getattr(a,"part"+i),i)
            overlap=set(combined)&set(part)
            if overlap:raise ValueError("duplicate chip across parts "+str(overlap))
            combined.update(part)
        cross=json.loads(CROSSWALK.read_text(encoding="utf-8"))
        if cross["source"]["series"]!="GSE295849":
            raise ValueError("wrong series crosswalk")
        output.update(analyze_crosswalk(cross,combined))
        code=0 if output["status"].startswith("PASS_") else 1
    except Exception as exc:
        output["reason"]=f"{type(exc).__name__}: {exc}"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    body=json.dumps(output,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    a.out.write_text(body,encoding="utf-8")
    # Avoid long CI logs: all 12 paired rows and aggregate; full secondary JSON retained.
    compact={k:v for k,v in output.items() if k!="secondary_exploratory_not_primary"}
    print("BIO_MIMIC_GSE295849_PAIRED "+json.dumps(compact,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
