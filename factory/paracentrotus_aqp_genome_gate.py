#!/usr/bin/env python3
from __future__ import annotations

ACCEPTED_STRICT_PROVIDERS={
    "Ensembl Compara","NCBI Ortholog","OMA","OrthoDB v12",
    "Peer-reviewed phylogenetic orthology"
}

def evaluate_aqp3_genome_candidate(candidate):
    """Fail-closed promotion gate for Paracentrotus lividus AQP3 candidates."""
    reasons=[]
    if candidate.get("species")!="Paracentrotus lividus":
        reasons.append("wrong species")
    if int(candidate.get("taxon_id") or 0)!=7656:
        reasons.append("wrong taxon")
    if str(candidate.get("gene") or "").upper()!="AQP3":
        reasons.append("wrong gene")
    if str(candidate.get("human_symbol") or "").upper()!="AQP3":
        reasons.append("wrong human target")
    if candidate.get("human_ensembl_id")!="ENSG00000165272":
        reasons.append("wrong human Ensembl target")
    if not candidate.get("exact_species_sequence_id"):
        reasons.append("missing exact-species sequence identifier")
    if not candidate.get("paralogue_controls_pass"):
        reasons.append("paralogue controls not passed")
    provider=str(candidate.get("orthology_provider") or "")
    if provider not in ACCEPTED_STRICT_PROVIDERS:
        reasons.append("no accepted orthology provider/dossier")
    if not candidate.get("orthology_evidence_id"):
        reasons.append("missing orthology evidence identifier")
    if not candidate.get("open_targets_validated"):
        reasons.append("Open Targets validation missing")
    if candidate.get("evidence_is_name_only"):
        reasons.append("annotation name alone is not orthology proof")
    if candidate.get("evidence_is_similarity_only"):
        reasons.append("sequence similarity alone is not orthology proof")
    return {
        "status":"PROMOTION_READY" if not reasons else "WATCHING",
        "promotion_ready":not reasons,
        "reasons":reasons,
        "clinical_efficacy_claim":False
    }
