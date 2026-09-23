#!/usr/bin/env python3
from __future__ import annotations
import json, re, urllib.parse
from pathlib import Path

from human_bridge import get_json, opentarget_context, norm

EPMC="https://www.ebi.ac.uk/europepmc/webservices/rest/search"
UNIPROT="https://rest.uniprot.org/uniprotkb"
SEED_PATH=Path(__file__).with_name("translation_path_seeds.json")
try:
    TRANSLATION_SEEDS=json.loads(SEED_PATH.read_text(encoding="utf-8")).get("species",{})
except Exception:
    TRANSLATION_SEEDS={}

PMID_CACHE={}
UNIPROT_CACHE={}

def pubmed_record(pmid):
    pmid=str(pmid).replace("PMID:","").strip()
    if pmid in PMID_CACHE:
        return PMID_CACHE[pmid]
    try:
        url=EPMC+"?"+urllib.parse.urlencode({
            "query":f"EXT_ID:{pmid} AND SRC:MED",
            "format":"json","resultType":"core","pageSize":"1"
        })
        data=get_json(url,1)
        rows=(data.get("resultList") or {}).get("result") or []
        rec=rows[0] if rows else None
    except Exception:
        rec=None
    PMID_CACHE[pmid]=rec
    return rec

def record_text(rec):
    if not rec:
        return ""
    return norm(" ".join(str(rec.get(k) or "") for k in ("title","abstractText","authorString","journalTitle")))

def validate_pmids(pmids, required_any=None):
    records=[]
    for pmid in pmids or []:
        rec=pubmed_record(pmid)
        if not rec:
            return False,[],f"PMID {pmid} unavailable"
        records.append({"pmid":str(pmid).replace("PMID:",""),"title":rec.get("title")})
    if required_any:
        text=" ".join(record_text(pubmed_record(x)) for x in pmids or [])
        if not any(norm(term) in text for term in required_any):
            return False,records,"required evidence terms absent"
    return True,records,None

def uniprot_entry(accession):
    if accession in UNIPROT_CACHE:
        return UNIPROT_CACHE[accession]
    try:
        data=get_json(f"{UNIPROT}/{urllib.parse.quote(accession)}.json",1)
    except Exception:
        data=None
    UNIPROT_CACHE[accession]=data
    return data

def uniprot_gene_names(entry):
    out=[]
    for g in (entry or {}).get("genes") or []:
        gn=(g.get("geneName") or {}).get("value")
        if gn: out.append(str(gn))
        for s in g.get("synonyms") or []:
            if s.get("value"): out.append(str(s["value"]))
    return out

def validate_target(ensembl_id,expected_symbol):
    try:
        t=opentarget_context(ensembl_id)
    except Exception:
        t=None
    if not t:
        return None
    if norm(t.get("approved_symbol"))!=norm(expected_symbol):
        return None
    return t

def validate_sequence_homology(subject,seed):
    ok,animal_records,err=validate_pmids(seed.get("animal_evidence_pmids"),["acomys","il10","regeneration"])
    if not ok:
        return None,err
    similarity=float(seed.get("human_similarity_pct") or 0)
    if similarity<=0 or similarity>100:
        return None,"invalid literature similarity"
    target=validate_target(seed.get("human_ensembl_id"),seed.get("human_symbol"))
    if not target:
        return None,"Open Targets human target mismatch/unavailable"
    return {
        "subject":subject,
        "status":"VERIFIED",
        "path_type":"LITERATURE_SEQUENCE_HOMOLOGY",
        "animal_feature":seed.get("animal_feature"),
        "human_symbol":target.get("approved_symbol"),
        "human_ensembl_id":seed.get("human_ensembl_id"),
        "human_name":target.get("approved_name"),
        "human_similarity_pct":similarity,
        "evidence_locator":seed.get("evidence_locator"),
        "animal_evidence":animal_records,
        "source_chain":[
            "replicated species claim",
            "exact-species regeneration literature",
            "published cross-species peptide comparison",
            "Open Targets human target validation"
        ],
        "caveat":seed.get("caveat"),
        "clinical_efficacy_claim":False
    },None

def validate_curated_protein_homology(subject,seed):
    ok,records,err=validate_pmids(seed.get("animal_evidence_pmids"),["cynops","shh","regeneration"])
    if not ok:
        return None,err
    animal=uniprot_entry(seed.get("animal_uniprot"))
    human=uniprot_entry(seed.get("human_uniprot"))
    if not animal or not human:
        return None,"UniProt entry unavailable"
    animal_org=((animal.get("organism") or {}).get("scientificName") or "")
    human_org=((human.get("organism") or {}).get("scientificName") or "")
    if norm(animal_org)!=norm(subject) or norm(human_org)!="homo sapiens":
        return None,"UniProt species mismatch"
    expected=seed.get("human_symbol")
    if not any(norm(x)==norm(expected) for x in uniprot_gene_names(animal)):
        return None,"animal UniProt gene mismatch"
    if not any(norm(x)==norm(expected) for x in uniprot_gene_names(human)):
        return None,"human UniProt gene mismatch"
    target=validate_target(seed.get("human_ensembl_id"),expected)
    if not target:
        return None,"Open Targets human target mismatch/unavailable"
    return {
        "subject":subject,
        "status":"VERIFIED",
        "path_type":"CURATED_PROTEIN_HOMOLOGY",
        "animal_feature":seed.get("animal_feature"),
        "animal_uniprot":seed.get("animal_uniprot"),
        "human_uniprot":seed.get("human_uniprot"),
        "human_symbol":target.get("approved_symbol"),
        "human_ensembl_id":seed.get("human_ensembl_id"),
        "human_name":target.get("approved_name"),
        "animal_evidence":records,
        "source_chain":[
            "replicated species claim",
            "regeneration PMID",
            "reviewed exact-species UniProt protein/gene",
            "reviewed human UniProt same-gene protein",
            "Open Targets human target validation"
        ],
        "caveat":seed.get("caveat"),
        "clinical_efficacy_claim":False
    },None

