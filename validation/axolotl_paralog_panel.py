#!/usr/bin/env python3
"""Independent-source, multi-family axolotl historical-locus screen.

PREDECLARED panel: HAND1/HAND2, PAX6/PAX7, SOX2/SOX3, SHH/DHH.
The public historical GTF, old assembly report, NCBI annotations and FASTA
are used as data. All missing, disputed, negative and failed cases are retained.

This is NOT a genome-wide reciprocal alignment, external validation, or an
estimate of error reduction in a representative industrial sample.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import re
import time
from pathlib import Path
from typing import Mapping

try:
    from validation.hand2_assembly_sequence_probe import (
        bounded_get, fasta_from_ncbi, reverse_complement)
    from validation.hand1_hand2_global_alignment import align_window
    from validation.hand2_legacy_crosswalk import GTF_URL, EXPECTED_GTF_SHA256
except ModuleNotFoundError:
    from hand2_assembly_sequence_probe import bounded_get,fasta_from_ncbi,reverse_complement
    from hand1_hand2_global_alignment import align_window
    from hand2_legacy_crosswalk import GTF_URL,EXPECTED_GTF_SHA256

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports/factory/AXOLOTL-PARALOG-PANEL-LATEST.json"
ASSEMBLY_URL="https://hgdownload.soe.ucsc.edu/hubs/GCA/002/915/635/GCA_002915635.3/GCA_002915635.3_assembly_report.txt"
ASSEMBLY_SHA="afab332ee6420dd92d50fc7cd21fdee39595ba57646561e7904887932243a0be"
FAMILIES=(("HAND1","HAND2"),("PAX6","PAX7"),("SOX2","SOX3"),("SHH","DHH"))
TARGETS={g for pair in FAMILIES for g in pair}
MAX_SPAN=40000
MIN_SPAN=250
ASSEMBLY="GCF_040938575.1"
TAG_RE=re.compile(r"([A-Za-z0-9-]+)\s*\[(hs|nr)\]",re.I)

def parse_gene_rows(gtf:bytes):
    """Use only full gene features; reject ambiguous symbol-to-gene mappings."""
    if hashlib.sha256(gtf).hexdigest()!=EXPECTED_GTF_SHA256:
        raise ValueError("historic GTF SHA mismatch")
    hits={g:[] for g in sorted(TARGETS)}
    with gzip.GzipFile(fileobj=io.BytesIO(gtf)) as source:
        for line in source:
            if line.startswith(b"#"):continue
            fields=line.decode("utf-8",errors="replace").rstrip("\n").split("\t")
            if len(fields)<9 or fields[2]!="gene":continue
            name=re.search(r'gene_name "([^"]+)"',fields[8])
            gid=re.search(r'gene_id "([^"]+)"',fields[8])
            if not name or not gid:continue
            labels={v.upper() for v,_ in TAG_RE.findall(name.group(1))}
            names=labels & TARGETS
            if not names:continue
            record={
                "legacy_gene_id":gid.group(1),"chr":fields[0],
                "start_1based":int(fields[3]),"end_1based":int(fields[4]),
                "strand":fields[6],"historical_name":name.group(1),
                "species_tagged_symbols":sorted(labels),
                "length":int(fields[4])-int(fields[3])+1,
            }
            for symbol in names:hits[symbol].append(record)
    return {g:sorted(rows,key=lambda x:x["legacy_gene_id"]) for g,rows in hits.items()}

def parse_old_assembly_mapping(data:bytes):
    if hashlib.sha256(data).hexdigest()!=ASSEMBLY_SHA:
        raise ValueError("old assembly mapping file SHA mismatch")
    mappings={}
    for line in data.decode("utf-8").splitlines():
        if line.startswith("#"):continue
        cols=line.split("\t")
        if len(cols)>=9 and cols[3]=="Chromosome":
            mappings[cols[0]]=cols[4]
    return mappings

def parse_current_gene(data:bytes,expected:str):
    j=json.loads(data)
    reports=j.get("reports") or []
    valid=[]
    for r in reports:
        g=r.get("gene") or {}
        if (str(g.get("symbol") or "").upper()!=expected or
            str(g.get("tax_id"))!="8296"):continue
        for a in g.get("annotations") or []:
            if a.get("assembly_accession")!=ASSEMBLY:continue
            for loc in a.get("genomic_locations") or []:
                rg=loc.get("genomic_range") or {}
                accession=loc.get("genomic_accession_version")
                try: start,end=int(rg["begin"]),int(rg["end"])
                except (KeyError,ValueError,TypeError):continue
                if accession and re.fullmatch(r"NC_\d+\.\d+",str(accession)) and start<=end:
                    valid.append({"symbol":expected,"gene_id":str(g["gene_id"]),
                        "accession":accession,"start":start,"end":end,
                        "length":end-start+1})
    if len(valid)!=1:
        raise ValueError("No unique NCBI current gene on exact modern assembly: "+expected)
    return valid[0]

def make_preflight(hits,mapping):
    """Predeclared inclusion; don't pick the best-scoring gene after inspection."""
    cases=[]
    for a,b in FAMILIES:
        for symbol,competitor in ((a,b),(b,a)):
            matches=hits[symbol]
            status="ELIGIBLE"
            row=None
            if len(matches)!=1:status="AMBIGUOUS_LEGACY_GENE_COUNT"
            else:
                row=matches[0]
                if not MIN_SPAN<=row["length"]<=MAX_SPAN:status="WINDOW_OUTSIDE_BOUNDS"
                elif row["chr"] not in mapping:status="NO_VERIFIED_OLD_CHR_ACCESSION"
                elif mapping[row["chr"]]=="na":status="NO_GENBANK_CHR_ACCESSION"
            cases.append({
                "symbol":symbol,"paralog":competitor,
                "historical_gene_candidates":len(matches),
                "status":status,"historical":row,
                "old_genbank_accession":mapping.get(row["chr"]) if row else None,
            })
    return cases

