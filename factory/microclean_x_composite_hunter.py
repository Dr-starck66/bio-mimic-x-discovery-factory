#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"factory"/"microclean_x_composites.json"
REPORT_DIR=ROOT/"reports"/"microclean-x"
PUBLIC_DIR=ROOT/"public"/"data"/"microclean-x"
STATE_DIR=ROOT/"state"/"microclean-x"

def _sha(obj):
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()

def load_registry(path=REGISTRY):
    x=json.loads(Path(path).read_text(encoding="utf-8"))
    assert x["campaign_id"]=="MICROCLEAN-X"
    assert x["phase"]==3
    assert x["policy"]["fail_closed"] is True
    ids=set()
    for c in x["candidates"]:
        assert c["id"] not in ids
        ids.add(c["id"])
        assert c["direct_evidence"] is True
        assert c.get("doi") or c.get("pmid")
        assert c["metrics"]["magnetic_recovery"] is True
        assert c["risks"]
        assert c["advantages"]
    return x

def evidence_completeness(c):
    m=c["metrics"]
    checks={
        "direct_evidence": bool(c.get("direct_evidence")),
        "persistent_identifier": bool(c.get("doi") or c.get("pmid")),
        "removal_metric": m.get("max_removal_pct") is not None,
        "magnetic_recovery": bool(m.get("magnetic_recovery")),
        "reuse_metric": m.get("reuse_cycles") is not None and m.get("retained_removal_pct_after_reuse") is not None,
        "real_matrix": bool(m.get("real_matrix_tested")),
        "risk_ledger": bool(c.get("risks")),
    }
    return checks, sum(checks.values())/len(checks)

def research_priority(c):
    """
    Research-priority heuristic.
    It deliberately rewards evidence quality and translational breadth,
    while penalising unresolved material hazards. It is not an efficacy
    or safety score.
    """
    m=c["metrics"]
    score=0.0
    score += min(35.0, float(m.get("max_removal_pct") or 0)*0.35)
    if m.get("reuse_cycles"):
        score += min(15.0, float(m["reuse_cycles"])*3.0)
    if m.get("retained_removal_pct_after_reuse") is not None:
        score += min(15.0, float(m["retained_removal_pct_after_reuse"])*0.15)
    if m.get("real_matrix_tested"):
        score += 15.0
    if m.get("magnetic_recovery"):
        score += 10.0
    architecture=c["architecture"].lower()
    if "mil-101(cr)" in architecture:
        score -= 12.0
    if "carbon black" in architecture:
        score -= 4.0
    if "tio2" in architecture:
        score -= 3.0
    return round(max(0.0,min(100.0,score)),2)

def risk_burden(c):
    a=c["architecture"].lower()
    flags=[]
    if "mil-101(cr)" in a:
        flags.append("chromium-bearing-material")
    if "carbon black" in a:
        flags.append("carbon-black-release")
    if "tio2" in a:
        flags.append("tio2-nanoparticle-fate")
    if "biochar" in a:
        flags.append("surface-modifier-release")
    if "@pda" in a:
        flags.append("strong-pH-regeneration")
    return flags

def falsification_plan(c):
    return {
        "status":"PROPOSED_NOT_EXECUTED",
        "candidate_id":c["id"],
        "must_test":[
            "head-to-head removal against the Ti3C2Tx@Ni reference under identical polymer loading",
            "magnetic recovery mass balance after each run",
            "metal/particle/coating release before and after actuation",
            "performance across at least PS, PET and PE",
            "natural-water or wastewater matrix challenge",
            "ten-cycle reuse challenge",
            "matched ecotoxicity controls"
        ],
        "kill_criteria":[
            "removal is not reproducible across independent replicates",
            "magnetic recovery leaves material above a pre-registered loss threshold",
            "secondary contaminant release exceeds the pre-registered threshold",
            "performance collapses materially by cycle 10",
            "candidate is materially more ecotoxic than the reference/control",
            "advantage disappears outside a single polymer or idealised matrix"
        ]
    }

def build(reg):
    rows=[]
    for c in reg["candidates"]:
        checks, completeness=evidence_completeness(c)
        row={
            "id":c["id"],
            "architecture":c["architecture"],
            "display_name":c["display_name"],
            "target":c["target"],
            "doi":c.get("doi"),
            "pmid":c.get("pmid"),
            "metrics":c["metrics"],
            "advantages":c["advantages"],
            "risks":c["risks"],
            "risk_burden":risk_burden(c),
            "evidence_checks":checks,
            "evidence_completeness":round(completeness,4),
            "research_priority_score":research_priority(c),
            "score_semantics":"heuristic research priority; not safety, efficacy or field readiness",
            "validation_plan":falsification_plan(c)
        }
        rows.append(row)
    ranked=sorted(rows,key=lambda x:(-x["research_priority_score"],-x["evidence_completeness"],x["id"]))
    champion=ranked[0] if ranked else None
    report={
        "campaign_id":"MICROCLEAN-X",
        "phase":3,
        "name":"Composite Hunter",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "status":"PASS" if rows else "FAIL",
        "policy":reg["policy"],
        "candidate_count":len(rows),
        "ranked_candidates":ranked,
        "research_champion": {
            "id":champion["id"],
            "architecture":champion["architecture"],
            "reason":"highest current research-priority heuristic among direct-evidence candidates; requires falsification before any deployment claim"
        } if champion else None,
        "promoted_safe_or_field_ready":[],
        "interpretation":"Ranking selects what to test first. It does not certify safety, efficacy, scalability or field readiness."
    }
    report["sha256"]=_sha({k:v for k,v in report.items() if k not in {"generated_at","sha256"}})
    return report

def write(report):
    for d in (REPORT_DIR,PUBLIC_DIR,STATE_DIR):
        d.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    (REPORT_DIR/"composite_hunter_latest.json").write_text(payload,encoding="utf-8")
    (PUBLIC_DIR/"composite_hunter_latest.json").write_text(payload,encoding="utf-8")
    (STATE_DIR/"composite_hunter_latest.json").write_text(payload,encoding="utf-8")
    champion=report["research_champion"]
    lines=[
        "# MICROCLEAN-X Phase 3 — Composite Hunter",
        "",
        f"- Status: **{report['status']}**",
        f"- Exact architectures: **{report['candidate_count']}**",
        f"- Research champion: **{champion['architecture'] if champion else 'NONE'}**",
        f"- Safe/field-ready promotions: **{len(report['promoted_safe_or_field_ready'])}**",
        f"- Evidence fingerprint: `{report['sha256']}`",
        "",
        "## Ranked test queue",
        ""
    ]
    for i,x in enumerate(report["ranked_candidates"],1):
        lines.append(
            f"{i}. **{x['architecture']}** — priority {x['research_priority_score']}/100 — "
            f"evidence completeness {x['evidence_completeness']:.2f} — DOI {x['doi']}"
        )
    lines += [
        "",
        "> The priority number is not an efficacy or safety score. No candidate is declared field-ready.",
        ""
    ]
    (REPORT_DIR/"COMPOSITE-HUNTER-LATEST.md").write_text("\n".join(lines),encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--registry",default=str(REGISTRY))
    p.add_argument("--no-write",action="store_true")
    args=p.parse_args()
    report=build(load_registry(args.registry))
    if not args.no_write:
        write(report)
    print(json.dumps({
        "status":report["status"],
        "candidate_count":report["candidate_count"],
        "research_champion":report["research_champion"],
        "sha256":report["sha256"]
    },ensure_ascii=False))
    return 0 if report["status"]=="PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
