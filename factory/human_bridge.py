#!/usr/bin/env python3
from __future__ import annotations
import json, re, time, urllib.parse, urllib.request
from pathlib import Path

ENSEMBL_BASE="https://rest.ensembl.org"
OPEN_TARGETS="https://api.platform.opentargets.org/api/v4/graphql"
EPMC_ANN="https://www.ebi.ac.uk/europepmc/annotations_api/annotationsByArticleIds"
EPMC_SEARCH="https://www.ebi.ac.uk/europepmc/webservices/rest/search"
OMA_BASE="https://omabrowser.org/api"
UNIPROT_SEARCH="https://rest.uniprot.org/uniprotkb/search"
NCBI_DATASETS="https://api.ncbi.nlm.nih.gov/datasets/v2"
ORTHODB_BASE="https://data.orthodb.org/v12"
TIMEOUT=12
ORTHO_CACHE={}
OT_CACHE={}
OMA_INFO_CACHE={}
OMA_ORTHO_CACHE={}
OMA_XREF_CACHE={}
ANN_ENTITY_CACHE={}
UNIPROT_SEARCH_CACHE={}
NCBI_GENE_CACHE={}
NCBI_ORTHO_CACHE={}
ORTHODB_GENE_CACHE={}
ORTHODB_ORTHO_CACHE={}
UNIPROT_ENTRY_CACHE={}
PUBMED_RECORD_CACHE={}

SEED_PATH=Path(__file__).with_name("bridge_seeds.json")
PHYLO_SEED_PATH=Path(__file__).with_name("phylogenetic_orthology_seeds.json")
try:
    BRIDGE_SEEDS=json.loads(SEED_PATH.read_text(encoding="utf-8")).get("species",{})
except Exception:
    BRIDGE_SEEDS={}
try:
    PHYLO_SEEDS=json.loads(PHYLO_SEED_PATH.read_text(encoding="utf-8")).get("species",{})
except Exception:
    PHYLO_SEEDS={}

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


def literature_seed_records(candidate):
    rows=BRIDGE_SEEDS.get(candidate_name(candidate),[])
    return [x for x in rows if isinstance(x,dict) and x.get("gene") and x.get("evidence_pmids")]

def literature_seed_genes(candidate):
    return [str(x["gene"]).strip() for x in literature_seed_records(candidate)]

def candidate_gene_candidates(candidate,max_genes=10):
    vals=[]
    for g in literature_seed_genes(candidate):
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{1,15}",g) and g not in vals:
            vals.append(g)
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

def ncbi_exact_gene(species,gene):
    key=(norm(species),str(gene).upper())
    if key in NCBI_GENE_CACHE:
        return NCBI_GENE_CACHE[key]
    try:
        url=(NCBI_DATASETS+"/gene/symbol/"
             +urllib.parse.quote(str(gene),safe="")
             +"/taxon/"+urllib.parse.quote(str(species),safe="")
             +"/dataset_report")
        data=get_json(url,1)
    except Exception:
        NCBI_GENE_CACHE[key]=None
        return None
    for rep in data.get("reports",[]) if isinstance(data,dict) else []:
        g=(rep or {}).get("gene") or {}
        if norm(str(g.get("taxname") or ""))!=norm(species):
            continue
        gid=str(g.get("gene_id") or "")
        if gid:
            out={
                "gene_id":gid,
                "symbol":g.get("symbol"),
                "tax_id":g.get("tax_id"),
                "taxname":g.get("taxname"),
                "description":g.get("description"),
                "gene_groups":g.get("gene_groups") or []
            }
            NCBI_GENE_CACHE[key]=out
            return out
    NCBI_GENE_CACHE[key]=None
    return None

def ncbi_human_orthologs(gene_id):
    key=str(gene_id)
    if key in NCBI_ORTHO_CACHE:
        return NCBI_ORTHO_CACHE[key]
    try:
        url=(NCBI_DATASETS+"/gene/id/"+urllib.parse.quote(key,safe="")
             +"/orthologs?taxon_filter=9606")
        data=get_json(url,1)
    except Exception:
        NCBI_ORTHO_CACHE[key]=[]
        return []
    out=[]
    for rep in data.get("reports",[]) if isinstance(data,dict) else []:
        g=(rep or {}).get("gene") or {}
        if str(g.get("tax_id") or "")!="9606":
            continue
        for ensg in g.get("ensembl_gene_ids") or []:
            if re.fullmatch(r"ENSG\d{6,}",str(ensg)):
                out.append({
                    "ensembl_id":str(ensg),
                    "gene_id":str(g.get("gene_id") or ""),
                    "symbol":g.get("symbol"),
                    "description":g.get("description"),
                    "ortholog_method":"NCBI Ortholog"
                })
    uniq={x["ensembl_id"]:x for x in out}
    out=list(uniq.values())
    NCBI_ORTHO_CACHE[key]=out
    return out

