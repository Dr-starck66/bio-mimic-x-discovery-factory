#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, re, hashlib, urllib.parse, urllib.request, time
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
LABS=json.loads((ROOT/"organization"/"labs.json").read_text(encoding="utf-8"))
EPMC="https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EPMC_ANN="https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds"
GBIF_MATCH="https://api.gbif.org/v1/species/match"
TIMEOUT=18

GENUS_STOP={"Cancer","Nature","Human","Novel","Clinical","Current","Comparative","Natural","European","American","Medical","Science","Biology","Molecular","Cellular","Genomic","Genome","Protein","Disease","Research","Journal","Effects","Evidence","Target","System","Animal","Animals","Study","Studies","Long","High","Low","Open","Results","Review","Reviews","Methods","This","These","Those","Emerging","Recent","Previous","Future","Our","Their","Such","Further","Growing","Available","Several","Many","New","Scientific","Experimental","Wound"}
EPITHET_STOP={"review","reviews","study","studies","findings","evidence","narrative","results","research","data","work","analysis","report","reports","article","articles","approach","approaches","method","methods","model","models","system","systems","process","processes","response","responses","effect","effects","role","roles","mechanism","mechanisms","therapy","treatment","healing"}
GENE_STOP={"DNA","RNA","ATP","NAD","ROS","ACE","MRI","PET","COVID","SARS","HIV","USA","PCR","ELISA","WT","KO","HR","CI","OR","AND","THE","AGE","LONG","BMI","AUC","ALT","AST","LAB","MEDLINE","ECM","IR","OS","ON","MC","GT","AD","DM","FD","HI","CPS","CVD","CRC"}
TAX_CACHE={}

def now(): return datetime.now(timezone.utc).isoformat()
def norm(x): return re.sub(r"\s+"," ",(x or "").lower()).strip()

def get_json(url,retries=2):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"BIO-MIMIC-X-V6/1.0"})
            with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last=e
            if i<retries-1: time.sleep(0.6*(i+1))
    raise last

def latin_mentions(text):
    out=[]
    for m in re.finditer(r"\b([A-Z][a-z]{2,})\s([a-z][a-z-]{2,})\b", text or ""):
        genus,epithet=m.group(1),m.group(2)
        if genus in GENUS_STOP or norm(epithet) in EPITHET_STOP:
            continue
        x=f"{genus} {epithet}"
        if x not in out: out.append(x)
    return out

def genes(text):
    vals=re.findall(r"\b[A-Z][A-Z0-9-]{1,8}\b",text or "")
    out=[]
    for x in vals:
        if x not in GENE_STOP and not x[0].isdigit() and x not in out: out.append(x)
    return out[:20]

def source_id(p):
    if p.get("pmid"): return "PMID:"+str(p["pmid"])
    if p.get("pmcid"): return "PMC:"+str(p["pmcid"])
    return f"{p.get('source','MED')}:{p.get('id','unknown')}"

def annotation_species(p):
    aid=f"{p.get('source','MED')}:{p.get('id') or p.get('pmid') or ''}"
    if aid.endswith(":"): return set()
    u=EPMC_ANN+"?"+urllib.parse.urlencode({"articleIds":aid,"format":"JSON","pageSize":"300"})
    try: data=get_json(u,1)
    except Exception: return set()
    txt=json.dumps(data,ensure_ascii=False)
    exact=re.findall(r'"exact"\s*:\s*"([^"]{3,120})"',txt)
    out=set()
    for x in exact:
        out.update(norm(v) for v in latin_mentions(x))
    return out

def validate_gbif_match(name):
    """Fail-closed taxonomy gate: exact Animalia species/subspecies only."""
    key=norm(name)
    if key in TAX_CACHE: return TAX_CACHE[key]
    try:
        data=get_json(GBIF_MATCH+"?"+urllib.parse.urlencode({"name":name,"verbose":"true"}),1)
    except Exception:
        TAX_CACHE[key]=None
        return None
    canonical=data.get("canonicalName") or data.get("scientificName") or ""
    rank=(data.get("rank") or "").upper()
    kingdom=(data.get("kingdom") or "").lower()
    match=(data.get("matchType") or "").upper()
    status=(data.get("status") or "").upper()
    ok=(match=="EXACT" and kingdom=="animalia" and rank in {"SPECIES","SUBSPECIES","INFRASPECIFIC_NAME"}
        and norm(" ".join(canonical.split()[:2]))==key and status not in {"DOUBTFUL","MISAPPLIED"})
    proof=None
    if ok:
        proof={"provider":"GBIF","taxon_key":data.get("usageKey") or data.get("speciesKey") or data.get("key"),
               "canonical_name":canonical,"rank":rank,"kingdom":data.get("kingdom"),
               "status":data.get("status"),"match_type":match}
    TAX_CACHE[key]=proof
    return proof

