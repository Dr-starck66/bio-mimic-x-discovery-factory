#!/usr/bin/env python3
"""Read-only ANRS RHIVIERA evidence bridge to existing BIO-MIMIC X engines.

This is a metadata/hypothesis comparison, not a therapeutic validation,
clinical protocol, or experiment involving HIV. No network or patient data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from factory.hypothesis_engine import generate_hypotheses
from factory.debate_engine import debate_hypotheses
from factory.experiment_planner import plan_experiments
from factory.scientific_memory import update_scientific_memory

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "rhiviera_public_evidence.json"
RELATIONS = {"anrs_trial", "anrs_pvisconti", "anrs_associated_human_study"}
VALID_SPECIES = {"human", "SIV_in_macaque", "human_ex_vivo"}


def _digest(obj):
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_evidence(data):
    errors = []
    if data.get("schema") != "astra-rhiviera-public-evidence/1":
        errors.append("unsupported schema")
    if data.get("clinical_cure_proven") is not False:
        errors.append("unproven clinical cure claim")
    records = data.get("records", [])
    if not records:
        errors.append("missing records")
    ids = set()
    for row in records:
        ident = row.get("id")
        if not ident or ident in ids:
            errors.append("duplicate or empty record id")
        ids.add(ident)
        relation = row.get("relation")
        species = row.get("species")
        if relation not in RELATIONS or species not in VALID_SPECIES:
            errors.append(f"{ident}: unknown origin or species")
        if relation == "anrs_pvisconti" and species != "SIV_in_macaque":
            errors.append(f"{ident}: invalid transfer of macaque result to human")
        if relation == "anrs_trial" and (species != "human" or row.get("has_results") is not False):
            errors.append(f"{ident}: trial outcome was not verified")
        if relation == "anrs_associated_human_study" and species != "human_ex_vivo":
            errors.append(f"{ident}: ex vivo evidence misrepresented as clinical")
        if not row.get("mechanisms") or not row.get("subject"):
            errors.append(f"{ident}: no hypothesis mechanism")
        if not row.get("limitations") or not row.get("negative_control"):
            errors.append(f"{ident}: missing adversity/negative control")
        if row.get("eradication_demonstrated", False) is not False:
            errors.append(f"{ident}: unsupported eradication claim")
        p = urlparse(row.get("source_url", ""))
        if p.scheme != "https" or not p.netloc or p.username or p.password:
            errors.append(f"{ident}: untraceable primary source")
        if relation == "anrs_trial" and p.hostname != "anrs.fr":
            errors.append(f"{ident}: official ANRS source required")
        if relation == "anrs_pvisconti" and p.hostname not in {"www.nature.com", "pubmed.ncbi.nlm.nih.gov"}:
            errors.append(f"{ident}: primary article required")
        if row.get("has_results") and not row.get("pmid"):
            errors.append(f"{ident}: PMID required for observed findings")
    comparator = data.get("independent_comparator", {})
    if comparator.get("relation") != "independent_comparator_not_rhiviera":
        errors.append("RIO cannot be attributed to ANRS RHIVIERA")
    if comparator.get("id") in ids:
        errors.append("independent trial misattributed to RHIVIERA")
    safety = data.get("safety", {})
    if not all(safety.get(k) is True for k in (
        "no_ART_interruption_recommendation",
        "no_experiment_on_humans_or_virus",
        "no_individual_patient_data",
    )):
        errors.append("safety policy missing")
    return errors


def run_bridge(data):
    problems = validate_evidence(data)
    if problems:
        raise ValueError("; ".join(problems))
    dossiers = []
    for row in data["records"]:
        program = {"id": "RHIVIERA-PUBLIC-" + row["id"]}
        claim = {
            "subject": row["subject"],
            "mechanisms": row["mechanisms"],
            "genes": row.get("genes", []),
            "pmid_sources": ["PMID:" + str(row["pmid"])] if row.get("pmid") else [],
        }
        # Adversarial flags enforce that observational association is not causality.
        flags = ["correlation not causation"]
        if row["species"] == "SIV_in_macaque":
            flags.append("SIV macaque is not human clinical efficacy")
        if row["species"] == "human_ex_vivo":
            flags.append("ex vivo result is not in-vivo elimination")
        if not row["has_results"]:
            flags.append("study protocol: no outcomes verified")
        causal_plan = {"counterfactual_tests": [
            "Consider the documented negative comparator: " + row["negative_control"],
            "Independent replication with appropriate confounder analysis; public data only",
        ]}
        hypotheses = generate_hypotheses(
            program, claim, causal_plan=causal_plan, bridge_records=[],
            max_hypotheses=3,
        )
        debate = debate_hypotheses(
            hypotheses, claim, audit={"flags": flags},
            causal_plan=causal_plan,
        )
        plans = plan_experiments(
            program, claim, hypotheses, debate,
            causal_plan=causal_plan, max_plans=2,
        )
        if any(h.get("clinical_efficacy_claim") is not False or
               h.get("status") != "HYPOTHESIS" for h in hypotheses):
            raise ValueError("engine promoted an unproven clinical claim")
        if any(p.get("status") != "PROPOSED_NOT_EXECUTED" or
               p.get("clinical_efficacy_claim") is not False for p in plans):
            raise ValueError("unexecuted experiment promoted to a result")
        dossiers.append({
            "record_id": row["id"],
            "source_url": row["source_url"],
            "pmid": row.get("pmid"),
            "relation": row["relation"],
            "species": row["species"],
            "study_design": row["design"],
            "has_verified_results": row["has_results"],
            "observation": row["observation"],
            "limitations": row["limitations"],
            "negative_control": row["negative_control"],
            "hypotheses": [{
                "id": h["id"],
                "kind": h["kind"],
                "subject": h["subject"],
                "status": h["status"],
                "statement": h["statement"],
                "falsifier": h["falsifier"],
                "source_pmids": h["source_pmids"],
                "clinical_efficacy_claim": False,
            } for h in hypotheses],
            "adversarial_review": {
                "status_by_hypothesis": {
                    h["hypothesis_id"]: h["status"] for h in debate["ranked"]
                },
                "objections": debate["adversarial_flags"],
                "priority_score_warning": "Any engine heuristic is NOT a probability of cure",
            },
            "conceptual_plans": [{
                "hypothesis_id": p["hypothesis_id"],
                "status": p["status"],
                "source_pmids": p["source_pmids"],
                "scope": "metadata-only / computational evidence review",
                "clinical_efficacy_claim": False,
            } for p in plans],
            "eradication_demonstrated": False,
        })
    report = {
        "schema": "astra-rhiviera-bridge-report/1",
        "as_of": data["as_of"],
        "source_dataset_sha256": _digest(data),
        "engines_invoked": [
            "factory.hypothesis_engine.generate_hypotheses",
            "factory.debate_engine.debate_hypotheses",
            "factory.experiment_planner.plan_experiments",
        ],
        "studies_checked": len(dossiers),
        "hypotheses_generated": sum(len(d["hypotheses"]) for d in dossiers),
        "conceptual_plans_generated": sum(len(d["conceptual_plans"]) for d in dossiers),
        "independent_comparator": data["independent_comparator"],
        "dossiers": dossiers,
        "clinical_cure_proven": False,
        "execution_status": "LOCAL_COMPUTATIONAL_ANALYSIS_ONLY",
        "scientific_status": "HYPOTHESES_NOT_CLINICALLY_VALIDATED",
    }
    report["report_sha256"] = _digest(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--memory", type=Path, default=None,
                        help="Optional standalone BIO-MIMIC scientific memory JSON path")
    args = parser.parse_args(argv)
    raw = json.loads(args.data.read_text(encoding="utf-8"))
    report = run_bridge(raw)
    if args.memory:
        memory_dossiers = [{
            "program_id": "RHIVIERA-PUBLIC-" + d["record_id"],
            "subject": d["observation"],
            "sha256": _digest(d),
            "reasoning_status": "HYPOTHESIS_ONLY_NOT_CLINICALLY_VALIDATED",
            "hypotheses": d["hypotheses"],
        } for d in report["dossiers"]]
        report["memory_update"] = update_scientific_memory(
            args.memory, memory_dossiers
        )
        report["report_sha256"] = _digest({
            k: v for k, v in report.items() if k not in ("report_sha256", "memory_update")
        })
    output = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
