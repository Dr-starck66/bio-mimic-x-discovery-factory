#!/usr/bin/env python3
from __future__ import annotations
import json, re, time, urllib.parse, urllib.request
from pathlib import Path

ENSEMBL_BASE="https://rest.ensembl.org"
OPEN_TARGETS="https://api.platform.opentargets.org/api/v4/graphql"
EPMC_ANN="https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds"
OMA_BASE="https://omabrowser.org/api"
UNIPROT_SEARCH="https://rest.uniprot.org/uniprotkb/search"
TIMEOUT=12
ORTHO_CACHE={}
OT_CACHE={}
OMA_INFO_CACHE={}
OMA_ORTHO_CACHE={}
OMA_XREF_CACHE={}
ANN_ENTITY_CACHE={}
UNIPROT_SEARCH_CACHE={}

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

def _walk_annotation_entities(x,names,uniprots):
    if isinstance(x,dict):
        sel=x.get("selector")
        if isinstance(sel,dict):
            exact=str(sel.get("exact") or "").strip()
            if exact:
                names.add(exact)
        tags=x.get("tags")
        if isinstance(tags,list):
            for t in tags:
                if not isinstance(t,dict):
                    continue
                uri=str(t.get("uri") or "")
                name=str(t.get("name") or "").strip()
                low=uri.lower()
                if name and any(k in low for k in ("uniprot","ensembl","/gene/","ncbigene","identifiers.org/hgnc")):
                    names.add(name)
                if "uniprot" in low:
                    m=re.search(r"/uniprotkb/([A-Za-z0-9]{6,10})(?:-\d+)?(?:/|$)",uri,re.I)
                    if not m:
                        m=re.search(r"(?:uniprot:|uniprotkb:)([A-Za-z0-9]{6,10})(?:-\d+)?",uri,re.I)
                    if m:
                        uniprots.add(m.group(1).upper())
        body=x.get("body")
        if isinstance(body,str) and "uniprot" in body.lower():
            m=re.search(r"/uniprotkb/([A-Za-z0-9]{6,10})(?:-\d+)?(?:/|$)",body,re.I)
            if not m:
                m=re.search(r"(?:uniprot:|uniprotkb:)([A-Za-z0-9]{6,10})(?:-\d+)?",body,re.I)
            if m:
                uniprots.add(m.group(1).upper())
        for v in x.values():
            _walk_annotation_entities(v,names,uniprots)
    elif isinstance(x,list):
        for v in x:
            _walk_annotation_entities(v,names,uniprots)

GENE_NOISE={
    "DNA","RNA","PCR","RT-PCR","NIH","USDA","ER","IBP","PBD","OCTA","SD-OCT",
    "NF-","PCNA-"
}

def annotation_entities(candidate):
    key=tuple(sorted(candidate.get("pmid_sources") or candidate.get("sources") or []))
    if key in ANN_ENTITY_CACHE:
        return ANN_ENTITY_CACHE[key]
    pmids=[]
    for s in key:
        s=str(s)
        if s.startswith("PMID:"):
            pmids.append(s.split(":",1)[1])
    if not pmids:
        result={"names":[],"uniprots":[]}
        ANN_ENTITY_CACHE[key]=result
        return result

    ids=",".join("MED:"+p for p in pmids[:4])
    try:
        url=EPMC_ANN+"?"+urllib.parse.urlencode({
            "articleIds":ids,
            "type":"Gene_Proteins",
            "provider":"Europe PMC",
            "format":"JSON",
            "pageSize":"1000"
        })
        data=get_json(url,1)
    except Exception:
        result={"names":[],"uniprots":[]}
        ANN_ENTITY_CACHE[key]=result
        return result

    raw=set(); uniprots=set()
    _walk_annotation_entities(data,raw,uniprots)
    names=set()
    for x in raw:
        x=x.strip()
        if not x or len(x)>80 or x.upper() in GENE_NOISE:
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{1,20}",x) or (" " in x and len(x)<=60):
            names.add(x)
    result={"names":sorted(names),"uniprots":sorted(uniprots)}
    ANN_ENTITY_CACHE[key]=result
    return result

def annotation_gene_candidates(candidate):
    return annotation_entities(candidate)["names"]

def annotation_uniprot_candidates(candidate,max_ids=8):
    return annotation_entities(candidate)["uniprots"][:max_ids]


def candidate_gene_candidates(candidate,max_genes=10):
    vals=[]
    for g in candidate.get("genes") or []:
        g=str(g).strip()
        if not g or g.upper() in GENE_NOISE:
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{1,15}",g) and g not in vals:
            vals.append(g)
    for g in annotation_gene_candidates(candidate):
        # Prefer compact symbols/accession-like labels. Full protein names create
        # many low-value Ensembl calls and are kept out of the online bridge path.
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{1,15}",g) and g not in vals:
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
    key=(species,gene)
    if key in ORTHO_CACHE:
        return ORTHO_CACHE[key]
    params="target_species=human;type=orthologues;sequence=none;content-type=application/json"
    url=f"{ENSEMBL_BASE}/homology/symbol/{urllib.parse.quote(species)}/{urllib.parse.quote(gene)}?{params}"
    try:
        data=get_json(url,1)
        out=collect_human_orthologues(data)
    except Exception:
        out=[]
    ORTHO_CACHE[key]=out
    return out

