#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json

def _sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode("utf-8")).hexdigest()

def plan_experiments(program,claim,hypotheses,debate,causal_plan=None,max_plans=2):
    """Create conceptual falsification plans. No experiment is represented as executed."""
    causal_plan=causal_plan or {}
    by_id={h["id"]:h for h in hypotheses}
    ordered=[x["hypothesis_id"] for x in debate.get("ranked",[]) if x["hypothesis_id"] in by_id]
    plans=[]
    for hid in ordered[:max_plans]:
        h=by_id[hid]
        plan={
            "program_id":program.get("id"),
            "hypothesis_id":hid,
            "subject":claim.get("subject"),
            "status":"PROPOSED_NOT_EXECUTED",
            "objective":"Distinguish the nominated causal explanation from marker-only and context-dependent alternatives.",
            "null_hypothesis":"The nominated mechanism does not causally alter the phenotype under the tested conditions.",
            "design":[
                "pre-register primary phenotype and exclusion criteria",
                "include untreated/baseline and negative controls",
                "perturb the nominated mechanism with an appropriate validated method",
                "perform an orthogonal or rescue validation where feasible",
                "repeat across independent biological replicates",
                "analyze effect direction, uncertainty, and failure conditions"
            ],
            "predicted_if_supported":h.get("prediction"),
            "falsifier":h.get("falsifier"),
            "counterfactual_tests":list(causal_plan.get("counterfactual_tests",[])),
            "kill_criteria":[
                "no reproducible phenotype change",
                "effect disappears under independent replication",
                "negative controls reproduce the claimed effect",
                "an alternative hypothesis explains the observations with fewer unsupported assumptions"
            ],
            "source_pmids":list(h.get("source_pmids",[])),
            "clinical_efficacy_claim":False
        }
        plan["sha256"]=_sha(plan)
        plans.append(plan)
    return plans
