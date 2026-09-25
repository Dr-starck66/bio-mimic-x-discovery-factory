#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"factory"))
from human_bridge import build_human_bridges
from translation_paths import build_translation_paths

STATE=ROOT/"state"/"factory"/"latest.json"
PUBLIC=ROOT/"public"/"data"/"factory"/"latest.json"
REPORT=ROOT/"reports"/"factory"/"HUMAN-BRIDGE-LATEST.md"

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

STRICT_PROVIDERS={
    "NCBI Ortholog",
    "OMA",
    "OrthoDB v12",
    "Peer-reviewed phylogenetic orthology",
    "Peer-reviewed functional orthology",
    "Peer-reviewed direct orthology",
}

def _parse_time(x):
    if not x:
        return None
    try:
        return datetime.fromisoformat(str(x).replace("Z","+00:00"))
    except Exception:
        return None

def retain_last_known_good_strict(cycle,result,claims,max_misses=2,max_age_days=7):
    """Prevent one transient provider outage from deleting a previously verified bridge."""
    previous=cycle.get("human_bridge_result") or {}
    previous_bridges=previous.get("bridges") or []
    if not previous_bridges:
        result["live_bridged_candidates"]=result.get("bridged_candidates",0)
        result["cached_bridged_candidates"]=0
        return result

    claim_names={x.get("subject") for x in claims}
    live_names={b.get("animal_species") for b in result.get("bridges",[])}
    previous_time=_parse_time((cycle.get("bridge_refresh") or {}).get("time"))
    now_dt=datetime.now(timezone.utc)

    by_subject={}
    for b in previous_bridges:
        if b.get("animal_species") not in claim_names:
            continue
        if b.get("translation_status")!="ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED":
            continue
        provider=(b.get("orthology") or {}).get("provider")
        # Older Ensembl bridges do not carry an explicit provider field.
        if not provider and b.get("animal_ensembl_species"):
            provider="Ensembl Compara"
        if provider not in STRICT_PROVIDERS and provider!="Ensembl Compara":
            continue
        by_subject.setdefault(b.get("animal_species"),[]).append(b)

    cached=[]
    cached_subjects=set()
    for subject,bridges in by_subject.items():
        if subject in live_names:
            continue
        valid=[]
        for old in bridges:
            prior_misses=int(old.get("cache_miss_count") or 0)
            if prior_misses>=max_misses:
                continue
            last_live=_parse_time(old.get("last_live_verified_at")) or previous_time
            if not last_live:
                continue
            age=(now_dt-last_live).total_seconds()
            if age<0 or age>max_age_days*86400:
                continue
            b=copy.deepcopy(old)
            b["verification_mode"]="LAST_KNOWN_GOOD_CACHE"
            b["last_live_verified_at"]=last_live.isoformat()
            b["cache_miss_count"]=prior_misses+1
            b["cache_reason"]="Current live providers did not reproduce this previously verified strict bridge; retained temporarily pending revalidation."
            valid.append(b)
        if valid:
            cached.extend(valid)
            cached_subjects.add(subject)

    result["live_bridged_candidates"]=len(live_names)
    result.setdefault("bridges",[]).extend(cached)

    # De-duplicate after merging current and cached evidence.
    uniq={}
    for b in result.get("bridges",[]):
        key=(b.get("animal_species"),b.get("animal_gene"),b.get("human_ensembl_id"),(b.get("orthology") or {}).get("provider"))
        uniq[key]=b
    result["bridges"]=list(uniq.values())

    final_names={b.get("animal_species") for b in result["bridges"] if b.get("animal_species")}
    result["cached_bridged_candidates"]=len(cached_subjects)
    result["cached_subjects"]=sorted(cached_subjects)
    result["bridged_candidates"]=len(final_names)
    result["coverage_ratio"]=round(len(final_names)/max(1,result.get("attempted_candidates",len(claims))),4)
    result.setdefault("provider_status",{})["Last-known-good cache"]="PASS" if cached_subjects else "IDLE"

    for row in result.get("candidate_status",[]):
        subject=row.get("candidate")
        if subject in cached_subjects and subject not in live_names:
            row["status"]="BRIDGED_CACHED"
            row["bridges"]=sum(1 for b in result["bridges"] if b.get("animal_species")==subject)
            row["cache_miss_count"]=max((b.get("cache_miss_count",0) for b in result["bridges"] if b.get("animal_species")==subject),default=0)
    return result

