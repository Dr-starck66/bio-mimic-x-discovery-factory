#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc).isoformat()

def load_memory(path):
    path=Path(path)
    if not path.exists():
        return {"schema":"biomimic-scientific-memory-v1","updated_at":None,"programs":{},"hypotheses":{},"events":[]}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"schema":"biomimic-scientific-memory-v1","updated_at":None,"programs":{},"hypotheses":{},"events":[]}

def update_scientific_memory(path,dossiers,max_events=1000):
    """Persist hypothesis lineage without rewriting hypotheses into facts."""
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    mem=load_memory(path)
    stamp=_now()
    new_hypotheses=0
    for d in dossiers:
        pid=str(d.get("program_id") or "")
        if not pid:
            continue
        previous=mem["programs"].get(pid)
        mem["programs"][pid]={
            "subject":d.get("subject"),
            "latest_reasoning_sha256":d.get("sha256"),
            "latest_status":d.get("reasoning_status"),
            "updated_at":stamp
        }
        for h in d.get("hypotheses",[]):
            hid=h.get("id")
            if not hid:
                continue
            if hid not in mem["hypotheses"]:
                new_hypotheses+=1
            mem["hypotheses"][hid]={
                "program_id":pid,
                "subject":h.get("subject"),
                "kind":h.get("kind"),
                "statement":h.get("statement"),
                "status":h.get("status"),
                "source_pmids":h.get("source_pmids",[]),
                "clinical_efficacy_claim":False,
                "updated_at":stamp
            }
        if previous is None or previous.get("latest_reasoning_sha256")!=d.get("sha256"):
            mem["events"].append({
                "time":stamp,
                "program_id":pid,
                "subject":d.get("subject"),
                "reasoning_sha256":d.get("sha256"),
                "event":"REASONING_DOSSIER_UPDATED"
            })
    mem["events"]=mem["events"][-max_events:]
    mem["updated_at"]=stamp
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(mem,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)
    return {"programs":len(mem["programs"]),"hypotheses":len(mem["hypotheses"]),"new_hypotheses":new_hypotheses,"events":len(mem["events"])}
