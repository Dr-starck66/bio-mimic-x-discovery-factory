#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "factory" / "microclean_x_candidates.json"
REPORT_DIR = ROOT / "reports" / "microclean-x"
PUBLIC_DIR = ROOT / "public" / "data" / "microclean-x"

REQUIRED_BOOL = (
    "microplastic_direct_evidence",
    "magnetic_recovery_precedent",
    "water_remediation_precedent",
    "soil_fate_reviewed",
    "reusability_precedent",
    "contains_nickel",
    "contains_cobalt",
    "nanoparticle_release_risk_open",
)

def _sha(obj):
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

def load_seed(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("campaign", {}).get("id") == "MICROCLEAN-X"
    sources = data.get("sources", {})
    candidates = data.get("candidates", [])
    assert sources and candidates
    ids = set()
    for c in candidates:
        assert c["id"] not in ids, f"duplicate candidate id: {c['id']}"
        ids.add(c["id"])
        assert c.get("role") in {"REFERENCE", "HYPOTHESIS"}
        for field in REQUIRED_BOOL:
            assert isinstance(c.get(field), bool), f"{c['id']} missing boolean {field}"
        assert c.get("sources"), f"{c['id']} has no provenance"
        for source_id in c["sources"]:
            assert source_id in sources, f"{c['id']} unknown source {source_id}"
        assert c.get("risk_flags"), f"{c['id']} missing risk flags"
    return data

def research_priority_score(c):
    """Heuristic for what to validate next; never a safety or efficacy score."""
    score = 0
    score += 25 if c["microplastic_direct_evidence"] else 0
    score += 20 if c["magnetic_recovery_precedent"] else 0
    score += 15 if c["water_remediation_precedent"] else 0
    score += 15 if c["soil_fate_reviewed"] else 0
    score += 10 if c["reusability_precedent"] else 0
    score -= 35 if c["contains_nickel"] else 0
    score -= 20 if c["contains_cobalt"] else 0
    score -= 10 if c["nanoparticle_release_risk_open"] else 0
    return max(0, score)

def gate(c):
    if c["role"] == "REFERENCE":
        return "REFERENCE_NOT_DEPLOYABLE"
    if c["contains_nickel"] or c["contains_cobalt"]:
        return "HOLD_METAL_HAZARD"
    if not c["microplastic_direct_evidence"]:
        return "SCOUT_NEEDS_DIRECT_VALIDATION"
    if c["nanoparticle_release_risk_open"]:
        return "HOLD_RELEASE_RISK"
    if not c["reusability_precedent"]:
        return "HOLD_REUSE_EVIDENCE"
    return "PROMOTE_FOR_REPLICATION"

def validation_plan(candidate_id):
    return {
        "candidate_id": candidate_id,
        "status": "PROPOSED_NOT_EXECUTED",
        "sequence": [
            "water capture benchmark against Ti3C2Tx@Ni using polystyrene and PET controls",
            "water-permeated soil extraction benchmark using the same polymer classes",
            "magnetic retrieval mass balance: quantify unrecovered robot material after each run",
            "metal/particle release assay before and after actuation",
            "ten-cycle capture/recovery/reuse durability test",
            "ecotoxicity screen on environmentally relevant organisms and matrix controls",
            "mixed-polymer and natural-water challenge only after the preceding gates pass"
        ],
        "kill_criteria": [
            "microplastic removal fails to reproduce above passive-adsorbent control",
            "material recovery is incomplete beyond a pre-registered tolerance",
            "measurable secondary contamination exceeds the pre-registered safety threshold",
            "performance collapses during repeated cycles",
            "ecotoxicity signal is materially worse than matched controls"
        ]
    }

def build_report(seed):
    rows = []
    for c in seed["candidates"]:
        rows.append({
            "id": c["id"],
            "label": c["label"],
            "role": c["role"],
            "gate": gate(c),
            "research_priority_score": research_priority_score(c),
            "score_semantics": "heuristic research-priority score; not efficacy or safety",
            "source_count": len(c["sources"]),
            "risk_flags": c["risk_flags"],
            "validation_plan": validation_plan(c["id"]) if c["role"] == "HYPOTHESIS" else None
        })
    hypotheses = sorted(
        [r for r in rows if r["role"] == "HYPOTHESIS"],
        key=lambda x: (-x["research_priority_score"], x["id"])
    )
    promoted = [r for r in rows if r["gate"] == "PROMOTE_FOR_REPLICATION"]
    report = {
        "campaign": seed["campaign"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "evidence_policy": {
            "fail_closed": True,
            "no_unvalidated_safety_claims": True,
            "no_unvalidated_efficacy_claims": True,
            "promotion_requires_direct_microplastic_evidence": True,
            "promotion_requires_closed_release_risk": True,
            "promotion_requires_reuse_evidence": True
        },
        "candidates": rows,
        "next_validation_queue": [x["id"] for x in hypotheses],
        "promoted_candidates": [x["id"] for x in promoted],
        "interpretation": (
            "No nickel-free hypothesis is treated as validated merely because iron-oxide "
            "or coating precedents exist. The queue prioritizes experiments, not deployment."
        )
    }
    report["sha256"] = _sha({k: v for k, v in report.items() if k not in {"generated_at", "sha256"}})
    return report

def write_outputs(report):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (REPORT_DIR / "latest.json").write_text(payload, encoding="utf-8")
    (PUBLIC_DIR / "latest.json").write_text(payload, encoding="utf-8")
    top = report["next_validation_queue"][0] if report["next_validation_queue"] else "NONE"
    md = [
        "# MICROCLEAN-X — latest evidence gate",
        "",
        f"- Status: **{report['status']}**",
        f"- Reference DOI: **{report['campaign']['reference_doi']}**",
        f"- Priority validation target: **{top}**",
        f"- Promoted candidates: **{len(report['promoted_candidates'])}**",
        f"- Evidence fingerprint: `{report['sha256']}`",
        "",
        "No candidate is declared environmentally safe or field-ready by this report.",
        "Scores only prioritize what should be tested next.",
        ""
    ]
    (REPORT_DIR / "LATEST.md").write_text("\n".join(md), encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(DEFAULT_INPUT))
    p.add_argument("--no-write", action="store_true")
    args = p.parse_args()
    seed = load_seed(Path(args.input))
    report = build_report(seed)
    if not args.no_write:
        write_outputs(report)
    print(json.dumps({
        "status": report["status"],
        "queue": report["next_validation_queue"],
        "promoted": report["promoted_candidates"],
        "sha256": report["sha256"]
    }, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