def main():
    cycle=json.loads(STATE.read_text(encoding="utf-8"))
    claims=[x for x in cycle.get("claims",[]) if x.get("status")=="SUPPORTED"]
    previous_sha=cycle.get("sha256")

    result=build_human_bridges(claims)
    result=retain_last_known_good_strict(cycle,result,claims)
    translation=build_translation_paths(claims,result)
    by_subject={}
    for b in result.get("bridges",[]):
        by_subject.setdefault(b["animal_species"],[]).append(b)

    path_by_subject={x["subject"]:x for x in translation.get("paths",[])}
    human=[]
    for claim in claims:
        subject=claim["subject"]
        hits=by_subject.get(subject,[])
        path=path_by_subject.get(subject)
        if hits:
            status="ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED"
        elif path and path.get("status")=="VERIFIED":
            status="HUMAN_TRANSLATION_PATH_VERIFIED"
        else:
            status="UNVERIFIED_HUMAN_BRIDGE"
        human.append({
            "subject":subject,
            "status":status,
            "bridges":hits,
            "translation_path":path,
            "claim_pmids":claim.get("pmid_sources",[]),
            "animal_claim_not_promoted_to_human_efficacy":True,
            "remaining":[] if status!="UNVERIFIED_HUMAN_BRIDGE" else [
                "provider-verified orthology or a separately typed evidence-backed translation path"
            ]
        })

    cycle["human_bridge_result"]=result
    cycle["human_translation_result"]=translation
    cycle["human_translation"]=human
    cycle["bridge_refresh"]={
        "time":now(),
        "previous_cycle_sha256":previous_sha,
        "supported_claims":len(claims),
        "strict_orthology_candidates":result.get("bridged_candidates",0),
        "strict_orthology_coverage_ratio":result.get("coverage_ratio",0),
        "translation_verified_candidates":translation.get("translation_verified_candidates",0),
        "translation_coverage_ratio":translation.get("translation_coverage_ratio",0),
        "status":translation.get("status","PARTIAL")
    }

    for e in cycle.get("brick_usage",[]):
        if e.get("brick_id")=="human-bridge":
            e["time"]=cycle["bridge_refresh"]["time"]
            e["output_ref"]="human_translation_result"
            e["metric"]="verified_human_translation_coverage"
            e["value"]=translation.get("translation_coverage_ratio",0)
            e["status"]=translation.get("status","PARTIAL")

    payload=copy.deepcopy(cycle)
    payload.pop("sha256",None)
    cycle["sha256"]=hashlib.sha256(
        json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()
    ).hexdigest()

    save(STATE,cycle)
    save(PUBLIC,cycle)

    lines=[
        "# BIO-MIMIC X — Human Bridge Refresh",
        "",
        f"Time: {cycle['bridge_refresh']['time']}",
        f"Supported claims: {len(claims)}",
        f"Strict orthology: {result.get('bridged_candidates',0)}/{len(claims)} ({result.get('coverage_ratio',0):.1%})",
        f"Verified human translation: {translation.get('translation_verified_candidates',0)}/{len(claims)} ({translation.get('translation_coverage_ratio',0):.1%})",
        f"Translation status: {translation.get('status','PARTIAL')}",
        "",
        "## Translation status"
    ]
    for row in translation.get("candidate_status",[]):
        lines.append(
            f"- {row.get('candidate')}: {row.get('status')} · {row.get('path_type') or 'none'}"
        )
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")

    print(json.dumps({
        "status":translation.get("status"),
        "supported_claims":len(claims),
        "strict_orthology_candidates":result.get("bridged_candidates",0),
        "strict_orthology_coverage_ratio":result.get("coverage_ratio",0),
        "translation_verified_candidates":translation.get("translation_verified_candidates",0),
        "translation_coverage_ratio":translation.get("translation_coverage_ratio",0),
        "path_type_counts":translation.get("path_type_counts",{}),
        "sha256":cycle["sha256"]
    }))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