def evidence_score(c):
    return min(100, round(
        12 + min(35,c["paper_count"]*8) + min(18,math.log10(1+c["citations"])*7)
        + min(20,len(c["mechanisms"])*6) + (15 if c["annotation_support"] else 0)
    ))

def skeptic_score(c):
    s=88
    if c["paper_count"]<2:s-=24
    if not c["annotation_support"]:s-=18
    if not c["mechanisms"]:s-=16
    if not c["genes"]:s-=8
    if c["citations"]<5:s-=8
    return max(0,s)

def challenge_flags(lab,c):
    flags=list(lab["challenge_focus"])
    if c["paper_count"]<2: flags.append("single-paper dependence")
    if not c["annotation_support"]: flags.append("taxonomy not annotation-supported")
    if not c["mechanisms"]: flags.append("phenotype without extracted mechanism")
    if not c["genes"]: flags.append("no gene symbol candidate")
    flags += ["correlation does not prove causation","human functional divergence remains possible"]
    return flags

def run_lab(lab_id,out_path):
    lab=next(x for x in LABS if x["id"]==lab_id)
    params={"format":"json","resultType":"core","pageSize":"35","query":lab["query"]}
    status="PASS"; failures=[]
    try:
        data=get_json(EPMC+"?"+urllib.parse.urlencode(params))
        papers=data.get("resultList",{}).get("result",[])
    except Exception as e:
        papers=[]; status="FAIL"; failures.append(str(e))

    buckets={}
    focus=[norm(x) for x in lab["mechanism_focus"]]
    for idx,p in enumerate(papers):
        text=(p.get("title") or "")+" "+(p.get("abstractText") or "")
        h=norm(text)
        mechs=[m for m in lab["mechanism_focus"] if norm(m) in h]
        gs=genes(text)
        anns=annotation_species(p) if idx<5 else set()
        for sp in latin_mentions(text):
            key=norm(sp)
            b=buckets.setdefault(key,{"name":sp,"sources":set(),"mechanisms":set(),"genes":set(),"citations":0,"annotation_support":False})
            b["sources"].add(source_id(p)); b["mechanisms"].update(mechs); b["genes"].update(gs)
            b["citations"] += int(p.get("citedByCount") or 0)
            if key in anns: b["annotation_support"]=True

    raw=sorted(buckets.values(),key=lambda b:(-int(b["annotation_support"]),-len(b["sources"]),-b["citations"]))
    rejected=[]; candidates=[]
    for b in raw[:40]:
        tax=validate_gbif_match(b["name"])
        taxon_verified=bool(tax)
        if not taxon_verified:
            rejected.append({"name":b["name"],"reason":"not an exact GBIF-verified Animalia taxon","annotation_support":b["annotation_support"]})
            continue
        c={
            "name":b["name"],"paper_count":len(b["sources"]),"sources":sorted(b["sources"]),
            "mechanisms":sorted(b["mechanisms"]),"genes":sorted(b["genes"])[:20],
            "citations":b["citations"],"annotation_support":b["annotation_support"],
            "taxon_verified":taxon_verified,"taxon_proof":tax
        }
        c["evidence"]=evidence_score(c)
        c["skeptic"]=skeptic_score(c)
        c["disagreement"]=abs(c["evidence"]-c["skeptic"])
        c["arbiter"]=max(0,round((c["evidence"]+c["skeptic"])/2-c["disagreement"]*0.25))
        c["challenge_flags"]=challenge_flags(lab,c)
        c["priority"]=round(
            c["arbiter"]*0.55 + min(100,c["paper_count"]*15)*0.20 +
            min(100,len(c["mechanisms"])*25)*0.15 + min(100,len(c["genes"])*8)*0.10
        )
        candidates.append(c)
    candidates.sort(key=lambda x:(-x["priority"],-x["arbiter"],-x["paper_count"]))

    top=candidates[:20]
    result={
        "schema":"biomimic-v6-lab-output-v1",
        "lab_id":lab["id"],"lab_name":lab["name"],"mission":lab["mission"],
        "human_domain":lab["human_domain"],"started_at":now(),"status":status,
        "paper_count":len(papers),"raw_candidate_count":len(buckets),
        "candidate_count":len(candidates),"rejected_candidate_count":len(rejected),
        "rejected_samples":rejected[:12],"candidates":top,"failures":failures
    }
    result["sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    out=Path(out_path); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":status,"lab":lab_id,"papers":len(papers),"raw_candidates":len(buckets),"verified_candidates":len(candidates),"rejected":len(rejected),"sha256":result["sha256"]}))
    return 0 if status=="PASS" else 2

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--lab",required=True,choices=[x["id"] for x in LABS])
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    run_lab(a.lab,a.out)
    # Provider failure is encoded inside the artifact. The process stays alive so the
    # committee can account for a failed lab instead of silently losing its evidence.
    raise SystemExit(0)
