#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"factory"))
from human_bridge import build_human_bridges
from translation_paths import build_translation_paths

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
    translation=build_translation_paths(claims,result)
    by_subject={}
    for b in result.get("bridges",[]):
        by_subject.setdefault(b["animal_species"],[]).append(b)

    path_by_subject={x["subject"]:x for x in translation.get("paths",[])}
    human=[]
    for claim in claims:
        subject=claim["subject"]
        hits=by_subject.get(subject,[])
        path=path_by_subject.get(subject)
        if hits:
            status="ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED"
        elif path and path.get("status")=="VERIFIED":
            status="HUMAN_TRANSLATION_PATH_VERIFIED"
        else:
            status="UNVERIFIED_HUMAN_BRIDGE"
        human.append({
            "subject":subject,
            "status":status,
            "bridges":hits,
            "translation_path":path,
            "claim_pmids":claim.get("pmid_sources",[]),
            "animal_claim_not_promoted_to_human_efficacy":True,
            "remaining":[] if status!="UNVERIFIED_HUMAN_BRIDGE" else [
                "provider-verified orthology or a separately typed evidence-backed translation path"
            ]
        })

    cycle["human_bridge_result"]=result
    cycle["human_translation_result"]=translation
    cycle["human_translation"]=human
    cycle["bridge_refresh"]={
        "time":now(),
        "previous_cycle_sha256":previous_sha,
        "supported_claims":len(claims),
        "strict_orthology_candidates":result.get("bridged_candidates",0),
        "strict_orthology_coverage_ratio":result.get("coverage_ratio",0),
        "translation_verified_candidates":translation.get("translation_verified_candidates",0),
        "translation_coverage_ratio":translation.get("translation_coverage_ratio",0),
        "status":translation.get("status","PARTIAL")
    }

    for e in cycle.get("brick_usage",[]):
        if e.get("brick_id")=="human-bridge":
            e["time"]=cycle["bridge_refresh"]["time"]
            e["output_ref"]="human_translation_result"
            e["metric"]="verified_human_translation_coverage"
            e["value"]=translation.get("translation_coverage_ratio",0)
            e["status"]=translation.get("status","PARTIAL")

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
        f"Strict orthology: {result.get('bridged_candidates',0)}/{len(claims)} ({result.get('coverage_ratio',0):.1%})",
        f"Verified human translation: {translation.get('translation_verified_candidates',0)}/{len(claims)} ({translation.get('translation_coverage_ratio',0):.1%})",
        f"Translation status: {translation.get('status','PARTIAL')}",
        "",
        "## Translation status"
    ]
    for row in translation.get("candidate_status",[]):
        lines.append(
            f"- {row.get('candidate')}: {row.get('status')} · {row.get('path_type') or 'none'}"
        )
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")

    print(json.dumps({
        "status":translation.get("status"),
        "supported_claims":len(claims),
        "strict_orthology_candidates":result.get("bridged_candidates",0),
        "strict_orthology_coverage_ratio":result.get("coverage_ratio",0),
        "translation_verified_candidates":translation.get("translation_verified_candidates",0),
        "translation_coverage_ratio":translation.get("translation_coverage_ratio",0),
        "path_type_counts":translation.get("path_type_counts",{}),
        "sha256":cycle["sha256"]
    }))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
