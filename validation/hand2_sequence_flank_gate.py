#!/usr/bin/env python3
"""Fail-closed reciprocal sequence-flank evidence gate. Not genome-wide uniqueness."""
import argparse, json, hashlib
from pathlib import Path

EXPECTED = {
 ("old_left","modern_right","reverse_complement"):3888,
 ("old_right","modern_left","reverse_complement"):4268,
}
def evaluate(report):
    rows=report.get("results",[])
    found={}
    for row in rows:
        key=(row["old"],row["modern"],row["modern_orientation"])
        if key in found: raise ValueError("duplicate comparison")
        found[key]=row["shared_distinct_31mers"]
    negatives={k:v for k,v in found.items() if k not in EXPECTED}
    valid=(len(found)==8 and all(found.get(k)==v for k,v in EXPECTED.items())
           and len(negatives)==6 and all(v==0 for v in negatives.values())
           and report.get("k")==31
           and report.get("cross_checks",{}).get("local_window_length_validation")=="PASS_4_OF_4")
    return {"status":"PARTIAL_SEQUENCE_FLANK_RECIPROCITY" if valid else "FAIL_CROSSCHECK",
      "positive_observed":{"/".join(k):found.get(k) for k in EXPECTED},
      "negative_count":len(negatives),"negative_nonzero":sum(v!=0 for v in negatives.values()),
      "genome_wide_reciprocal_best_hit":"UNVERIFIED",
      "independent_neighbor_gene_orthology":"UNVERIFIED",
      "note":"Checks published NCBI-derived counts, not raw FASTA recomputation or genome-wide search."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    raw=a.evidence.read_bytes()
    result=evaluate(json.loads(raw))
    result["evidence_sha256"]=hashlib.sha256(raw).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"])
    return 0 if result["status"].startswith("PARTIAL") else 1
if __name__=="__main__":raise SystemExit(main())