def validate_functional_intervention(subject,seed):
    kind=seed.get("path_type")
    if kind=="FUNCTIONAL_CRYOPRESERVATION_INTERVENTION":
        animal_terms=["paracentrotus","cryopreservation","trehalose","dimethyl sulfoxide","dmso"]
        human_terms=["human","cryopreservation","trehalose","dmso"]
    else:
        animal_terms=["caenorhabditis","ice binding","antifreeze","cryoprote"]
        human_terms=["human","antifreeze","cryopreservation","ice recrystallization"]
    aok,arecs,aerr=validate_pmids(seed.get("animal_evidence_pmids"),animal_terms)
    if not aok:
        return None,aerr
    hok,hrecs,herr=validate_pmids(seed.get("human_evidence_pmids"),human_terms)
    if not hok:
        return None,herr
    return {
        "subject":subject,
        "status":"VERIFIED",
        "path_type":kind,
        "intervention":seed.get("intervention"),
        "animal_evidence":arecs,
        "human_evidence":hrecs,
        "human_symbol":None,
        "human_ensembl_id":None,
        "source_chain":[
            "replicated species claim",
            "species-specific intervention evidence",
            "independent human-biomedical cryopreservation evidence"
        ],
        "caveat":seed.get("caveat"),
        "clinical_efficacy_claim":False
    },None

def validate_fallback(subject,seed):
    kind=seed.get("path_type")
    if kind=="LITERATURE_SEQUENCE_HOMOLOGY":
        return validate_sequence_homology(subject,seed)
    if kind=="CURATED_PROTEIN_HOMOLOGY":
        return validate_curated_protein_homology(subject,seed)
    if kind in {"FUNCTIONAL_CRYOPRESERVATION_INTERVENTION","FUNCTIONAL_ICE_BINDING_PROTEIN_INTERVENTION"}:
        return validate_functional_intervention(subject,seed)
    return None,f"unsupported path type {kind}"

def build_translation_paths(claims,strict_result):
    strict_by_subject={}
    for b in strict_result.get("bridges",[]):
        strict_by_subject.setdefault(b.get("animal_species"),[]).append(b)

    paths=[]; candidate_status=[]; errors=[]
    for claim in claims:
        subject=claim.get("subject")
        strict=strict_by_subject.get(subject,[])
        if strict:
            paths.append({
                "subject":subject,
                "status":"VERIFIED",
                "path_type":"STRICT_ORTHOLOGY_TARGET",
                "strict_bridge_count":len(strict),
                "bridges":strict,
                "source_chain":["provider-verified animal-to-human orthology","Open Targets human target validation"],
                "clinical_efficacy_claim":False
            })
            candidate_status.append({"candidate":subject,"status":"VERIFIED","path_type":"STRICT_ORTHOLOGY_TARGET"})
            continue

        seed=TRANSLATION_SEEDS.get(subject)
        if not seed:
            candidate_status.append({"candidate":subject,"status":"NO_TRANSLATION_PATH","path_type":None})
            errors.append({"candidate":subject,"error":"no typed fallback translation seed"})
            continue

        path,err=validate_fallback(subject,seed)
        if path:
            paths.append(path)
            candidate_status.append({"candidate":subject,"status":"VERIFIED","path_type":path["path_type"]})
        else:
            candidate_status.append({"candidate":subject,"status":"UNVERIFIED","path_type":seed.get("path_type"),"reason":err})
            errors.append({"candidate":subject,"error":err})

    attempted=len(claims)
    verified_subjects={x["subject"] for x in paths if x.get("status")=="VERIFIED"}
    strict_subjects={x["subject"] for x in paths if x.get("path_type")=="STRICT_ORTHOLOGY_TARGET"}
    types={}
    for x in paths:
        types[x["path_type"]]=types.get(x["path_type"],0)+1
    verified=len(verified_subjects)
    strict=len(strict_subjects)
    return {
        "status":"PASS" if attempted and verified==attempted else "PARTIAL",
        "attempted_candidates":attempted,
        "translation_verified_candidates":verified,
        "translation_coverage_ratio":round(verified/max(1,attempted),4),
        "strict_orthology_candidates":strict,
        "strict_orthology_coverage_ratio":round(strict/max(1,attempted),4),
        "fallback_verified_candidates":verified-strict,
        "path_type_counts":types,
        "paths":paths,
        "candidate_status":candidate_status,
        "errors":errors
    }