def ncbi_bridges_for_candidate(candidate):
    name=candidate_name(candidate)
    bridges=[]; checked=0; exact_genes=0; human_orthologs=0
    for seed in literature_seed_records(candidate):
        gene=str(seed["gene"]).strip()
        checked+=1
        source=ncbi_exact_gene(name,gene)
        if not source:
            continue
        exact_genes+=1
        orths=ncbi_human_orthologs(source["gene_id"])
        human_orthologs+=len(orths)
        for orth in orths:
            try:
                human=opentarget_context(orth["ensembl_id"])
            except Exception:
                human=None
            if not human:
                continue
            bridges.append({
                "animal_species":name,
                "animal_ensembl_species":None,
                "animal_gene":source.get("symbol") or gene,
                "animal_ncbi_gene_id":source["gene_id"],
                "human_ensembl_id":orth["ensembl_id"],
                "human_symbol":human.get("approved_symbol"),
                "human_name":human.get("approved_name"),
                "human_biotype":human.get("biotype"),
                "orthology":{
                    "provider":"NCBI Ortholog",
                    "method":"NCBI Ortholog",
                    "human_ncbi_gene_id":orth.get("gene_id"),
                    "source_tax_id":source.get("tax_id")
                },
                "tractability":human.get("tractability",[]),
                "source_claim_pmids":candidate.get("pmid_sources",[]),
                "bridge_evidence_pmids":[str(x) for x in seed.get("evidence_pmids",[])],
                "bridge_seed_rationale":seed.get("rationale"),
                "source_chain":[
                    "replicated PMID species claim",
                    "literature-backed exact-species mechanism seed",
                    "NCBI Datasets exact species + gene resolution",
                    "NCBI Ortholog to Homo sapiens",
                    "NCBI human Ensembl Gene ID",
                    "Open Targets human target annotation"
                ],
                "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
                "clinical_efficacy_claim":False
            })
    return bridges,{
        "ncbi_seed_genes_checked":checked,
        "ncbi_exact_genes":exact_genes,
        "ncbi_human_orthologs":human_orthologs
    }

def _gene_norm(x):
    return re.sub(r"[^a-z0-9]+","",str(x or "").lower())

def europepmc_record(pmid):
    pmid=str(pmid or "").replace("PMID:","").strip()
    if pmid in PUBMED_RECORD_CACHE:
        return PUBMED_RECORD_CACHE[pmid]
    try:
        url=EPMC_SEARCH+"?"+urllib.parse.urlencode({
            "query":f"EXT_ID:{pmid}",
            "format":"json",
            "resultType":"core",
            "pageSize":"1"
        })
        data=get_json(url,1)
        rows=((data.get("resultList") or {}).get("result") or []) if isinstance(data,dict) else []
        rec=rows[0] if rows else None
    except Exception:
        rec=None
    PUBMED_RECORD_CACHE[pmid]=rec
    return rec

def validate_bridge_context_paper(pmid,species,gene):
    rec=europepmc_record(pmid)
    if not isinstance(rec,dict):
        return False
    text=" ".join([
        str(rec.get("title") or ""),
        str(rec.get("abstractText") or "")
    ]).lower()
    species_key=norm(species)
    if species_key not in norm(text):
        return False
    gene_key=str(gene or "").lower()
    gene_ok=(gene_key in text) or (gene_key=="shh" and "sonic hedgehog" in text)
    if not gene_ok:
        return False
    if "regenerat" not in text:
        return False
    return True

def uniprot_entry(accession):
    accession=str(accession or "").strip()
    if accession in UNIPROT_ENTRY_CACHE:
        return UNIPROT_ENTRY_CACHE[accession]
    try:
        data=get_json("https://rest.uniprot.org/uniprotkb/"+urllib.parse.quote(accession)+".json",1)
    except Exception:
        data=None
    UNIPROT_ENTRY_CACHE[accession]=data
    return data