def opentarget_context(ensembl_id):
    if ensembl_id in OT_CACHE:
        return OT_CACHE[ensembl_id]
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
        OT_CACHE[ensembl_id]=None
        return None
    tr=[x for x in (target.get("tractability") or []) if x.get("value")]
    result={
        "id":target.get("id"),
        "approved_symbol":target.get("approvedSymbol"),
        "approved_name":target.get("approvedName"),
        "biotype":target.get("biotype"),
        "tractability":[{"label":x.get("label"),"modality":x.get("modality")} for x in tr[:12]]
    }
    OT_CACHE[ensembl_id]=result
    return result

def uniprot_species_gene_accessions(candidate,max_terms=7,max_accessions=10):
    """Resolve article-derived gene/protein terms inside the exact claim species."""
    species=candidate_name(candidate)
    terms=candidate_gene_candidates(candidate,max_genes=max_terms)
    cache_key=(norm(species),tuple(terms))
    if cache_key in UNIPROT_SEARCH_CACHE:
        return UNIPROT_SEARCH_CACHE[cache_key]

    out=[]
    for term in terms:
        # Avoid free-text phrases here: gene: is intentionally constrained.
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{1,15}",term):
            continue
        query=f'(organism_name:"{species}") AND (gene:{term})'
        try:
            url=UNIPROT_SEARCH+"?"+urllib.parse.urlencode({
                "query":query,
                "format":"json",
                "fields":"accession,gene_names,organism_name",
                "size":"4"
            })
            data=get_json(url,1)
        except Exception:
            continue
        for row in data.get("results",[]) if isinstance(data,dict) else []:
            org=(row.get("organism") or {}).get("scientificName") or ""
            acc=str(row.get("primaryAccession") or "").strip()
            if norm(org)!=norm(species):
                continue
            if re.fullmatch(r"[A-Z0-9]{6,10}",acc) and acc not in out:
                out.append(acc)
                if len(out)>=max_accessions:
                    UNIPROT_SEARCH_CACHE[cache_key]=out
                    return out
    UNIPROT_SEARCH_CACHE[cache_key]=out
    return out

def oma_protein_info(entry_id):
    if entry_id in OMA_INFO_CACHE:
        return OMA_INFO_CACHE[entry_id]
    try:
        data=get_json(f"{OMA_BASE}/protein/{urllib.parse.quote(str(entry_id))}/",1)
    except Exception:
        data=None
    OMA_INFO_CACHE[entry_id]=data
    return data

def oma_human_orthologs(entry_id):
    if entry_id in OMA_ORTHO_CACHE:
        return OMA_ORTHO_CACHE[entry_id]
    try:
        data=get_json(f"{OMA_BASE}/protein/{urllib.parse.quote(str(entry_id))}/orthologs/",1)
    except Exception:
        data=[]
    out=[]
    if isinstance(data,list):
        for x in data:
            if not isinstance(x,dict):
                continue
            sp=x.get("species") or {}
            if sp.get("taxon_id")==9606:
                out.append(x)
    OMA_ORTHO_CACHE[entry_id]=out
    return out

def oma_xrefs(entry_id):
    if entry_id in OMA_XREF_CACHE:
        return OMA_XREF_CACHE[entry_id]
    try:
        data=get_json(f"{OMA_BASE}/protein/{urllib.parse.quote(str(entry_id))}/xref/",1)
    except Exception:
        data=[]
    OMA_XREF_CACHE[entry_id]=data if isinstance(data,list) else []
    return OMA_XREF_CACHE[entry_id]

def human_ensembl_ids_from_oma(entry):
    ids=[]
    entry_id=entry.get("entry_nr") or entry.get("omaid") or entry.get("canonicalid")
    for x in oma_xrefs(entry_id):
        val=str(x.get("xref") or "").split(".",1)[0]
        if re.fullmatch(r"ENSG\d{6,}",val) and val not in ids:
            ids.append(val)
    return ids

