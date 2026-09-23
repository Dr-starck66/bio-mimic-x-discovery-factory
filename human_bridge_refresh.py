#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"factory"))
from human_bridge import build_human_bridges

STATE=ROOT/"state"/"factory"/"latest.json"
PUBLIC=ROOT/"public"/"data"/"factory"/"latest.json"
REPORT=ROOT/"reports"/"factory"/"HUMAN-BRIDGE-LATEST.md"

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

def main():
    cycle=json.loads(STATE.read_text(encoding="utf-8"))
    claims=[x for x in cycle.get("claims",[]) if x.get("status")=="SUPPORTED"]
    previous_sha=cycle.get("sha256")

    result=build_human_bridges(claims)
    by_subject={}
    for b in result.get("bridges",[]):
        by_subject.setdefault(b["animal_species"],[]).append(b)

    human=[]
    for claim in claims:
        subject=claim["subject"]
        hits=by_subject.get(subject,[])
        human.append({
            "subject":subject,
            "status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED" if hits else "UNVERIFIED_HUMAN_BRIDGE",
            "bridges":hits,
            "claim_pmids":claim.get("pmid_sources",[]),
            "animal_claim_not_promoted_to_human_efficacy":True,
            "remaining":[] if hits else [
                "supported species in orthology provider",
                "gene/protein annotation with validated orthologue",
                "Open Targets human target context"
            ]
        })

    cycle["human_bridge_result"]=result
    cycle["human_translation"]=human
    cycle["bridge_refresh"]={
        "time":now(),
        "previous_cycle_sha256":previous_sha,
        "supported_claims":len(claims),
        "bridged_candidates":result.get("bridged_candidates",0),
        "coverage_ratio":result.get("coverage_ratio",0),
        "status":result.get("status","PARTIAL")
    }

    for e in cycle.get("brick_usage",[]):
        if e.get("brick_id")=="human-bridge":
            e["time"]=cycle["bridge_refresh"]["time"]
            e["output_ref"]="human_bridge_result"
            e["metric"]="supported_claim_bridge_coverage"
            e["value"]=result.get("coverage_ratio",0)
            e["status"]=result.get("status","PARTIAL")

    payload=copy.deepcopy(cycle)
    payload.pop("sha256",None)
    cycle["sha256"]=hashlib.sha256(
        json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()
    ).hexdigest()

    save(STATE,cycle)
    save(PUBLIC,cycle)

    lines=[
        "# BIO-MIMIC X — Human Bridge Refresh",
        "",
        f"Time: {cycle['bridge_refresh']['time']}",
        f"Supported claims: {len(claims)}",
        f"Bridged claims: {result.get('bridged_candidates',0)}",
        f"Coverage: {result.get('coverage_ratio',0):.1%}",
        f"Status: {result.get('status','PARTIAL')}",
        "",
        "## Candidate status"
    ]
    for row in result.get("candidate_status",[]):
        lines.append(
            f"- {row.get('candidate')}: {row.get('status')} · "
            f"genes={row.get('gene_candidates',0)} · bridges={row.get('bridges',0)}"
        )
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")

    print(json.dumps({
        "status":result.get("status"),
        "supported_claims":len(claims),
        "resolved_species":result.get("resolved_species",0),
        "bridged_candidates":result.get("bridged_candidates",0),
        "coverage_ratio":result.get("coverage_ratio",0),
        "bridges":len(result.get("bridges",[])),
        "sha256":cycle["sha256"]
    }))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
