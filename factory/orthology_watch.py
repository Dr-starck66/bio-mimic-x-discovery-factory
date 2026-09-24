#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
FACTORY=ROOT/"factory"
STATE=ROOT/"state"/"factory"
PUBLIC=ROOT/"public"/"data"/"factory"
REPORTS=ROOT/"reports"/"factory"

sys.path.insert(0,str(FACTORY))
from human_bridge import build_human_bridges

TARGETS=FACTORY/"orthology_watch_targets.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path,default):
    path=Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path,obj):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

def stable_sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode("utf-8")).hexdigest()

def pending_targets():
    cfg=load(TARGETS,{"targets":[]})
    return [x for x in cfg.get("targets",[]) if x.get("enabled") and x.get("status")=="PENDING_STRICT"]

def evaluate_target(target,claim,bridge_result):
    species=target["species"]
    gene=target["gene"]
    expected_human=str(target.get("human_symbol") or gene).upper()
    bridges=[
        b for b in bridge_result.get("bridges",[])
        if b.get("animal_species")==species
        and str(b.get("animal_gene") or "").upper()==gene.upper()
        and str(b.get("human_symbol") or "").upper()==expected_human
        and b.get("translation_status")=="ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED"
        and b.get("clinical_efficacy_claim") is False
    ]
    providers=sorted({
        str((b.get("orthology") or {}).get("provider") or "unknown")
        for b in bridges
    })
    return {
        "species":species,
        "gene":gene,
        "human_symbol":target.get("human_symbol"),
        "human_ensembl_id":target.get("human_ensembl_id"),
        "genome_assemblies":target.get("genome_assemblies",[]),
        "claim_supported":bool(claim and claim.get("status")=="SUPPORTED"),
        "claim_pmids":list((claim or {}).get("pmid_sources",[])),
        "strict_bridge_count":len(bridges),
        "strict_providers":providers,
        "promotion_ready":bool(bridges),
        "status":"PROMOTION_READY" if bridges else "WATCHING",
        "promotion_rule":target.get("promotion_rule"),
        "bridges":bridges,
        "clinical_efficacy_claim":False
    }

def run_watch(persist=True):
    latest=load(STATE/"latest.json",{})
    claims={
        c.get("subject"):c
        for c in latest.get("claims",[])
        if c.get("status")=="SUPPORTED"
    }
    rows=[]
    for target in pending_targets():
        species=target["species"]
        claim=claims.get(species)
        if not claim:
            rows.append({
                "species":species,
                "gene":target["gene"],
                "status":"NO_SUPPORTED_CLAIM",
                "promotion_ready":False,
                "clinical_efficacy_claim":False
            })
            continue

        candidate=copy.deepcopy(claim)
        # The Human Bridge reads literature seeds by species name, so we preserve
        # the real supported claim and let the same strict provider chain decide.
        bridge_result=build_human_bridges([candidate],max_candidates=1,max_genes=12)
        row=evaluate_target(target,claim,bridge_result)
        row["provider_status"]=bridge_result.get("provider_status",{})
        row["candidate_status"]=bridge_result.get("candidate_status",[])
        row["errors"]=bridge_result.get("errors",[])
        rows.append(row)

    out={
        "schema":"biomimic-orthology-watch-v1",
        "time":now(),
        "targets":rows,
        "pending_targets":len(rows),
        "promotion_ready_targets":sum(1 for r in rows if r.get("promotion_ready")),
        "status":"PROMOTION_READY" if any(r.get("promotion_ready") for r in rows) else ("WATCHING" if rows else "IDLE"),
        "clinical_efficacy_claim":False
    }
    out["sha256"]=stable_sha(out)

    if persist:
        save(STATE/"orthology_watch_latest.json",out)
        save(PUBLIC/"orthology_watch_latest.json",out)
        lines=[
            "# BIO-MIMIC X Orthology Watch — Latest",
            "",
            f"Time: {out['time']}",
            f"Status: {out['status']}",
            f"Pending targets: {out['pending_targets']}",
            f"Promotion-ready targets: {out['promotion_ready_targets']}",
            ""
        ]
        for r in rows:
            lines += [
                f"## {r.get('species')} → {r.get('gene')}",
                f"- Status: {r.get('status')}",
                f"- Strict bridge count: {r.get('strict_bridge_count',0)}",
                f"- Providers: {', '.join(r.get('strict_providers',[])) or 'none'}",
                f"- Genome assemblies watched: {', '.join(r.get('genome_assemblies',[])) or 'none'}",
                f"- Clinical efficacy claim: {r.get('clinical_efficacy_claim')}",
                ""
            ]
        REPORTS.mkdir(parents=True,exist_ok=True)
        (REPORTS/"ORTHOLOGY-WATCH-LATEST.md").write_text("\n".join(lines),encoding="utf-8")
    return out

if __name__=="__main__":
    out=run_watch(persist=True)
    print(json.dumps({
        "status":out["status"],
        "pending_targets":out["pending_targets"],
        "promotion_ready_targets":out["promotion_ready_targets"],
        "sha256":out["sha256"]
    }))
