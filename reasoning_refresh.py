#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
FACTORY=ROOT/"factory"
STATE=ROOT/"state"/"factory"
PUBLIC=ROOT/"public"/"data"/"factory"
REPORTS=ROOT/"reports"/"factory"
sys.path.insert(0,str(FACTORY))

from reasoning_engine import reason_program
from scientific_memory import update_scientific_memory
from control_plane import morpheus_audit, causal_uncertainty

V9_IDS={"scientific-reasoning","hypothesis-engine","debate-engine","experiment-planner","scientific-memory"}

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

def sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode("utf-8")).hexdigest()

def main():
    latest=STATE/"latest.json"
    cycle=json.loads(latest.read_text(encoding="utf-8"))
    registry=json.loads((FACTORY/"brick_registry.json").read_text(encoding="utf-8"))
    active={x["id"]:x for x in registry["active"]}

    programs=cycle.get("programs",[])
    claims={c["subject"]:c for c in cycle.get("claims",[]) if c.get("status")=="SUPPORTED"}
    bridge_index={}
    for b in (cycle.get("human_bridge_result") or {}).get("bridges",[]):
        bridge_index.setdefault(b.get("animal_species"),[]).append(b)

    dossiers=[]
    for p in programs:
        claim=claims.get(p.get("title"))
        if not claim:
            continue
        audit=morpheus_audit(p,claim)
        causal=causal_uncertainty(claim,audit)
        dossiers.append(reason_program(p,claim,audit,causal,bridge_index.get(claim["subject"],[])))

    cycle["scientific_reasoning"]=dossiers
    cycle["reasoning_refresh"]={
        "time":now(),
        "dossiers":len(dossiers),
        "hypotheses":sum(len(d.get("hypotheses",[])) for d in dossiers),
        "surviving_hypotheses":sum(len(d.get("debate",{}).get("surviving_hypothesis_ids",[])) for d in dossiers),
        "experiment_plans":sum(len(d.get("experiment_plans",[])) for d in dossiers),
        "clinical_efficacy_claims":sum(1 for d in dossiers if d.get("clinical_efficacy_claim") is True)
    }

    mem=update_scientific_memory(STATE/"scientific_reasoning_memory.json",dossiers)

    # Replace only V9 usage events; preserve all prior scientific and Human Bridge events.
    usage=[e for e in cycle.get("brick_usage",[]) if e.get("brick_id") not in V9_IDS]
    values={
        "scientific-reasoning":("scientific_reasoning","reasoning_dossiers_generated",len(dossiers)),
        "hypothesis-engine":("scientific_reasoning","falsifiable_hypotheses_generated",cycle["reasoning_refresh"]["hypotheses"]),
        "debate-engine":("scientific_reasoning","hypotheses_surviving_adversarial_review",cycle["reasoning_refresh"]["surviving_hypotheses"]),
        "experiment-planner":("scientific_reasoning","conceptual_experiment_plans_generated",cycle["reasoning_refresh"]["experiment_plans"]),
        "scientific-memory":("state/factory/scientific_reasoning_memory.json","reasoning_hypotheses_retained",mem.get("hypotheses",0))
    }
    stamp=now()
    for bid,(output_ref,metric,value) in values.items():
        b=active[bid]
        usage.append({
            "brick_id":bid,"name":b["name"],"stage":b["stage"],"time":stamp,
            "output_ref":output_ref,"metric":metric,"value":value,
            "status":"PASS" if value else "PARTIAL"
        })

    cycle["brick_usage"]=usage
    used={e.get("brick_id") for e in usage}
    cycle["unused_active_bricks"]=sorted(set(active)-used)
    cycle.setdefault("telemetry",{})["brick_observability_ratio"]=round(len(used)/max(1,len(active)),4)
    for e in cycle["brick_usage"]:
        if e.get("brick_id")=="omega-telemetry":
            e["value"]=cycle["telemetry"]["brick_observability_ratio"]
            e["status"]="PASS" if e["value"]==1.0 else "PARTIAL"

    # Preserve pre-existing scientific PASS/PARTIAL semantics; V9 refresh may only lower
    # status if a registered brick is unexpectedly missing.
    if cycle["unused_active_bricks"]:
        cycle["status"]="PARTIAL"

    payload=copy.deepcopy(cycle)
    payload.pop("sha256",None)
    cycle["sha256"]=sha(payload)

    save(latest,cycle)
    save(PUBLIC/"latest.json",cycle)
    save(PUBLIC/"brick_usage.json",cycle["brick_usage"])
    save(STATE/"brick_usage_latest.json",cycle["brick_usage"])

    lines=[
        "# BIO-MIMIC X V9 Scientific Reasoning — Latest",
        "",
        f"Time: {cycle['reasoning_refresh']['time']}",
        f"Dossiers: {cycle['reasoning_refresh']['dossiers']}",
        f"Hypotheses: {cycle['reasoning_refresh']['hypotheses']}",
        f"Surviving adversarial review: {cycle['reasoning_refresh']['surviving_hypotheses']}",
        f"Conceptual experiment plans: {cycle['reasoning_refresh']['experiment_plans']}",
        f"Clinical efficacy claims: {cycle['reasoning_refresh']['clinical_efficacy_claims']}",
        f"Active/used bricks: {len(active)}/{len(used)}",
        "",
        "All hypotheses remain hypotheses; all experiment plans are PROPOSED_NOT_EXECUTED."
    ]
    REPORTS.mkdir(parents=True,exist_ok=True)
    (REPORTS/"V9-REASONING-LATEST.md").write_text("\n".join(lines)+"\n",encoding="utf-8")

    print(json.dumps({
        "status":cycle.get("status"),
        **cycle["reasoning_refresh"],
        "active_bricks":len(active),
        "used_bricks":len(used),
        "unused_active_bricks":cycle["unused_active_bricks"],
        "sha256":cycle["sha256"]
    }))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
