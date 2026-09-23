#!/usr/bin/env python3
from __future__ import annotations
import json, re, time, urllib.parse, urllib.request
from pathlib import Path

ENSEMBL_BASE="https://rest.ensembl.org"
OPEN_TARGETS="https://api.platform.opentargets.org/api/v4/graphql"
TIMEOUT=18

def norm(x):
    return re.sub(r"[^a-z0-9]+"," ",(x or "").lower()).strip()

def get_json(url,retries=2):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"BIO-MIMIC-X-V7.1/1.0",
                "Accept":"application/json"
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last=e
            if i<retries-1: time.sleep(0.6*(i+1))
    raise last

def post_json(url,payload,retries=2):
    data=json.dumps(payload).encode("utf-8")
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,data=data,method="POST",headers={
                "User-Agent":"BIO-MIMIC-X-V7.1/1.0",
                "Accept":"application/json",
                "Content-Type":"application/json"
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last=e
            if i<retries-1: time.sleep(0.6*(i+1))
    raise last

def ensembl_species_index():
    data=get_json(ENSEMBL_BASE+"/info/species?content-type=application/json",1)
    out={}
    for s in data.get("species",[]):
        aliases=set()
        for x in [s.get("name",""),s.get("display_name","")]:
            if x:
                aliases.add(norm(x.replace("_"," ")))
        for a in s.get("aliases") or []:
            aliases.add(norm(a))
        for a in aliases:
            if a:
                out[a]=s.get("name")
    return out

def resolve_ensembl_species(candidate,index):
    names=[candidate.get("name","")]
    for proof in candidate.get("taxon_proofs") or []:
        names += [proof.get("canonical_name",""),proof.get("scientific_name","")]
    for n in names:
        k=norm(n)
        if k in index:
            return index[k]
    return None

def collect_human_orthologues(obj):
    found={}
    def walk(x):
        if isinstance(x,dict):
            # Ensembl full homology responses normally expose a target object.
            t=x.get("target")
            if isinstance(t,dict):
                sid=str(t.get("id") or "")
                species=norm(str(t.get("species") or ""))
                if sid.startswith("ENSG") and species in ("homo sapiens","homo_sapiens","human",""):
                    found[sid]={
                        "ensembl_id":sid,
                        "protein_id":t.get("protein_id"),
                        "perc_id":t.get("perc_id"),
                        "perc_pos":t.get("perc_pos"),
                        "taxon_id":t.get("taxon_id")
                    }
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(obj)
    return list(found.values())

def orthologues_for_symbol(species,gene):
    params="target_species=human;type=orthologues;sequence=none;content-type=application/json"
    url=f"{ENSEMBL_BASE}/homology/symbol/{urllib.parse.quote(species)}/{urllib.parse.quote(gene)}?{params}"
    data=get_json(url,1)
    return collect_human_orthologues(data)

def opentarget_context(ensembl_id):
    query="""
    query targetInfo($ensemblId: String!) {
      target(ensemblId: $ensemblId) {
        id
        approvedSymbol
        approvedName
        biotype
        tractability { label modality value }
      }
    }
    """
    data=post_json(OPEN_TARGETS,{"query":query,"variables":{"ensemblId":ensembl_id}},1)
    target=((data.get("data") or {}).get("target"))
    if not target:
        return None
    tr=[x for x in (target.get("tractability") or []) if x.get("value")]
    return {
        "id":target.get("id"),
        "approved_symbol":target.get("approvedSymbol"),
        "approved_name":target.get("approvedName"),
        "biotype":target.get("biotype"),
        "tractability":[{"label":x.get("label"),"modality":x.get("modality")} for x in tr[:12]]
    }

def build_human_bridges(portfolio,max_candidates=12,max_genes=8):
    try:
        species_index=ensembl_species_index()
        species_provider="PASS"
    except Exception as e:
        return {
            "status":"PARTIAL",
            "provider_status":{"Ensembl species":f"FAIL: {e}"},
            "bridges":[],
            "attempted_candidates":0,
            "resolved_species":0,
            "orthologue_hits":0,
            "open_targets_hits":0
        }

    bridges=[]
    attempted=0
    resolved=0
    orth_hits=0
    ot_hits=0
    errors=[]

    for c in portfolio[:max_candidates]:
        attempted+=1
        ens_species=resolve_ensembl_species(c,species_index)
        if not ens_species:
            continue
        resolved+=1
        genes=[]
        for g in c.get("genes") or []:
            g=str(g).strip()
            # conservative symbol shape; Ensembl call is the authoritative validation.
            if re.fullmatch(r"[A-Z][A-Z0-9.-]{1,14}",g) and g not in genes:
                genes.append(g)
        for gene in genes[:max_genes]:
            try:
                orths=orthologues_for_symbol(ens_species,gene)
            except Exception as e:
                errors.append({"candidate":c.get("name"),"gene":gene,"stage":"ensembl_homology","error":str(e)[:180]})
                continue
            if not orths:
                continue
            orth_hits+=len(orths)
            for orth in orths[:3]:
                try:
                    human=opentarget_context(orth["ensembl_id"])
                except Exception as e:
                    errors.append({"candidate":c.get("name"),"gene":gene,"stage":"open_targets","error":str(e)[:180]})
                    human=None
                if not human:
                    continue
                ot_hits+=1
                bridges.append({
                    "animal_species":c.get("name"),
                    "animal_ensembl_species":ens_species,
                    "animal_gene":gene,
                    "human_ensembl_id":orth["ensembl_id"],
                    "human_symbol":human.get("approved_symbol"),
                    "human_name":human.get("approved_name"),
                    "human_biotype":human.get("biotype"),
                    "orthology":orth,
                    "tractability":human.get("tractability",[]),
                    "source_chain":[
                        "candidate taxonomy proof / organism annotation",
                        "Ensembl Compara orthology",
                        "Open Targets human target annotation"
                    ],
                    "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
                    "clinical_efficacy_claim":False
                })

    # Deduplicate exact animal/gene/human target bridges.
    uniq={}
    for b in bridges:
        key=(b["animal_species"],b["animal_gene"],b["human_ensembl_id"])
        uniq[key]=b
    bridges=list(uniq.values())

    status="PASS" if bridges else "PARTIAL"
    return {
        "status":status,
        "provider_status":{
            "Ensembl species":species_provider,
            "Ensembl homology":"PASS" if orth_hits else "PARTIAL",
            "Open Targets":"PASS" if ot_hits else "PARTIAL"
        },
        "attempted_candidates":attempted,
        "resolved_species":resolved,
        "orthologue_hits":orth_hits,
        "open_targets_hits":ot_hits,
        "bridges":bridges,
        "errors":errors[:25]
    }
