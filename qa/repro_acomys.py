#!/usr/bin/env python3
"""Deterministic research software demonstration using curated Acomys literature.

Scope: source provenance and scientific hypothesis triage, NOT an experimental
validation, drug-discovery claim, clinical result, or proof of commercial value.
All records are the project's curated literature registry, not novel findings.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from factory.million_euro_evidence import (  # noqa: E402
    PROGRAMS_PATH, MEMORY_PATH, REGISTRY_PATH,
    EXTERNAL_VALIDATION_PATH, COMMERCIAL_EVIDENCE_PATH,
    load_json, build_package, classify_program,
)

def make_demo():
    programs = load_json(PROGRAMS_PATH)
    memory = load_json(MEMORY_PATH)
    registry = load_json(REGISTRY_PATH)
    independent = load_json(EXTERNAL_VALIDATION_PATH)
    commercial = load_json(COMMERCIAL_EVIDENCE_PATH)

    def evaluate(source=registry):
        return build_package(programs, memory, source, independent, commercial)

    a = evaluate()
    b = evaluate()
    assert a["sha256"] == b["sha256"], "Identical inputs yielded different evidence SHA"
    assert a["flagship"]["title"] == "Acomys cahirinus"
    assert a["flagship"]["eligible_for_investor_package"] is True

    literature = a["flagship"]["registry"]["literature_evidence"]
    primary = [x for x in literature if x["role"] == "primary"]
    assert len(primary) >= 4, "Insufficient curated primary sources"
    source_ids = [x["id"] for x in primary]
    assert len(set(source_ids)) == len(source_ids), "Duplicate sources"
    assert all(re.fullmatch(r"PMID:\d+", x) for x in source_ids), "Untraceable source"
    assert any(int(x["year"]) >= 2025 for x in primary)

    fake_title = classify_program({
        "id": "SYNTHETIC-NOISE", "title": "This study", "taxon_verified": True,
        "sources": ["FIXTURE:A", "FIXTURE:B"], "mechanisms": ["regeneration"],
        "genes": ["IL10"], "status": "ACTIVE"
    })
    fake_taxon = classify_program({
        "id": "SYNTHETIC-TAXON", "title": "Ficticia exemplaris",
        "taxon_verified": False, "sources": ["FIXTURE:A", "FIXTURE:B"],
        "mechanisms": ["regeneration"], "genes": ["IL10"], "status": "ACTIVE"
    })
    assert not fake_title["eligible_for_investor_package"]
    assert "NON_SPECIES_TEXT_FRAGMENT" in fake_title["quality_flags"]
    assert not fake_taxon["eligible_for_investor_package"]
    assert "TAXON_NOT_VERIFIED" in fake_taxon["quality_flags"]

    altered = copy.deepcopy(registry)
    altered["candidates"]["Acomys cahirinus"]["literature_evidence"][0]["year"] += 1
    changed = evaluate(altered)
    assert changed["sha256"] != a["sha256"], "Tampered bibliography left SHA unchanged"

    hypothesis = a["flagship"]["registry"]["proposed_falsification"]
    assert hypothesis["status"] == "PROPOSED_NOT_EXECUTED"
    assert a["external_validation"]["accepted_supporting_validations"] == 0
    assert a["commercial_evidence"]["verified_entries"] == 0
    gates = {g["gate"]: g["status"] for g in a["valuation_readiness"]["gates"]}
    assert gates["independent_lab_validation_of_biomimic_output"] == "UNVERIFIED"
    assert gates["formal_ip_novelty_freedom_to_operate"] == "UNVERIFIED"
    assert gates["paying_customers_or_contracts"] == "UNVERIFIED"

    return {
        "status": "PASS_SOFTWARE_REPLAY_ONLY",
        "subject": "Acomys cahirinus",
        "input_origin": "existing curated literature and state registries",
        "replay_sha256": a["sha256"],
        "repeat_same_input_sha256": b["sha256"],
        "mutated_source_sha256": changed["sha256"],
        "primary_studies": len(primary),
        "primary_source_ids": source_ids,
        "controls": {
            "reject_prose_as_species": "PASS",
            "reject_unverified_taxon": "PASS",
            "detect_source_mutation": "PASS",
            "same_input_same_hash": "PASS"
        },
        "hypothesis": hypothesis["hypothesis"],
        "hypothesis_status": hypothesis["status"],
        "external_validation": "UNVERIFIED",
        "clinical_efficacy": "NOT_TESTED",
        "commercial_valuation": "NOT_ESTABLISHED",
        "claim": "reproducible bibliographic triage, not a new validated discovery"
    }

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="")
    args = p.parse_args()
    report = make_demo()
    encoded = json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")
    print(json.dumps({
        "status": report["status"], "subject": report["subject"],
        "primary_studies": report["primary_studies"],
        "sha256": report["replay_sha256"],
        "negative_controls": "PASS", "experimental_validation": "UNVERIFIED"
    }, sort_keys=True))
