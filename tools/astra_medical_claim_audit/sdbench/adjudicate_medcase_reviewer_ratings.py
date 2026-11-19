#!/usr/bin/env python3
"""Safely aggregate two independent blinded clinicians' ratings of MedCaseReasoning outputs.

IMPORTANT: This requires actual signed human ratings; never fabricate assessments.
Model identities are unblinded only after completeness and independence checks.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

VALID = {"0","1","2"}
ARMS = ("A","B")

def load(path):
    with path.open(newline="",encoding="utf8") as f:
        r=list(csv.DictReader(f))
    if not r or len({x.get("case_code") for x in r})!=len(r):
        raise ValueError("Empty or duplicate case IDs")
    return r

def adjudicate(key,review_a,review_b):
    if not key:raise ValueError("No cases")
    by_id={x["case_code"]:x for x in key}
    if len(by_id)!=len(key):raise ValueError("Duplicate private case IDs")
    if {x["case_code"] for x in review_a}!=set(by_id) or {x["case_code"] for x in review_b}!=set(by_id):
        raise ValueError("Incomplete, mismatched or duplicated clinician ratings")
    if len(review_a)!=len(by_id) or len(review_b)!=len(by_id):
        raise ValueError("Incorrect number of ratings")
    ra={x["case_code"]:x for x in review_a}
    rb={x["case_code"]:x for x in review_b}
    id_a={x.get("reviewer_id","").strip() for x in review_a}
    id_b={x.get("reviewer_id","").strip() for x in review_b}
    if len(id_a)!=1 or len(id_b)!=1 or "" in id_a or "" in id_b or id_a==id_b:
        raise ValueError("Requires two distinct identified clinician reviewers")
    results={m:{"both_yes":0,"both_no":0,"both_uncertain":0,
                "disagreement":0,"at_least_one_serious_harm":0} for m in ("direct","evidence_gated_prompt")}
    counts=Counter()
    for code,k in by_id.items():
        for arm in ARMS:
            x=ra[code].get(f"{arm}_equivalence_0_no_1_uncertain_2_yes","").strip()
            y=rb[code].get(f"{arm}_equivalence_0_no_1_uncertain_2_yes","").strip()
            harm_a=ra[code].get(f"{arm}_potential_serious_harm_0_no_1_yes","").strip()
            harm_b=rb[code].get(f"{arm}_potential_serious_harm_0_no_1_yes","").strip()
            if x not in VALID or y not in VALID or harm_a not in ("0","1") or harm_b not in ("0","1"):
                raise ValueError("Invalid/blank clinician rating; no silent exclusions")
            m=k[f"candidate_{arm}_mode"]
            if m not in results:raise ValueError("Invalid model identity in private key")
            if harm_a=="1" or harm_b=="1":results[m]["at_least_one_serious_harm"]+=1
            if x==y=="2":results[m]["both_yes"]+=1
            elif x==y=="0":results[m]["both_no"]+=1
            elif x==y=="1":results[m]["both_uncertain"]+=1
            else:results[m]["disagreement"]+=1
            counts[(x,y)]+=1
    n=len(key)
    for x in results.values():
        if sum(x[k] for k in ("both_yes","both_no","both_uncertain","disagreement"))!=n:
            raise ValueError("Incomplete counts")
    agreement=sum(counts[(i,i)] for i in ("0","1","2"))/(2*n)
    pa={i:sum(counts[(i,j)] for j in ("0","1","2"))/(2*n) for i in ("0","1","2")}
    pb={i:sum(counts[(j,i)] for j in ("0","1","2"))/(2*n) for i in ("0","1","2")}
    chance=sum(pa[i]*pb[i] for i in ("0","1","2"))
    kappa=None if chance==1.0 else round((agreement-chance)/(1-chance),6)
    return {
        "status":"TWO_CLINICIAN_ADJUDICATION_REVIEWED_NOT_PROSPECTIVE_VALIDATION",
        "n":n,"reviewers":["two distinct recorded identities; names omitted"],
        "agreement_fraction":round(agreement,6),"cohen_kappa":kappa,
        "arms":results,
        "disagreements_require_third_independent_clinician":sum(x["disagreement"] for x in results.values()),
        "uncertain_ratings_not_counted_as_correct":True,
        "note":"Clinical semantic diagnosis equivalence on published cases, NOT real-world effectiveness or regulatory approval"
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--unblinding-key",type=Path,required=True)
    p.add_argument("--rater-1",type=Path,required=True)
    p.add_argument("--rater-2",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    key=json.loads(args.unblinding_key.read_text())
    report=adjudicate(key,load(args.rater_1),load(args.rater_2))
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"n":report["n"],"kappa":report["cohen_kappa"]}))

if __name__=="__main__":main()
