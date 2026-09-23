#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json

def _stable_id(prefix,payload):
    raw=json.dumps(payload,sort_keys=True,ensure_ascii=False).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(raw).hexdigest()[:12]}"

def _pmids(claim):
    return sorted({str(x) for x in claim.get("pmid_sources",claim.get("sources",[])) if str(x).startswith("PMID:")})

def generate_hypotheses(program,claim,causal_plan=None,bridge_records=None,max_hypotheses=3):
    """Generate falsifiable, evidence-linked hypotheses without promoting them to facts."""
    causal_plan=causal_plan or {}
    bridge_records=bridge_records or []
    subject=claim.get("subject","unknown subject")
    mechanisms=[str(x) for x in claim.get("mechanisms",[]) if str(x).strip()]
    genes=[str(x) for x in claim.get("genes",[]) if str(x).strip()]
    pmids=_pmids(claim)

    mechanism=mechanisms[0] if mechanisms else (genes[0] if genes else "the observed biological mechanism")
    gene=genes[0] if genes else None
    human_targets=sorted({str(b.get("human_symbol")) for b in bridge_records if b.get("human_symbol")})

    templates=[
        {
            "kind":"PRIMARY_CAUSAL",
            "statement":f"In {subject}, {mechanism} contributes causally to the reported phenotype rather than merely correlating with it.",
            "prediction":f"Perturbing {mechanism} should change the phenotype in the predicted direction, and rescue should partially restore it.",
            "falsifier":f"Specific perturbation of {mechanism} produces no reproducible phenotype change under adequate controls."
        },
        {
            "kind":"MARKER_ONLY_ALTERNATIVE",
            "statement":f"In {subject}, {mechanism} is a downstream marker or correlate rather than a causal driver.",
            "prediction":f"The phenotype should persist when {mechanism} changes, provided upstream drivers remain intact.",
            "falsifier":f"Targeted perturbation of {mechanism} reproducibly abolishes the phenotype and rescue restores it."
        },
        {
            "kind":"CONTEXT_DEPENDENT_ALTERNATIVE",
            "statement":f"In {subject}, the effect associated with {mechanism} depends on biological context or interacting pathways.",
            "prediction":f"The effect size should vary across context, lineage, tissue, developmental state, or pathway background.",
            "falsifier":f"The effect remains stable across relevant contexts and does not depend on plausible interacting pathways."
        }
    ]

    out=[]
    for t in templates[:max_hypotheses]:
        payload={
            "program_id":program.get("id"),
            "subject":subject,
            "kind":t["kind"],
            "statement":t["statement"],
            "source_pmids":pmids
        }
        out.append({
            "id":_stable_id("HYP",payload),
            **payload,
            "status":"HYPOTHESIS",
            "prediction":t["prediction"],
            "falsifier":t["falsifier"],
            "mechanisms":mechanisms,
            "genes":genes,
            "human_targets":human_targets,
            "association_only":True,
            "clinical_efficacy_claim":False,
            "counterfactual_tests":list(causal_plan.get("counterfactual_tests",[])),
            "evidence_requirements":[
                "independent replication",
                "causal perturbation",
                "rescue or orthogonal validation",
                "negative control",
                "human-relevant validation only after conservation checks"
            ]
        })
    return out
