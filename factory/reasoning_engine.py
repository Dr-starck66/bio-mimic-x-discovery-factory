#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from hypothesis_engine import generate_hypotheses
from debate_engine import debate_hypotheses
from experiment_planner import plan_experiments

def _fingerprint(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode("utf-8")).hexdigest()

def reason_program(program,claim,audit=None,causal_plan=None,bridge_records=None):
    """Build a reproducible scientific reasoning dossier from already-grounded evidence."""
    audit=audit or {}
    causal_plan=causal_plan or {}
    bridge_records=bridge_records or []
    hypotheses=generate_hypotheses(program,claim,causal_plan,bridge_records)
    debate=debate_hypotheses(hypotheses,claim,audit,causal_plan)
    experiments=plan_experiments(program,claim,hypotheses,debate,causal_plan)
    contradictions=sorted(set(audit.get("flags",[])))
    dossier={
        "schema":"biomimic-scientific-reasoning-v1",
        "program_id":program.get("id"),
        "subject":claim.get("subject"),
        "evidence_status":claim.get("status"),
        "source_pmids":list(claim.get("pmid_sources",[])),
        "hypotheses":hypotheses,
        "debate":debate,
        "contradictions":contradictions,
        "experiment_plans":experiments,
        "human_bridge_count":len(bridge_records),
        "reasoning_status":"PROPOSED_AND_FALSIFIABLE",
        "claims_established_truth":False,
        "experiments_executed":False,
        "clinical_efficacy_claim":False
    }
    dossier["sha256"]=_fingerprint(dossier)
    return dossier
