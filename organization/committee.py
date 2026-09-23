#!/usr/bin/env python3
from __future__ import annotations
import json, math, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
LABS=json.loads((ROOT/"organization"/"labs.json").read_text(encoding="utf-8"))
OUT=ROOT/"organization"/"output"/"labs"
STATE=ROOT/"state"/"org"
REPORTS=ROOT/"reports"/"org"
PUBLIC=ROOT/"public"/"data"/"org"
for p in [STATE,REPORTS,PUBLIC]: p.mkdir(parents=True,exist_ok=True)

def now(): return datetime.now(timezone.utc).isoformat()
def load(path,default):
    if path.exists():
        try:return json.loads(path.read_text(encoding="utf-8"))
        except Exception:return default
    return default
def save(path,obj):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

def merge_outputs():
    outputs=[]
    for p in sorted(OUT.glob("*.json")):
        try: outputs.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception: pass
    return outputs

def candidate_key(name): return " ".join((name or "").lower().split())

def cross_lab_portfolio(outputs):
    bucket=defaultdict(lambda:{
        "name":None,"labs":set(),"sources":set(),"mechanisms":set(),"genes":set(),
        "arbiter_scores":[],"priorities":[],"challenges":set(),"annotation_support":False,
        "taxon_verified":False,"taxon_proofs":[]
    })
    for o in outputs:
        for c in o.get("candidates",[]):
            if not c.get("taxon_verified"):
                continue
            k=candidate_key(c["name"]); b=bucket[k]; b["name"]=c["name"]; b["labs"].add(o["lab_id"])
            b["sources"].update(c.get("sources",[])); b["mechanisms"].update(c.get("mechanisms",[]))
            b["genes"].update(c.get("genes",[])); b["arbiter_scores"].append(c.get("arbiter",0))
            b["priorities"].append(c.get("priority",0)); b["challenges"].update(c.get("challenge_flags",[]))
            b["annotation_support"]=b["annotation_support"] or bool(c.get("annotation_support"))
            if c.get("taxon_verified"):
                b["taxon_verified"]=True
                if c.get("taxon_proof"): b["taxon_proofs"].append(c["taxon_proof"])
    out=[]
    for b in bucket.values():
        lab_count=len(b["labs"])
        source_count=len(b["sources"])
        pmid_sources=sorted(s for s in b["sources"] if str(s).startswith("PMID:"))
        independent_source_count=len(pmid_sources)
        mean_arb=sum(b["arbiter_scores"])/max(1,len(b["arbiter_scores"]))
        convergence=min(100,lab_count*28)
        provenance=min(100,source_count*10)
        mechanism=min(100,len(b["mechanisms"])*22)
        challenge_penalty=min(30,len(b["challenges"])*2.0)
        taxonomy_bonus=15 if b["taxon_verified"] else 5 if b["annotation_support"] else 0
        committee=max(0,round(mean_arb*0.36+convergence*0.22+provenance*0.18+mechanism*0.12+taxonomy_bonus-challenge_penalty*0.10))
        out.append({
            "name":b["name"],"labs":sorted(b["labs"]),"lab_count":lab_count,
            "sources":sorted(b["sources"]),"source_count":source_count,
            "pmid_sources":pmid_sources,"independent_source_count":independent_source_count,
            "mechanisms":sorted(b["mechanisms"]),"genes":sorted(b["genes"])[:30],
            "mean_arbiter":round(mean_arb,2),"annotation_support":b["annotation_support"],
            "taxon_verified":b["taxon_verified"],"taxon_proofs":b["taxon_proofs"][:3],
            "committee_score":committee,"challenges":sorted(b["challenges"])
        })
    out.sort(key=lambda x:(-x["committee_score"],-x["lab_count"],-x["source_count"]))
    return out

def allocate_credits(portfolio,total=100):
    elig=[x for x in portfolio[:15] if x["committee_score"]>0]
    weight=sum(x["committee_score"] for x in elig) or 1
    raw=[(x,x["committee_score"]/weight*total) for x in elig]
    alloc=[]; used=0
    for i,(x,v) in enumerate(raw):
        c=round(v)
        if i==len(raw)-1: c=max(0,total-used)
        used+=c
        alloc.append({"name":x["name"],"research_credits":c,"committee_score":x["committee_score"],"labs":x["labs"]})
    return alloc