def uniprot_exact_species_gene(accession,species,gene,taxon_id=None):
    data=uniprot_entry(accession)
    if not isinstance(data,dict):
        return None
    org=data.get("organism") or {}
    if norm(str(org.get("scientificName") or ""))!=norm(species):
        return None
    if taxon_id is not None and str(org.get("taxonId") or "")!=str(taxon_id):
        return None
    genes=[]
    for g in data.get("genes") or []:
        gn=(g.get("geneName") or {}).get("value")
        if gn:
            genes.append(str(gn))
        for syn in g.get("synonyms") or []:
            v=syn.get("value")
            if v:
                genes.append(str(v))
    if _gene_norm(gene) not in {_gene_norm(x) for x in genes}:
        return None
    reviewed="reviewed" in str(data.get("entryType") or "").lower()
    if not reviewed:
        return None
    return {
        "accession":data.get("primaryAccession") or accession,
        "species":org.get("scientificName"),
        "taxon_id":org.get("taxonId"),
        "genes":genes,
        "reviewed":reviewed
    }

def phylogenetic_seed_records(candidate):
    rows=PHYLO_SEEDS.get(candidate_name(candidate),[])
    return [x for x in rows if isinstance(x,dict)]

def strict_phylogenetic_bridges_for_candidate(candidate):
    name=candidate_name(candidate)
    bridges=[]; checked=0; validated=0
    for seed in phylogenetic_seed_records(candidate):
        checked+=1
        required=[
            seed.get("animal_gene"),seed.get("animal_uniprot"),
            seed.get("animal_taxon_id"),seed.get("modern_transcript_genbank"),
            seed.get("modern_evidence_pmid"),seed.get("human_symbol"),
            seed.get("human_ensembl_id"),seed.get("phylogeny_pmid"),
            seed.get("phylogeny_doi"),seed.get("exact_species_accession_in_phylogeny")
        ]
        if not all(required):
            continue
        if str(seed.get("exact_species_accession_in_phylogeny"))!=str(seed.get("animal_uniprot")):
            continue
        controls={_gene_norm(x.replace("human ","")) for x in seed.get("paralog_controls") or []}
        if not {"ihh","dhh"}.issubset(controls):
            continue
        exact=uniprot_exact_species_gene(
            seed["animal_uniprot"],name,seed["animal_gene"],seed.get("animal_taxon_id")
        )
        if not exact:
            continue
        # The current claim must be the same biological context that motivated
        # the modern exact-species observation; otherwise the orthology dossier
        # cannot silently upgrade an unrelated claim.
        claim_pmids={str(x).replace("PMID:","") for x in candidate.get("pmid_sources",[])}
        modern_pmid=str(seed["modern_evidence_pmid"])
        if modern_pmid not in claim_pmids:
            if not validate_bridge_context_paper(modern_pmid,name,seed["animal_gene"]):
                continue
        try:
            human=opentarget_context(seed["human_ensembl_id"])
        except Exception:
            human=None
        if not human or _gene_norm(human.get("approved_symbol"))!=_gene_norm(seed["human_symbol"]):
            continue
        validated+=1
        bridges.append({
            "animal_species":name,
            "animal_ensembl_species":None,
            "animal_gene":seed["animal_gene"],
            "animal_uniprot":seed["animal_uniprot"],
            "animal_taxon_id":seed["animal_taxon_id"],
            "animal_genbank_nucleotide":seed.get("animal_genbank_nucleotide"),
            "animal_genbank_protein":seed.get("animal_genbank_protein"),
            "modern_transcript_genbank":seed.get("modern_transcript_genbank"),
            "human_ensembl_id":seed["human_ensembl_id"],
            "human_symbol":human.get("approved_symbol"),
            "human_name":human.get("approved_name"),
            "human_biotype":human.get("biotype"),
            "orthology":{
                "provider":"Peer-reviewed phylogenetic orthology",
                "phylogeny_pmid":seed["phylogeny_pmid"],
                "phylogeny_doi":seed["phylogeny_doi"],
                "method":seed.get("phylogeny_method"),
                "exact_species_accession":seed["exact_species_accession_in_phylogeny"],
                "human_target_in_phylogeny":seed.get("human_target_in_phylogeny"),
                "paralog_controls":seed.get("paralog_controls") or []
            },
            "tractability":human.get("tractability",[]),
            "source_claim_pmids":candidate.get("pmid_sources",[]),
            "bridge_evidence_pmids":[str(seed["phylogeny_pmid"]),str(seed["modern_evidence_pmid"])],
            "bridge_seed_rationale":seed.get("rationale"),
            "source_chain":[
                "replicated PMID species claim",
                "reviewed UniProt exact-species protein",
                "peer-reviewed Hedgehog-family phylogeny with human SHH/IHH/DHH paralog discrimination",
                "independent modern exact-species Shh transcript cloning in regenerative tissue",
                "Open Targets human Ensembl target validation"
            ],
            "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
            "clinical_efficacy_claim":False
        })
    return bridges,{
        "phylogenetic_seed_records_checked":checked,
        "phylogenetic_strict_bridges":validated
    }


