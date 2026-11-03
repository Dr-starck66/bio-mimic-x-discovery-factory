#!/usr/bin/env python3
"""ASTRA Scientific Discovery Ω: zero-budget, CPU-only, evidence-first research cycle.

Does not perform molecular design, laboratory experiments, or paid GPU calls.
Uses existing BIO-MIMIC X hypothesis_engine and experiment_planner.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from hypothesis_engine import generate_hypotheses
from experiment_planner import plan_experiments

SCHEMA = "astra-scientific-discovery-omega/1"


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _is_url(value):
    return isinstance(value, str) and value.startswith(("https://", "http://"))


def propose(knowledge, focus="regeneration", limit=5):
    """Rank existing benign science cases; labels are *not* experimental proof."""
    if limit < 1:
        raise ValueError("limit must be positive")
    species = knowledge.get("species", [])
    if not isinstance(species, list):
        raise ValueError("species must be a list")
    candidates = []
    for item in species:
        if not isinstance(item, dict):
            continue
        traits = item.get("traits", [])
        modules = item.get("modules", [])
        if not isinstance(traits, list) or not isinstance(modules, list):
            continue
        if focus.casefold() not in " ".join(str(t) for t in traits).casefold():
            continue
        if not _is_url(item.get("url")) or not item.get("latin") or not modules:
            continue
        # Ranking uses catalogue metadata as *heuristics*, not validated data.
        evidence = max(0, min(5, int(item.get("evidence", 0))))
        translation = max(0, min(5, int(item.get("humanity", 0))))
        score = (evidence * 3) + translation
        candidates.append((score, str(item.get("latin")), item))
    candidates.sort(key=lambda x: (-x[0], x[1]))
    programs = []
    for score, _, item in candidates[:limit]:
        program = {"id": "ASTRA-" + digest({"species": item["latin"], "focus": focus})[:12],
                   "focus": focus}
        claim = {"subject": item["latin"], "mechanisms": item["modules"],
                 "genes": [], "pmid_sources": []}
        hypotheses = generate_hypotheses(program, claim, max_hypotheses=3)
        debate = {"ranked": [{"hypothesis_id": h["id"]} for h in hypotheses]}
        causal = {"counterfactual_tests": [
            "Blindly analyze an appropriate negative-control condition",
            "Compare with an unrelated biological mechanism",
            "Require replication on a truly independent dataset",
        ]}
        plans = plan_experiments(program, claim, hypotheses, debate, causal, max_plans=2)
        programs.append({
            "program_id": program["id"], "species": item["latin"],
            "source_url": item["url"], "catalogue_score": score,
            "catalogue_score_not_independently_verified": True,
            "hypotheses": hypotheses, "experiments": plans,
            "status": "PROPOSED_NOT_EXECUTED",
        })
    return programs


def retrospective_audit_csv(path):
    """Read-only audit of published labeled results. No sequence design or sequence output."""
    with Path(path).open(newline="", encoding="utf-8-sig") as fp:
        rows = list(csv.DictReader(fp))
    expected = {"uuid", "binder_against", "intended_toxins"}
    if not rows or not expected.issubset(rows[0]):
        raise ValueError("missing required Anthropic design.csv columns")
    uuids = [r["uuid"].strip() for r in rows]
    if any(not x for x in uuids) or len(set(uuids)) != len(uuids):
        raise ValueError("duplicate or empty design ID")
    labels = {}
    for r in rows:
        label = (r["binder_against"] or "").strip()
        if label.lower() in {"nan", "none", "null", "no binder", "no hit"}:
            label = ""
        if label:
            # Only published outcomes; never produce sequences or new designs.
            for target in [x.strip() for x in label.split(",") if x.strip()]:
                labels[target] = labels.get(target, 0) + 1
    return {
        "source": "Anthropic/scorpion-toxin-binder-design/design.csv",
        "dataset_url": "https://huggingface.co/datasets/Anthropic/scorpion-toxin-binder-design",
        "record_count": len(rows), "binder_designs": sum(bool((r["binder_against"] or "").strip()) for r in rows),
        "binding_outcomes_by_target": dict(sorted(labels.items())),
        "designs_without_reported_binder": len(rows) - sum(bool((r["binder_against"] or "").strip()) for r in rows),
        "laboratory_work_performed_by_astra": False,
        "prediction_out_of_sample_demonstrated": False,
        "sequence_design_performed_by_astra": False,
        "status": "PARTIAL",
    }


def run(knowledge, focus="regeneration", limit=5, retrospective=None):
    programs = propose(knowledge, focus, limit)
    audit = retrospective_audit_csv(retrospective) if retrospective else None
    report = {
        "schema": SCHEMA,
        "project": "BIO-MIMIC X / ASTRA Scientific Discovery Ω",
        "mode": "CPU_ONLY_NO_EXTERNAL_PAYMENTS",
        "focus": focus,
        "candidate_program_count": len(programs),
        "programs": programs,
        "retrospective_benchmark": audit,
        "biological_validation": "UNVERIFIED",
        "external_source_validation": "UNVERIFIED",
        "status": "PARTIAL" if programs or audit else "UNVERIFIED",
        "limitations": [
            "Catalogue scores are not independent evidence",
            "Hypotheses and experiments are plans, not executed experiments",
            "No independent biological validation or de novo protein generation",
            "No paid compute and no automatic scheduling",
        ],
    }
    report["sha256"] = digest(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge", default="data/knowledge-base.json")
    parser.add_argument("--focus", default="regeneration")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--retrospective-csv", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    knowledge = json.loads(Path(args.knowledge).read_text(encoding="utf-8"))
    report = run(knowledge, args.focus, args.limit, args.retrospective_csv)
    encoded = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(encoded, encoding="utf-8")
    print(json.dumps({"status": report["status"], "programs": report["candidate_program_count"],
                      "sha256": report["sha256"], "retrospective": report["retrospective_benchmark"]},
                     ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
