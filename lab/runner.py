#!/usr/bin/env python3
"""
BIO-MIMIC X V5 — Autonomous Comparative Medicine Lab
Zero mandatory API keys. Python stdlib only.

Daily loop:
OBSERVE -> DISCOVER -> VERIFY -> GRAPH -> DUALITY -> MORPHEUS
-> LEARN -> REPLAY -> REPORT

"Self-improving" here means the research policy and knowledge state change
from measured outcomes. The program does NOT autonomously rewrite its own code.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
import hashlib
import random
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
REPORTS = ROOT / "reports"
PUBLIC = ROOT / "public" / "data"
DATA = ROOT / "data"
TRACKS_PATH = ROOT / "lab" / "tracks.json"

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EPMC_ANN = "https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds"
ENSEMBL_SPECIES = "https://rest.ensembl.org/info/species?content-type=application/json"

STATE.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)
PUBLIC.mkdir(parents=True, exist_ok=True)

MAX_TRACKS_PER_RUN = int(os.environ.get("BIOMIMIC_TRACKS_PER_RUN", "4"))
PAPERS_PER_TRACK = int(os.environ.get("BIOMIMIC_PAPERS_PER_TRACK", "30"))
TIMEOUT = int(os.environ.get("BIOMIMIC_HTTP_TIMEOUT", "20"))

MECH = [
    "DNA repair","genome maintenance","apoptosis","p53","hyaluronan",
    "inflammation","fibrosis","regeneration","stem cell","Wnt",
    "metabolic suppression","mitochondria","hypoxia","oxidative stress",
    "immune","interferon","extracellular matrix","senescence","telomere",
    "angiogenesis","autophagy","proteostasis","heat shock","antioxidant",
    "cryoprotectant","neuroprotection","thrombosis","coagulation",
    "ion channel","GLP-1","ACE inhibition","circadian","antimicrobial peptide"
]
GENE_STOP = {
    "DNA","RNA","ATP","NAD","ROS","ACE","MRI","PET","COVID","SARS","HIV",
    "USA","PCR","ELISA","WT","KO","HR","CI","OR","AND","THE","AGE","LONG"
}
GENUS_STOP = {
    "Cancer","Nature","Human","Novel","Clinical","Current","Comparative",
    "Natural","European","American","Medical","Science","Biology","Molecular",
    "Cellular","Genomic","Genome","Protein","Disease","Research","Journal",
    "Effects","Evidence","Target","System","Animal","Animals","Study","Studies",
    "Long","High","Low","Open","Results","Review","Reviews","Methods"
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def save(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)

def get_json(url, headers=None, retries=2):
    hdr = {"User-Agent":"BIO-MIMIC-X/5.0 autonomous-research-lab"}
    if headers:
        hdr.update(headers)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            if attempt < retries - 1:
                time.sleep(0.8 * (attempt + 1))
    raise last

def norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()

def latin_mentions(text):
    out = []
    for m in re.finditer(r"\b([A-Z][a-z]{2,})\s([a-z][a-z-]{2,})\b", text or ""):
        genus, species = m.group(1), m.group(2)
        if genus not in GENUS_STOP:
            x = f"{genus} {species}"
            if x not in out:
                out.append(x)
    return out

def mechanisms(text):
    h = norm(text)
    return [m for m in MECH if norm(m) in h]

def genes(text):
    vals = re.findall(r"\b[A-Z][A-Z0-9-]{1,8}\b", text or "")
    out = []
    for x in vals:
        if x not in GENE_STOP and not x[0].isdigit() and x not in out:
            out.append(x)
    return out[:25]

def paper_id(p):
    if p.get("pmid"):
        return f"PMID:{p['pmid']}"
    if p.get("pmcid"):
        return f"PMC:{p['pmcid']}"
    return f"{p.get('source','MED')}:{p.get('id','unknown')}"

def load_known_species():
    kb = load(DATA / "knowledge-base.json", {})
    names = set()
    for s in kb.get("species", []):
        names.add(norm(s.get("name","")))
        names.add(norm(s.get("latin","")))
    return names

def is_known_species(name, known):
    n = norm(name)
    if n in known:
        return True
    return any(n in x or x in n for x in known if len(x) > 5)

def init_learning(tracks):
    data = load(STATE/"learning.json", {})
    data.setdefault("total_runs", 0)
    data.setdefault("tracks", {})
    data.setdefault("term_weights", {})
    for t in tracks:
        data["tracks"].setdefault(t["id"], {
            "runs":0, "reward_ema":0.0, "novelty_ema":0.0,
            "evidence_ema":0.0, "last_run":None
        })
        for term in t.get("seed_terms", []):
            data["term_weights"].setdefault(term, 1.0)
    return data

def ucb_score(stats, total_runs):
    n = stats["runs"]
    if n == 0:
        return 999.0
    exploit = stats["reward_ema"]
    explore = math.sqrt(2.0 * math.log(max(2,total_runs+1)) / n)
    return exploit + explore

def choose_tracks(tracks, learning, count):
    ranked = []
    for t in tracks:
        s = learning["tracks"][t["id"]]
        ranked.append((ucb_score(s, learning["total_runs"]), t))
    ranked.sort(key=lambda x: x[0], reverse=True)
    # Deterministic-ish daily diversity: top UCB plus one underexplored track.
    chosen = [t for _,t in ranked[:max(1,count-1)]]
    under = sorted(tracks, key=lambda t: learning["tracks"][t["id"]]["runs"])
    for t in under:
        if t not in chosen and len(chosen) < count:
            chosen.append(t)
    return chosen[:count]

def query_track(track, learning):
    boosted = sorted(
        track.get("seed_terms", []),
        key=lambda x: learning["term_weights"].get(x,1.0),
        reverse=True
    )[:3]
    q = track["query"]
    if boosted:
        q += " AND (" + " OR ".join(boosted) + ")"
    params = {
        "format":"json",
        "resultType":"core",
        "pageSize":str(PAPERS_PER_TRACK),
        "query":q
    }
    return get_json(EPMC + "?" + urllib.parse.urlencode(params))

def species_annotation_support(p):
    art_id = f"{p.get('source','MED')}:{p.get('id') or p.get('pmid') or ''}"
    if art_id.endswith(":"):
        return set()
    params = {
        "articleIds": art_id,
        "format":"JSON",
        "pageSize":"400"
    }
    try:
        data = get_json(EPMC_ANN + "?" + urllib.parse.urlencode(params), retries=1)
    except Exception:
        return set()
    txt = json.dumps(data, ensure_ascii=False)
    exact = re.findall(r'"exact"\s*:\s*"([^"]{3,120})"', txt)
    out = set()
    for x in exact:
        for lat in latin_mentions(x):
            out.add(norm(lat))
    return out

def verify_ensembl_species(candidate_names):
    try:
        species = get_json(ENSEMBL_SPECIES, headers={"Accept":"application/json"}, retries=1).get("species",[])
    except Exception:
        return {}
    index = {}
    for s in species:
        for key in [s.get("display_name",""), (s.get("name","") or "").replace("_"," ")]:
            if key:
                index[norm(key)] = s.get("name")
    out = {}
    for name in candidate_names:
        n = norm(name)
        if n in index:
            out[name] = index[n]
    return out

def graph_add_node(graph, node_id, ntype, label, attrs=None):
    graph["nodes"].setdefault(node_id, {"id":node_id,"type":ntype,"label":label,"attrs":attrs or {}})
    if attrs:
        graph["nodes"][node_id]["attrs"].update(attrs)

def graph_add_edge(graph, src, dst, relation, source, score=1.0):
    key = hashlib.sha1(f"{src}|{relation}|{dst}|{source}".encode()).hexdigest()[:16]
    graph["edges"][key] = {
        "id":key, "source":src, "target":dst, "relation":relation,
        "provenance":source, "score":round(float(score),4)
    }

def evaluator_evidence(c):
    return min(100, round(
        10 + min(35,c["paper_count"]*8) +
        min(15,math.log10(1+c["citations"])*6) +
        min(15,len(c["mechanisms"])*5) +
        (15 if c["annotation_support"] else 0) +
        (10 if c["ensembl_verified"] else 0)
    ))

def evaluator_skeptic(c):
    s = 85
    if c["paper_count"] < 2: s -= 22
    if not c["annotation_support"]: s -= 18
    if not c["ensembl_verified"]: s -= 12
    if not c["mechanisms"]: s -= 15
    if not c["genes"]: s -= 8
    if c["citations"] < 5: s -= 8
    return max(0,s)

def morpheus_flags(c):
    flags = []
    if c["paper_count"] < 2: flags.append("single-paper dependence")
    if not c["annotation_support"]: flags.append("taxon not annotation-supported")
    if not c["ensembl_verified"]: flags.append("taxon not Ensembl-verified")
    if not c["mechanisms"]: flags.append("phenotype without extracted mechanism")
    if not c["genes"]: flags.append("no gene symbol candidate")
    if c["citations"] < 5: flags.append("weak citation signal")
    flags += [
        "phylogeny confound must be tested",
        "correlation does not establish causality",
        "human functional divergence remains possible"
    ]
    return flags

def update_learning(learning, track, metrics):
    s = learning["tracks"][track["id"]]
    alpha = 0.30
    reward = (
        0.40 * min(1.0, metrics["novel_species"]/4.0) +
        0.25 * min(1.0, metrics["verified_species"]/3.0) +
        0.20 * min(1.0, metrics["mechanism_density"]/4.0) +
        0.15 * min(1.0, metrics["source_diversity"]/8.0)
    )
    s["runs"] += 1
    s["reward_ema"] = round((1-alpha)*s["reward_ema"] + alpha*reward, 6)
    s["novelty_ema"] = round((1-alpha)*s["novelty_ema"] + alpha*metrics["novel_species"], 6)
    s["evidence_ema"] = round((1-alpha)*s["evidence_ema"] + alpha*metrics["verified_species"], 6)
    s["last_run"] = now_iso()
    for term in track.get("seed_terms", []):
        old = learning["term_weights"].get(term, 1.0)
        signal = 0.92 + reward * 0.22
        learning["term_weights"][term] = round(max(0.25,min(3.0,old*signal)),6)
    return reward

def main():
    tracks = load(TRACKS_PATH, [])
    known = load_known_species()
    learning = init_learning(tracks)
    graph = load(STATE/"knowledge_graph.json", {"schema":"biomimic-kg-v1","nodes":{},"edges":{}})
    negative = load(STATE/"negative_knowledge.json", [])
    history = load(STATE/"runs.json", [])

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    chosen = choose_tracks(tracks, learning, MAX_TRACKS_PER_RUN)
    run = {
        "run_id":run_id, "started_at":now_iso(), "tracks":[t["id"] for t in chosen],
        "provider_status":{}, "papers":[], "candidates":[], "track_metrics":{},
        "claims":[], "human_bridges":[], "failures":[]
    }

    all_candidate_buckets = {}

    for track in chosen:
        try:
            data = query_track(track, learning)
            papers = data.get("resultList",{}).get("result",[])
            run["provider_status"]["Europe PMC"] = "PASS"
        except Exception as e:
            run["provider_status"]["Europe PMC"] = "PARTIAL"
            run["failures"].append({"track":track["id"],"stage":"search","error":str(e)})
            papers = []

        t_new = set()
        t_verified = set()
        t_mechs = set()
        src_ids = set()

        # Only annotation-check a limited number of papers to stay polite/lightweight.
        annotation_budget = 6
        for idx,p in enumerate(papers):
            text = (p.get("title") or "") + " " + (p.get("abstractText") or "")
            latins = latin_mentions(text)
            mechs = mechanisms(text)
            gs = genes(text)
            src = paper_id(p)
            src_ids.add(src)
            ann = species_annotation_support(p) if idx < annotation_budget else set()

            run["papers"].append({
                "track":track["id"], "source_id":src, "title":p.get("title"),
                "year":p.get("pubYear"), "citations":int(p.get("citedByCount") or 0),
                "species_mentions":latins, "mechanisms":mechs, "genes":gs
            })

            paper_node = "paper:"+src
            graph_add_node(graph,paper_node,"paper",p.get("title") or src,{"year":p.get("pubYear")})
            track_node = "phenotype:"+track["id"]
            graph_add_node(graph,track_node,"phenotype",track["label"])
            graph_add_edge(graph,paper_node,track_node,"studies",src,1.0)

            for name in latins:
                if is_known_species(name,known):
                    continue
                key = norm(name)
                bucket = all_candidate_buckets.setdefault(key,{
                    "name":name,"tracks":set(),"papers":set(),"mechanisms":set(),
                    "genes":set(),"citations":0,"annotation_support":False
                })
                bucket["tracks"].add(track["id"])
                bucket["papers"].add(src)
                bucket["mechanisms"].update(mechs)
                bucket["genes"].update(gs)
                bucket["citations"] += int(p.get("citedByCount") or 0)
                if key in ann:
                    bucket["annotation_support"] = True
                    t_verified.add(name)
                t_new.add(name)
                t_mechs.update(mechs)

                species_node = "species:"+key.replace(" ","_")
                graph_add_node(graph,species_node,"species",name,{"status":"candidate"})
                graph_add_edge(graph,paper_node,species_node,"mentions",src,1.0)
                graph_add_edge(graph,species_node,track_node,"candidate_for",src,0.5)
                for mech in mechs:
                    mech_node = "mechanism:"+norm(mech).replace(" ","_")
                    graph_add_node(graph,mech_node,"mechanism",mech)
                    graph_add_edge(graph,species_node,mech_node,"associated_with",src,0.5)

        metrics = {
            "novel_species":len(t_new),
            "verified_species":len(t_verified),
            "mechanism_density": (len(t_mechs)/max(1,len(papers))),
            "source_diversity":len(src_ids)
        }
        reward = update_learning(learning,track,metrics)
        metrics["policy_reward"] = round(reward,6)
        run["track_metrics"][track["id"]] = metrics

    # Taxonomy verification in one batch.
    names = [b["name"] for b in all_candidate_buckets.values()]
    ensembl = verify_ensembl_species(names)
    run["provider_status"]["Ensembl"] = "PASS" if ensembl else "PARTIAL"

    negative_subjects = {norm(x.get("subject","")) for x in negative}
    candidates = []
    for key,b in all_candidate_buckets.items():
        c = {
            "name":b["name"],
            "tracks":sorted(b["tracks"]),
            "paper_count":len(b["papers"]),
            "sources":sorted(b["papers"]),
            "mechanisms":sorted(b["mechanisms"]),
            "genes":sorted(b["genes"])[:20],
            "citations":b["citations"],
            "annotation_support":bool(b["annotation_support"]),
            "ensembl_verified":b["name"] in ensembl,
            "ensembl_species":ensembl.get(b["name"]),
            "blocked":key in negative_subjects
        }
        c["evidence_evaluator"] = evaluator_evidence(c)
        c["skeptic_evaluator"] = evaluator_skeptic(c)
        c["disagreement"] = abs(c["evidence_evaluator"]-c["skeptic_evaluator"])
        c["arbiter"] = max(0, round(
            (c["evidence_evaluator"]+c["skeptic_evaluator"])/2 - c["disagreement"]*0.25
        ))
        c["morpheus_flags"] = morpheus_flags(c)
        c["status"] = (
            "BLOCKED" if c["blocked"] else
            "VERIFIED_CANDIDATE" if c["annotation_support"] and c["ensembl_verified"] and c["paper_count"] >= 2 else
            "PLAUSIBLE_CANDIDATE" if (c["annotation_support"] or c["ensembl_verified"]) and c["paper_count"] >= 2 else
            "UNVERIFIED_CANDIDATE"
        )
        candidates.append(c)

        sn = "species:"+key.replace(" ","_")
        if sn in graph["nodes"]:
            graph["nodes"][sn]["attrs"].update({
                "status":c["status"],"arbiter":c["arbiter"],
                "ensembl_species":c["ensembl_species"]
            })

    candidates.sort(key=lambda x:(x["blocked"],-x["arbiter"],-x["paper_count"]))
    run["candidates"] = candidates[:100]

    # Claims are deliberately bounded.
    for c in run["candidates"][:25]:
        run["claims"].append({
            "subject":c["name"],
            "claim":f"{c['name']} is a comparative-biology candidate for tracks: {', '.join(c['tracks'])}",
            "status":c["status"],
            "sources":c["sources"][:8],
            "arbiter":c["arbiter"],
            "limitations":c["morpheus_flags"][:6]
        })

    learning["total_runs"] += 1
    run["finished_at"] = now_iso()

    # Objective learning/progress metrics.
    run["progress"] = {
        "graph_nodes":len(graph["nodes"]),
        "graph_edges":len(graph["edges"]),
        "new_candidates":len(run["candidates"]),
        "verified_candidates":sum(1 for c in run["candidates"] if c["status"]=="VERIFIED_CANDIDATE"),
        "plausible_candidates":sum(1 for c in run["candidates"] if c["status"]=="PLAUSIBLE_CANDIDATE"),
        "negative_knowledge_size":len(negative),
        "mean_arbiter":round(sum(c["arbiter"] for c in run["candidates"])/max(1,len(run["candidates"])),2)
    }

    # Replay fingerprint.
    fingerprint_payload = {
        "run_id":run["run_id"],"tracks":run["tracks"],"papers":run["papers"],
        "candidates":run["candidates"],"learning":learning
    }
    run["sha256"] = hashlib.sha256(
        json.dumps(fingerprint_payload,sort_keys=True,ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    # Persist.
    history.insert(0,{
        "run_id":run["run_id"],"finished_at":run["finished_at"],"tracks":run["tracks"],
        "progress":run["progress"],"sha256":run["sha256"]
    })
    history = history[:365]

    save(STATE/"learning.json",learning)
    save(STATE/"knowledge_graph.json",graph)
    save(STATE/"runs.json",history)
    save(STATE/"latest.json",run)
    save(PUBLIC/"latest.json",run)
    save(PUBLIC/"history.json",history)
    save(PUBLIC/"learning.json",learning)

    report = [
        f"# BIO-MIMIC X Daily Lab — {run_id}",
        "",
        f"**SHA-256:** `{run['sha256']}`",
        "",
        "## Run",
        f"- Tracks: {', '.join(run['tracks'])}",
        f"- Papers: {len(run['papers'])}",
        f"- Novel candidates: {run['progress']['new_candidates']}",
        f"- Verified candidates: {run['progress']['verified_candidates']}",
        f"- Plausible candidates: {run['progress']['plausible_candidates']}",
        f"- Knowledge graph: {run['progress']['graph_nodes']} nodes / {run['progress']['graph_edges']} edges",
        f"- Mean Arbiter score: {run['progress']['mean_arbiter']}",
        "",
        "## Top candidates",
    ]
    for c in run["candidates"][:12]:
        report += [
            f"### {c['name']} — {c['status']} — Arbiter {c['arbiter']}",
            f"- Papers: {c['paper_count']} | citations signal: {c['citations']}",
            f"- Annotation support: {c['annotation_support']} | Ensembl verified: {c['ensembl_verified']}",
            f"- Mechanisms: {', '.join(c['mechanisms'][:8]) or 'none extracted'}",
            f"- Genes: {', '.join(c['genes'][:8]) or 'none extracted'}",
            f"- Sources: {', '.join(c['sources'][:6])}",
            f"- Morpheus: {', '.join(c['morpheus_flags'][:6])}",
            ""
        ]
    (REPORTS/f"{run_id}.md").write_text("\n".join(report),encoding="utf-8")
    (REPORTS/"LATEST.md").write_text("\n".join(report),encoding="utf-8")

    print(json.dumps({
        "status":"PASS",
        "run_id":run_id,
        "papers":len(run["papers"]),
        "candidates":len(run["candidates"]),
        "verified":run["progress"]["verified_candidates"],
        "graph_nodes":run["progress"]["graph_nodes"],
        "graph_edges":run["progress"]["graph_edges"],
        "sha256":run["sha256"]
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