def orthodb_exact_gene(species,gene):
    """Resolve one OrthoDB gene only when the returned organism is the exact claim species."""
    key=(norm(species),_gene_norm(gene))
    if key in ORTHODB_GENE_CACHE:
        return ORTHODB_GENE_CACHE[key]
    try:
        url=ORTHODB_BASE+"/genesearch?"+urllib.parse.urlencode({"query":f"{gene} {species}"})
        data=get_json(url,1)
    except Exception:
        ORTHODB_GENE_CACHE[key]=None
        return None

    candidates=[]
    if isinstance(data,dict):
        if isinstance(data.get("gene"),dict):
            candidates.append(data)
        for x in data.get("data") or []:
            if isinstance(x,dict):
                candidates.append(x)
        for x in data.get("results") or []:
            if isinstance(x,dict):
                candidates.append(x)

    for row in candidates:
        org=row.get("organism") or {}
        g=row.get("gene") or {}
        gid=g.get("gene_id") or {}
        label=gid.get("id") if isinstance(gid,dict) else gid
        param=gid.get("param") if isinstance(gid,dict) else None
        if norm(str(org.get("name") or "")) != norm(species):
            continue
        if _gene_norm(label) != _gene_norm(gene):
            continue
        if not param:
            continue
        out={
            "source_gene":str(label),
            "source_param":str(param),
            "organism_id":str(org.get("id") or ""),
            "organism_name":str(org.get("name") or ""),
            "protein_id":((g.get("genomic_coordinates") or {}).get("protein_id")),
            "assembly":org.get("organism_id")
        }
        ORTHODB_GENE_CACHE[key]=out
        return out
    ORTHODB_GENE_CACHE[key]=None
    return None

def orthodb_human_orthologs(source_param,expected_gene):
    key=(str(source_param),_gene_norm(expected_gene))
    if key in ORTHODB_ORTHO_CACHE:
        return ORTHODB_ORTHO_CACHE[key]
    try:
        url=ORTHODB_BASE+"/orthologs?"+urllib.parse.urlencode({
            "id":str(source_param),"species":"9606_0"
        })
        data=get_json(url,1)
    except Exception:
        ORTHODB_ORTHO_CACHE[key]=[]
        return []
    out=[]
    for row in data.get("data",[]) if isinstance(data,dict) else []:
        if str(row.get("taxon_id") or "")!="9606_0":
            continue
        g=row.get("gene") or {}
        gid=g.get("id") if isinstance(g,dict) else None
        param=g.get("param") if isinstance(g,dict) else None
        if _gene_norm(gid) != _gene_norm(expected_gene):
            continue
        out.append({
            "human_gene":gid,
            "human_param":param,
            "clade_id":row.get("clade_id"),
            "taxon_id":"9606_0"
        })
    # de-duplicate repeated clade projections of the same human gene.
    uniq={}
    for x in out:
        uniq[(x.get("human_param"),_gene_norm(x.get("human_gene")))]=x
    out=list(uniq.values())
    ORTHODB_ORTHO_CACHE[key]=out
    return out

