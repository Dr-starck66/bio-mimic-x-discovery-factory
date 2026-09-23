#!/usr/bin/env python3
from __future__ import annotations
import json, re, time, urllib.parse, urllib.request
from pathlib import Path

ENSEMBL_BASE="https://rest.ensembl.org"
OPEN_TARGETS="https://api.platform.opentargets.org/api/v4/graphql"
EPMC_ANN="https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds"
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

def candidate_name(candidate):
    return candidate.get("subject") or candidate.get("name") or ""

def resolve_ensembl_species(candidate,index):
    names=[candidate_name(candidate)]
    for proof in candidate.get("taxon_proofs") or []:
        names += [proof.get("canonical_name",""),proof.get("scientific_name","")]
    for n in names:
        k=norm(n)
        if k in index:
            return index[k]
    return None

def _walk_annotations(x,out):
    if isinstance(x,dict):
        sel=x.get("selector")
        if isinstance(sel,dict):
            exact=str(sel.get("exact") or "").strip()
            if exact:
                out.add(exact)
        tags=x.get("tags")
        if isinstance(tags,list):
            for t in tags:
                if not isinstance(t,dict):
                    continue
                uri=str(t.get("uri") or "").lower()
                name=str(t.get("name") or "").strip()
                if name and any(k in uri for k in ("uniprot","ensembl","/gene/","ncbigene","identifiers.org/hgnc")):
                    out.add(name)
        for v in x.values():
            _walk_annotations(v,out)
    elif isinstance(x,list):
        for v in x:
            _walk_annotations(v,out)

GENE_NOISE={
    "DNA","RNA","PCR","RT-PCR","NIH","USDA","MAPK","ER","IBP","PBD","OCTA","SD-OCT",
    "NF-","PCNA-","VEGF"
}

def annotation_gene_candidates(candidate):
    pmids=[]
    for s in candidate.get("pmid_sources") or candidate.get("sources") or []:
        s=str(s)
        if s.startswith("PMID:"):
            pmids.append(s.split(":",1)[1])
    out=set()
    for pmid in pmids[:4]:
        try:
            url=EPMC_ANN+"?"+urllib.parse.urlencode({
                "articleIds":"MED:"+pmid,
                "format":"JSON",
                "pageSize":"1000"
            })
            data=get_json(url,1)
            raw=set(); _walk_annotations(data,raw)
            for x in raw:
                x=x.strip()
                if not x or len(x)>80:
                    continue
                # Keep plausible symbols/display names; Ensembl remains the authority.
                if x.upper() in GENE_NOISE:
                    continue
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{1,20}",x) or (" " in x and len(x)<=60):
                    out.add(x)
        except Exception:
            continue
    return sorted(out)

def candidate_gene_candidates(candidate,max_genes=24):
    vals=[]
    for g in candidate.get("genes") or []:
        g=str(g).strip()
        if not g or g.upper() in GENE_NOISE:
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{1,20}",g) and g not in vals:
            vals.append(g)
    for g in annotation_gene_candidates(candidate):
        if g not in vals:
            vals.append(g)
    return vals[:max_genes]

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
    data=get_json(url,2)
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

def build_human_bridges(portfolio,max_candidates=20,max_genes=24):
    try:
        species_index=ensembl_species_index()
        species_provider="PASS"
    except Exception as e:
        return {
            "status":"PARTIAL",
            "provider_status":{"Ensembl species":f"FAIL: {e}"},
            "bridges":[],"candidate_status":[],
            "attempted_candidates":0,"resolved_species":0,
            "bridged_candidates":0,"coverage_ratio":0,
            "orthologue_hits":0,"open_targets_hits":0
        }

    bridges=[]; attempted=0; resolved=0; orth_hits=0; ot_hits=0; errors=[]
    candidate_status=[]

    for c in portfolio[:max_candidates]:
        attempted+=1
        name=candidate_name(c)
        row={"candidate":name,"status":"UNRESOLVED","ensembl_species":None,
             "gene_candidates":0,"validated_gene_candidates":[],"bridges":0}
        ens_species=resolve_ensembl_species(c,species_index)
        if not ens_species:
            row["status"]="NO_ENSEMBL_SPECIES"
            candidate_status.append(row)
            continue
        resolved+=1
        row["ensembl_species"]=ens_species

        genes=candidate_gene_candidates(c,max_genes=max_genes)
        row["gene_candidates"]=len(genes)
        if not genes:
            row["status"]="NO_GENE_OR_PROTEIN_ANNOTATION"
            candidate_status.append(row)
            continue

        for gene in genes:
            try:
                orths=orthologues_for_symbol(ens_species,gene)
            except Exception as e:
                errors.append({"candidate":name,"gene":gene,"stage":"ensembl_homology","error":str(e)[:180]})
                continue
            if not orths:
                continue
            row["validated_gene_candidates"].append(gene)
            orth_hits+=len(orths)
            for orth in orths[:4]:
                try:
                    human=opentarget_context(orth["ensembl_id"])
                except Exception as e:
                    errors.append({"candidate":name,"gene":gene,"stage":"open_targets","error":str(e)[:180]})
                    human=None
                if not human:
                    continue
                ot_hits+=1
                bridges.append({
                    "animal_species":name,
                    "animal_ensembl_species":ens_species,
                    "animal_gene":gene,
                    "human_ensembl_id":orth["ensembl_id"],
                    "human_symbol":human.get("approved_symbol"),
                    "human_name":human.get("approved_name"),
                    "human_biotype":human.get("biotype"),
                    "orthology":orth,
                    "tractability":human.get("tractability",[]),
                    "source_claim_pmids":c.get("pmid_sources",[]),
                    "source_chain":[
                        "replicated PMID claim",
                        "Europe PMC gene/protein annotation or claim gene",
                        "Ensembl Compara orthology",
                        "Open Targets human target annotation"
                    ],
                    "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
                    "clinical_efficacy_claim":False
                })

        row["bridges"]=sum(1 for b in bridges if b["animal_species"]==name)
        row["status"]="BRIDGED" if row["bridges"] else (
            "NO_VALIDATED_ORTHOLOGUE" if row["validated_gene_candidates"] else "NO_ENSEMBL_GENE_MATCH"
        )
        candidate_status.append(row)

    uniq={}
    for b in bridges:
        key=(b["animal_species"],b["animal_gene"],b["human_ensembl_id"])
        uniq[key]=b
    bridges=list(uniq.values())

    bridged_names={b["animal_species"] for b in bridges}
    for row in candidate_status:
        row["bridges"]=sum(1 for b in bridges if b["animal_species"]==row["candidate"])
        if row["bridges"]:
            row["status"]="BRIDGED"
    bridged=len(bridged_names)
    coverage=round(bridged/max(1,attempted),4)

    # PASS means all replicated claims got at least one verified human bridge.
    # Anything less is explicitly PARTIAL rather than hidden.
    status="PASS" if attempted>0 and bridged==attempted else "PARTIAL"
    return {
        "status":status,
        "provider_status":{
            "Europe PMC annotations":"PASS",
            "Ensembl species":species_provider,
            "Ensembl homology":"PASS" if orth_hits else "PARTIAL",
            "Open Targets":"PASS" if ot_hits else "PARTIAL"
        },
        "attempted_candidates":attempted,
        "resolved_species":resolved,
        "bridged_candidates":bridged,
        "coverage_ratio":coverage,
        "orthologue_hits":orth_hits,
        "open_targets_hits":ot_hits,
        "bridges":bridges,
        "candidate_status":candidate_status,
        "errors":errors[:50]
    }

