#!/usr/bin/env python3
from __future__ import annotations

CRITICAL_CAUSAL_FLAGS={
    "correlation not causation",
    "phenotype without mechanism",
}

def _score(h,audit,claim):
    pmids=len(set(h.get("source_pmids",[])))
    mechanisms=len(h.get("mechanisms",[]))
    genes=len(h.get("genes",[]))
    flags=len((audit or {}).get("flags",[]))
    # Evidence-prioritization score only. It is never a probability of truth.
    return round(max(0.0,min(1.0,0.20 + min(pmids,4)*0.10 + min(mechanisms,2)*0.08 + min(genes,2)*0.04 - min(flags,8)*0.035)),4)

def _review_status(h, objections, counter_tests):
    """Fail closed on causal promotion when causal evidence is explicitly missing."""
    kind=h.get("kind")
    normalized={str(x).strip().lower() for x in objections}
    if not counter_tests:
        return "NEEDS_DISCRIMINATING_TEST"
    if kind=="PRIMARY_CAUSAL" and normalized.intersection(CRITICAL_CAUSAL_FLAGS):
        return "NEEDS_CAUSAL_EVIDENCE"
    if not h.get("source_pmids"):
        return "LOW_EVIDENCE"
    return "SURVIVES_AS_ALTERNATIVE"

def debate_hypotheses(hypotheses,claim,audit=None,causal_plan=None):
    """Adversarially compare hypotheses without converting association into causation."""
    audit=audit or {}
    causal_plan=causal_plan or {}
    ranked=[]
    counter_tests=list(causal_plan.get("counterfactual_tests",[]))
    for h in hypotheses:
        support=[
            f"{len(set(h.get('source_pmids',[])))} independent PMID-linked sources",
            f"{len(h.get('mechanisms',[]))} recorded mechanisms",
            f"{len(h.get('genes',[]))} recorded gene/protein candidates"
        ]
        objections=list(audit.get("flags",[]))
        if not h.get("human_targets"):
            objections.append("no verified human target in this hypothesis dossier")
        if h.get("kind")=="PRIMARY_CAUSAL":
            objections.append("association does not establish causation")
        objections=sorted(set(objections))
        score=_score(h,audit,claim)
        status=_review_status(h,objections,counter_tests)
        ranked.append({
            "hypothesis_id":h["id"],
            "kind":h.get("kind"),
            "evidence_support":support,
            "objections":objections,
            "counter_tests":counter_tests,
            "evidence_priority_score":score,
            "score_semantics":"heuristic evidence-prioritization score; not probability, efficacy, or truth",
            "status":status,
            "clinical_efficacy_claim":False
        })
    ranked.sort(key=lambda x:(x["evidence_priority_score"],x["hypothesis_id"]),reverse=True)
    survivors=[x["hypothesis_id"] for x in ranked if x["status"]=="SURVIVES_AS_ALTERNATIVE"]
    blocked=[x["hypothesis_id"] for x in ranked if x["status"]!="SURVIVES_AS_ALTERNATIVE"]
    return {
        "ranked":ranked,
        "surviving_hypothesis_ids":survivors,
        "blocked_or_pending_hypothesis_ids":blocked,
        "adversarial_flags":sorted({f for x in ranked for f in x["objections"]}),
        "decision_rule":"fail closed on causal promotion; alternatives may survive only as hypotheses pending discriminating tests"
    }