def challenge_matrix(outputs):
    lab_ids=[o["lab_id"] for o in outputs]
    pairs=[]
    for i,lab in enumerate(lab_ids):
        if not lab_ids: break
        challenger=lab_ids[(i+1)%len(lab_ids)]
        if challenger==lab and len(lab_ids)>1: challenger=lab_ids[(i+2)%len(lab_ids)]
        pairs.append({
            "proponent_lab":lab,
            "challenger_lab":challenger,
            "challenge":"Re-audit the top hypothesis using the challenger lab's confounders and require at least one falsifiable counter-test."
        })
    return pairs

def main():
    outputs=merge_outputs()
    if not outputs:
        raise SystemExit("No lab outputs found.")
    memory=load(STATE/"organization_memory.json",{"runs":0,"committee_history":[],"lab_performance":{}})
    portfolio=cross_lab_portfolio(outputs)
    credits=allocate_credits(portfolio,100)
    challenges=challenge_matrix(outputs)

    for o in outputs:
        perf=memory["lab_performance"].setdefault(o["lab_id"],{"runs":0,"success":0,"mean_candidates":0.0})
        perf["runs"]+=1
        if o.get("status")=="PASS": perf["success"]+=1
        perf["mean_candidates"]=round((perf["mean_candidates"]*(perf["runs"]-1)+o.get("candidate_count",0))/perf["runs"],3)

    org_run={
        "schema":"biomimic-v6-org-run-v1","time":now(),
        "labs":[{"id":o["lab_id"],"name":o["lab_name"],"status":o["status"],"paper_count":o["paper_count"],"candidate_count":o["candidate_count"],"sha256":o["sha256"]} for o in outputs],
        "portfolio":portfolio[:50],"allocations":credits,"cross_lab_challenges":challenges,
        "committee_rules":{
            "hard_gate":"exact GBIF-verified Animalia taxon required",
            "score_components":["mean arbiter","cross-lab convergence","provenance","mechanism density","taxonomy proof","challenge penalty"],
            "research_credits":"internal prioritization units, not currency"
        }
    }
    org_run["sha256"]=hashlib.sha256(json.dumps(org_run,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

    memory["runs"]+=1
    memory["committee_history"].insert(0,{
        "time":org_run["time"],"sha256":org_run["sha256"],
        "top":[{"name":x["name"],"score":x["committee_score"]} for x in portfolio[:10]]
    })
    memory["committee_history"]=memory["committee_history"][:365]

    save(STATE/"latest.json",org_run)
    save(STATE/"organization_memory.json",memory)
    save(PUBLIC/"latest.json",org_run)
    save(PUBLIC/"memory.json",memory)

    lines=[
        f"# BIO-MIMIC X V6 Scientific Investment Committee — {org_run['time']}",
        "",
        f"**Organization replay SHA-256:** `{org_run['sha256']}`",
        "",
        "## Laboratory status",
    ]
    for x in org_run["labs"]:
        lines.append(f"- {x['name']}: {x['status']} · {x['paper_count']} papers · {x['candidate_count']} candidates")
    lines += ["","## Top portfolio"]
    for x in portfolio[:15]:
        lines += [
            f"### {x['name']} — Committee {x['committee_score']}/100",
            f"- Labs: {', '.join(x['labs'])}",
            f"- Sources: {x['source_count']} · mechanisms: {', '.join(x['mechanisms'][:8]) or 'none extracted'}",
            f"- Challenge flags: {', '.join(x['challenges'][:6])}",
            ""
        ]
    lines += ["## Research-credit allocation"]
    for x in credits:
        lines.append(f"- {x['name']}: {x['research_credits']} credits")
    lines += ["","## Cross-lab challenge plan"]
    for x in challenges:
        lines.append(f"- {x['challenger_lab']} challenges {x['proponent_lab']}: {x['challenge']}")
    (REPORTS/"LATEST.md").write_text("\n".join(lines),encoding="utf-8")
    (REPORTS/(org_run["time"][:10]+".md")).write_text("\n".join(lines),encoding="utf-8")

    print(json.dumps({
        "status":"PASS","labs":len(outputs),"portfolio":len(portfolio),
        "allocations":len(credits),"sha256":org_run["sha256"]
    }))
if __name__=="__main__": main()
