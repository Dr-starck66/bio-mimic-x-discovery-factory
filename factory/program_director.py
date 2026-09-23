#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/"state"/"factory"
STATE.mkdir(parents=True,exist_ok=True)

def load(path,default):
    if path.exists():
        try:return json.loads(path.read_text(encoding="utf-8"))
        except Exception:return default
    return default

def save(path,obj):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

def now(): return datetime.now(timezone.utc).isoformat()

def create_or_update_programs(committee,max_programs=6):
    old=load(STATE/"programs.json",{"programs":[]})
    existing={p["key"]:p for p in old["programs"]}
    portfolio=committee.get("portfolio",[])[:max_programs]
    programs=[]
    for rank,c in enumerate(portfolio,1):
        key=" ".join(c["name"].lower().split())
        p=existing.get(key)
        if not p:
            p={
                "id":"PRG-"+hashlib.sha1(key.encode()).hexdigest()[:10],
                "key":key,"title":c["name"],"created_at":now(),"age_days":0,
                "status":"ACTIVE","stage":"DISCOVERY","credit_history":[],
                "milestones":[
                    {"id":"M1","name":"Replicate evidence","status":"PENDING","kill":"<2 independent sources"},
                    {"id":"M2","name":"Resolve mechanism","status":"PENDING","kill":"no causal mechanism candidate"},
                    {"id":"M3","name":"Human bridge","status":"PENDING","kill":"no relevant conserved human context"},
                    {"id":"M4","name":"Adversarial survival","status":"PENDING","kill":"critical Morpheus failure unresolved"},
                    {"id":"M5","name":"Experiment specification","status":"PENDING","kill":"no falsifiable perturbation test"}
                ]
            }
        p["updated_at"]=now()
        p["committee_score"]=c.get("committee_score",0)
        p["labs"]=c.get("labs",[])
        p["sources"]=c.get("sources",[])
        p["mechanisms"]=c.get("mechanisms",[])
        p["genes"]=c.get("genes",[])
        p["taxon_verified"]=bool(c.get("taxon_verified"))
        p["taxon_proofs"]=c.get("taxon_proofs",[])
        p["source_count"]=c.get("source_count",len(c.get("sources",[])))
        p["independent_source_count"]=c.get("independent_source_count",len([s for s in c.get("sources",[]) if str(s).startswith("PMID:")]))
        p["pmid_sources"]=c.get("pmid_sources",[s for s in c.get("sources",[]) if str(s).startswith("PMID:")])
        p["priority_rank"]=rank
        # Scientific promotion gate: exact animal taxonomy + >=2 independent PubMed records.
        if not p["taxon_verified"]:
            p["status"]="REJECTED"
        elif p["independent_source_count"] < 2:
            p["status"]="SCOUT"
        else:
            p["status"]="ACTIVE" if c.get("committee_score",0)>=25 else "PAUSED"
        programs.append(p)
    # Preserve prior programs not currently funded as PAUSED.
    current={p["key"] for p in programs}
    for p in existing.values():
        if p["key"] not in current:
            p["status"]="PAUSED"
            p["updated_at"]=now()
            programs.append(p)
    result={"updated_at":now(),"programs":programs}
    save(STATE/"programs.json",result)
    return result

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--committee",required=True)
    a=ap.parse_args()
    committee=json.loads(Path(a.committee).read_text(encoding="utf-8"))
    print(json.dumps(create_or_update_programs(committee),ensure_ascii=False))