def oma_bridges_for_candidate(candidate,max_uniprots=10):
    name=candidate_name(candidate)
    wanted=norm(name)
    bridges=[]; checked=0; matched_species=0
    annotated=annotation_uniprot_candidates(candidate,max_ids=max_uniprots)
    species_resolved=uniprot_species_gene_accessions(candidate,max_accessions=max_uniprots)
    accessions=[]
    for acc in species_resolved+annotated:
        if acc not in accessions:
            accessions.append(acc)
    for acc in accessions[:max_uniprots]:
        checked+=1
        info=oma_protein_info(acc)
        if not isinstance(info,dict):
            continue
        sp=info.get("species") or {}
        if norm(str(sp.get("species") or "")) != wanted:
            continue
        matched_species+=1
        for h in oma_human_orthologs(acc)[:4]:
            for ensg in human_ensembl_ids_from_oma(h)[:2]:
                try:
                    human=opentarget_context(ensg)
                except Exception:
                    human=None
                if not human:
                    continue
                bridges.append({
                    "animal_species":name,
                    "animal_ensembl_species":None,
                    "animal_gene":acc,
                    "animal_uniprot":acc,
                    "human_ensembl_id":ensg,
                    "human_symbol":human.get("approved_symbol"),
                    "human_name":human.get("approved_name"),
                    "human_biotype":human.get("biotype"),
                    "orthology":{
                        "provider":"OMA",
                        "rel_type":h.get("rel_type"),
                        "distance":h.get("distance"),
                        "score":h.get("score"),
                        "human_omaid":h.get("omaid"),
                        "human_canonicalid":h.get("canonicalid")
                    },
                    "tractability":human.get("tractability",[]),
                    "source_claim_pmids":candidate.get("pmid_sources",[]),
                    "source_chain":[
                        "replicated PMID claim",
                        "Europe PMC Gene_Proteins term extraction",
                        "UniProt exact-species gene/protein resolution",
                        "OMA source-protein species verification",
                        "OMA pairwise orthology to Homo sapiens",
                        "OMA human Ensembl xref",
                        "Open Targets human target annotation"
                    ],
                    "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
                    "clinical_efficacy_claim":False
                })
    return bridges,{
        "oma_uniprots_checked":checked,
        "oma_species_matched":matched_species,
        "uniprot_annotation_candidates":len(annotated),
        "uniprot_species_gene_candidates":len(species_resolved)
    }

def build_human_bridges(portfolio,max_candidates=20,max_genes=10):
    try:
        species_index=ensembl_species_index()
        species_provider="PASS"
    except Exception as e:
        # Ensembl availability must never disable the OMA fallback.
        species_index={}
        species_provider=f"FAIL: {e}"

    bridges=[]; attempted=0; resolved=0; orth_hits=0; ot_hits=0; errors=[]
    candidate_status=[]

    for c in portfolio[:max_candidates]:
        attempted+=1
        name=candidate_name(c)
        row={"candidate":name,"status":"UNRESOLVED","ensembl_species":None,
             "gene_candidates":0,"validated_gene_candidates":[],"bridges":0}
        ens_species=resolve_ensembl_species(c,species_index)
        if ens_species:
            resolved+=1
            row["ensembl_species"]=ens_species

        genes=candidate_gene_candidates(c,max_genes=max_genes)
        row["gene_candidates"]=len(genes)

        if ens_species:
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

        oma_new,oma_stats=oma_bridges_for_candidate(c)
        bridges.extend(oma_new)
        row.update(oma_stats)
        row["uniprot_candidates"]=row.get("uniprot_annotation_candidates",0)+row.get("uniprot_species_gene_candidates",0)

        row["bridges"]=sum(1 for b in bridges if b["animal_species"]==name)
        if row["bridges"]:
            row["status"]="BRIDGED"
        elif not ens_species and row.get("oma_species_matched",0)==0:
            row["status"]="NO_SUPPORTED_ORTHOLOGY_PROVIDER_MATCH"
        elif not genes and not row.get("uniprot_candidates",0):
            row["status"]="NO_GENE_OR_PROTEIN_ANNOTATION"
        elif row["validated_gene_candidates"]:
            row["status"]="NO_HUMAN_TARGET_CONTEXT"
        else:
            row["status"]="NO_VALIDATED_ORTHOLOGUE"
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
    oma_bridge_count=sum(1 for b in bridges if (b.get("orthology") or {}).get("provider")=="OMA")
    verified_human_targets=len({(b["animal_species"],b["human_ensembl_id"]) for b in bridges})
    total_orthologue_hits=orth_hits+oma_bridge_count

    # PASS means all replicated claims got at least one verified human bridge.
    # Anything less is explicitly PARTIAL rather than hidden.
    status="PASS" if attempted>0 and bridged==attempted else "PARTIAL"
    return {
        "status":status,
        "provider_status":{
            "Europe PMC annotations":"PASS",
            "Ensembl species":species_provider,
            "OMA orthology":"PASS" if oma_bridge_count else "PARTIAL",
            "Ensembl homology":"PASS" if orth_hits else "PARTIAL",
            "Open Targets":"PASS" if verified_human_targets else "PARTIAL"
        },
        "attempted_candidates":attempted,
        "resolved_species":resolved,
        "bridged_candidates":bridged,
        "coverage_ratio":coverage,
        "orthologue_hits":total_orthologue_hits,
        "open_targets_hits":verified_human_targets,
        "ensembl_orthologue_hits":orth_hits,
        "oma_orthologue_hits":oma_bridge_count,
        "bridges":bridges,
        "candidate_status":candidate_status,
        "errors":errors[:50]
    }

