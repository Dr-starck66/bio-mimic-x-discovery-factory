#!/usr/bin/env python3
from __future__ import annotations

def _score(h,audit,claim):
    pmids=len(set(h.get("source_pmids",[])))
    mechanisms=len(h.get("mechanisms",[]))
    genes=len(h.get("genes",[]))
    flags=len((audit or {}).get("flags",[]))
    # Evidence-prioritization score, not a probability and not biological truth.
    return round(max(0.0,min(1.0,0.20 + min(pmids,4)*0.10 + min(mechanisms,2)*0.08 + min(genes,2)*0.04 - min(flags,8)*0.035)),4)

def debate_hypotheses(hypotheses,claim,audit=None,causal_plan=None):
    """Adversarially compare hypotheses. Scores are ranking aids, never probabilities."""
    audit=audit or {}
    causal_plan=causal_plan or {}
    ranked=[]
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
        score=_score(h,audit,claim)
        ranked.append({
            "hypothesis_id":h["id"],
            "kind":h.get("kind"),
            "evidence_support":support,
            "objections":sorted(set(objections)),
            "counter_tests":list(causal_plan.get("counterfactual_tests",[])),
            "evidence_priority_score":score,
            "score_semantics":"heuristic evidence-prioritization score; not probability, efficacy, or truth",
            "status":"SURVIVES_REVIEW" if score>=0.25 else "LOW_PRIORITY",
            "clinical_efficacy_claim":False
        })
    ranked.sort(key=lambda x:(x["evidence_priority_score"],x["hypothesis_id"]),reverse=True)
    return {
        "ranked":ranked,
        "surviving_hypothesis_ids":[x["hypothesis_id"] for x in ranked if x["status"]=="SURVIVES_REVIEW"],
        "adversarial_flags":sorted({f for x in ranked for f in x["objections"]}),
        "decision_rule":"prioritize evidence-rich falsifiable hypotheses; never promote ranking to scientific fact"
    }