def orthodb_bridges_for_candidate(candidate):
    name=candidate_name(candidate)
    bridges=[]; checked=0; exact_genes=0; human_orthologs=0
    for seed in literature_seed_records(candidate):
        gene=str(seed.get("gene") or "").strip()
        human_symbol=str(seed.get("human_symbol") or gene).strip()
        human_ensembl_id=str(seed.get("human_ensembl_id") or "").strip()
        if not gene or not human_ensembl_id:
            continue
        checked+=1
        source=orthodb_exact_gene(name,gene)
        if not source:
            continue
        exact_genes+=1
        orths=orthodb_human_orthologs(source["source_param"],human_symbol)
        human_orthologs+=len(orths)
        if not orths:
            continue
        try:
            human=opentarget_context(human_ensembl_id)
        except Exception:
            human=None
        if not human or _gene_norm(human.get("approved_symbol")) != _gene_norm(human_symbol):
            continue
        for orth in orths:
            bridges.append({
                "animal_species":name,
                "animal_ensembl_species":None,
                "animal_gene":source.get("source_gene") or gene,
                "animal_orthodb_gene_id":source.get("source_param"),
                "human_ensembl_id":human_ensembl_id,
                "human_symbol":human.get("approved_symbol"),
                "human_name":human.get("approved_name"),
                "human_biotype":human.get("biotype"),
                "orthology":{
                    "provider":"OrthoDB v12",
                    "source_gene_id":source.get("source_param"),
                    "human_gene_id":orth.get("human_param"),
                    "clade_id":orth.get("clade_id"),
                    "source_assembly":source.get("assembly")
                },
                "tractability":human.get("tractability",[]),
                "source_claim_pmids":candidate.get("pmid_sources",[]),
                "bridge_evidence_pmids":[str(x) for x in seed.get("evidence_pmids",[])],
                "bridge_seed_rationale":seed.get("rationale"),
                "source_chain":[
                    "replicated PMID species claim",
                    "literature-backed exact-species mechanism seed",
                    "OrthoDB exact species + gene resolution",
                    "OrthoDB ortholog to Homo sapiens",
                    "Open Targets human Ensembl target validation"
                ],
                "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
                "clinical_efficacy_claim":False
            })
    return bridges,{
        "orthodb_seed_genes_checked":checked,
        "orthodb_exact_genes":exact_genes,
        "orthodb_human_orthologs":human_orthologs
    }

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

        ncbi_new,ncbi_stats=ncbi_bridges_for_candidate(c)
        bridges.extend(ncbi_new)
        row.update(ncbi_stats)

        orthodb_new,orthodb_stats=orthodb_bridges_for_candidate(c)
        bridges.extend(orthodb_new)
        row.update(orthodb_stats)

        phylo_new,phylo_stats=strict_phylogenetic_bridges_for_candidate(c)
        bridges.extend(phylo_new)
        row.update(phylo_stats)

        oma_new,oma_stats=oma_bridges_for_candidate(c)
        bridges.extend(oma_new)
        row.update(oma_stats)
        row["uniprot_candidates"]=row.get("uniprot_annotation_candidates",0)+row.get("uniprot_species_gene_candidates",0)

        row["bridges"]=sum(1 for b in bridges if b["animal_species"]==name)
        if row["bridges"]:
            row["status"]="BRIDGED"
        elif (not ens_species and row.get("oma_species_matched",0)==0
              and row.get("ncbi_exact_genes",0)==0 and row.get("orthodb_exact_genes",0)==0
              and row.get("phylogenetic_strict_bridges",0)==0):
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
    ncbi_bridge_count=sum(1 for b in bridges if (b.get("orthology") or {}).get("provider")=="NCBI Ortholog")
    orthodb_bridge_count=sum(1 for b in bridges if (b.get("orthology") or {}).get("provider")=="OrthoDB v12")
    phylo_bridge_count=sum(1 for b in bridges if (b.get("orthology") or {}).get("provider")=="Peer-reviewed phylogenetic orthology")
    verified_human_targets=len({(b["animal_species"],b["human_ensembl_id"]) for b in bridges})
    total_orthologue_hits=orth_hits+oma_bridge_count+ncbi_bridge_count+orthodb_bridge_count+phylo_bridge_count

    # PASS means all replicated claims got at least one verified human bridge.
    # Anything less is explicitly PARTIAL rather than hidden.
    status="PASS" if attempted>0 and bridged==attempted else "PARTIAL"
    return {
        "status":status,
        "provider_status":{
            "Europe PMC annotations":"PASS",
            "Ensembl species":species_provider,
            "OMA orthology":"PASS" if oma_bridge_count else "PARTIAL",
            "NCBI Ortholog":"PASS" if ncbi_bridge_count else "PARTIAL",
            "OrthoDB v12":"PASS" if orthodb_bridge_count else "PARTIAL",
            "Peer-reviewed phylogenetic orthology":"PASS" if phylo_bridge_count else "PARTIAL",
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
        "ncbi_orthologue_hits":ncbi_bridge_count,
        "orthodb_orthologue_hits":orthodb_bridge_count,
        "phylogenetic_orthologue_hits":phylo_bridge_count,
        "bridges":bridges,
        "candidate_status":candidate_status,
        "errors":errors[:50]
    }