def score_old_against_candidates(old,seqs,edlib):
    result={}
    for symbol,modern in seqs.items():
        best=align_window(modern,old,edlib)["best"]
        result[symbol]={
            "edit_distance":best["edit_distance"],
            "aligned_identical_bases":best["counts"]["="],
            "aligned_columns":best["aligned_columns"],
            "identity_in_aligned_columns":best["fraction_matching_in_alignment"],
            "query_length":best["query_bases"],
            "length_normalized_edit_distance":round(best["edit_distance"]/best["query_bases"],6),
            "strand":best["strand"],
            "CIGAR_counts":best["counts"],
        }
    return result

def compare_scores(original,paralog,metrics):
    a=metrics[original];b=metrics[paralog]
    # Lower edit distance per query base wins, only with a LARGE margin
    # and a meaningful match. This is a screening rule, not biological truth.
    ea=a["length_normalized_edit_distance"]
    eb=b["length_normalized_edit_distance"]
    if min(ea,eb)>0.08 or abs(ea-eb)<0.20:
        return "INCONCLUSIVE"
    return "FAVORS_ORIGINAL" if ea<eb else "FAVORS_PARALOG"

def run_panel():
    out={
        "schema":"BIO-MIMIC-X/PARALOG-PANEL/1",
        "predeclared_families":FAMILIES,
        "status":"UNVERIFIED",
        "limitations":[
            "Preselected symbol families, not a representative genome-wide benchmark.",
            "Legacy labels may be ambiguous and are not gold-standard identities.",
            "No label-only accuracy or industrial false-positive rate can be estimated without independent truth.",
            "Whole-genome reciprocal mapping, paralog synteny, exon mapping and independent curator review missing.",
            "No clinical efficacy or monetary ROI is inferred.",
        ],
        "strict_source_shas":{"legacy_GTF":EXPECTED_GTF_SHA256,"legacy_assembly_report":ASSEMBLY_SHA},
        "cases":[],"source_failures":{},
    }
    try:
        gtf,_=bounded_get(GTF_URL,60_000_000)
        hits=parse_gene_rows(gtf)
        raw,_=bounded_get(ASSEMBLY_URL,3_000_000)
        mapping=parse_old_assembly_mapping(raw)
    except Exception as ex:
        out["status"]="PARTIAL_SOURCE_FAILURE"
        out["source_failures"]["preflight"]=type(ex).__name__+": "+str(ex)[:220]
        return out

    cases=make_preflight(hits,mapping)
    out["cases"]=cases
    eligible=[x for x in cases if x["status"]=="ELIGIBLE"]
    if not eligible:
        out["status"]="UNVERIFIED_NO_ELIGIBLE_HISTORIC_LOCUS"
        return out
    # Only request official modern genes for eligible cases. All failures retained.
    genes={}
    for sym in sorted({x["symbol"] for x in eligible}|{x["paralog"] for x in eligible}):
        try:
            url=f"https://api.ncbi.nlm.nih.gov/datasets/v2/gene/symbol/{sym}/taxon/8296/dataset_report"
            payload,receipt=bounded_get(url,400_000)
            gene=parse_current_gene(payload,sym)
            if not MIN_SPAN<=gene["length"]<=MAX_SPAN:
                raise ValueError("modern gene length outside prespecified 250-40000 bp")
            dna,seqreceipt=fasta_from_ncbi(gene["accession"],gene["start"],gene["end"])
            genes[sym]={"gene":gene,"dna":dna,"sequence_sha256":hashlib.sha256(dna.encode()).hexdigest(),
                        "gene_report":receipt,"fasta":seqreceipt}
        except Exception as ex:
            out["source_failures"]["modern:"+sym]=type(ex).__name__+": "+str(ex)[:220]
        time.sleep(0.33)
    import edlib
    for case in eligible:
        sym=case["symbol"];competitor=case["paralog"]
        if sym not in genes or competitor not in genes:
            case["status"]="PARTIAL_MODERN_SOURCE_MISSING"
            continue
        row=case["historical"]
        try:
            dna,receipt=fasta_from_ncbi(case["old_genbank_accession"],row["start_1based"],row["end_1based"])
            scores=score_old_against_candidates(dna,{sym:genes[sym]["dna"],competitor:genes[competitor]["dna"]},edlib)
            case["status"]="PARTIAL_ALIGNMENT_COMPUTED"
            case["old_fasta"]=receipt
            case["old_sequence_sha256"]=hashlib.sha256(dna.encode()).hexdigest()
            case["modern_references"]={
                key:{p:v for p,v in genes[key].items() if p!="dna"}
                for key in (sym,competitor)
            }
            case["scores"]=scores
            case["screening_inference"]=compare_scores(sym,competitor,scores)
            case["identity_certified"]=False
        except Exception as ex:
            case["status"]="PARTIAL_ALIGNMENT_SOURCE_FAILURE"
            out["source_failures"]["case:"+sym]=type(ex).__name__+": "+str(ex)[:220]
        time.sleep(0.33)
    count=sum(x["status"]=="PARTIAL_ALIGNMENT_COMPUTED" for x in cases)
    out["evaluated_loci"]=count
    out["attempted_loci"]=len(eligible)
    out["status"]="PARTIAL_SCREENED_NONREPRESENTATIVE" if count else "PARTIAL_NO_REAL_ALIGNMENT"
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args()
    try: out=run_panel()
    except Exception as ex:
        out={"schema":"BIO-MIMIC-X/PARALOG-PANEL/1","status":"FAIL_IMPLEMENTATION",
             "error":type(ex).__name__+": "+str(ex)[:220]}
    out["scientific_identity_confirmation"]="UNVERIFIED"
    canon=json.dumps(out,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    out["sha256"]=hashlib.sha256(canon.encode()).hexdigest()
    print("AXOLOTL_PARALOG_PANEL "+json.dumps(out,sort_keys=True,ensure_ascii=False))
    if args.write:
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    return 1 if out["status"]=="FAIL_IMPLEMENTATION" else 0

if __name__=="__main__":raise SystemExit(main())
