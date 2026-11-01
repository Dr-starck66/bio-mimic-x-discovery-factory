#!/usr/bin/env python3
"""BIO-MIMIC X: verify whether public sequence resources can resolve the
historical HAND1/HAND2 axolotl annotation. No inferred crosswalk is promoted.
Read-only API requests, bounded payloads and strict sequence provenance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]/"reports/factory/HAND2-ASSEMBLY-SEQUENCE-PROBE-LATEST.json"
LEGACY={"assembly":"GCA_002915635.3","gene":"AMEX60DD030069","chrom":"chr3q",
        "start_1based":632140538,"end_1based":632169448}
GENE_ID="138516365"
USER_AGENT="BIO-MIMIC-X-HAND2-readonly/1.0 research-provenance"
BASE="https://api.ncbi.nlm.nih.gov/datasets/v2"
HUB="https://ambystoma.uky.edu/hubExamples/hubAssembly/hub_AmexG_v6/hub.txt"
UCSC="https://api.genome.ucsc.edu/getData/sequence"
UCSC_QUERY={"hubUrl":HUB,"genome":"AmexG.v6-DD",
            "chrom":LEGACY["chrom"],
            "start":LEGACY["start_1based"]-1,
            "end":LEGACY["start_1based"]+499}

URLS={
    "ncbi_gene_report":f"{BASE}/gene/id/{GENE_ID}/dataset_report",
    "ncbi_old_assembly_report":f"{BASE}/genome/accession/{LEGACY['assembly']}/dataset_report",
    "ncbi_gene_xml":"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
                    +urllib.parse.urlencode({"db":"gene","id":GENE_ID,"retmode":"xml"}),
    "ucsc_old_assembly_window":UCSC+"?"+urllib.parse.urlencode(UCSC_QUERY),
}

def bounded_get(url:str,maxbytes:int=3_000_000)->tuple[bytes,dict]:
    req=urllib.request.Request(url,headers={"Accept":"application/json, application/xml, text/plain",
                                          "User-Agent":USER_AGENT})
    with urllib.request.urlopen(req,timeout=25) as r:
        data=r.read(maxbytes+1)
        ct=r.headers.get("Content-Type","")
    if len(data)>maxbytes:
        raise ValueError("source exceeded request size cap")
    if not data or data.startswith((b"<html",b"<!DOCTYPE html")):
        raise ValueError("empty or HTML error payload")
    return data,{"source":url,"size":len(data),"sha256":hashlib.sha256(data).hexdigest(),"content_type":ct}

def _string_matches(obj,terms=("chromosome","genome","assembly","accession","location","reference","gene_id","symbol")):
    """Return diagnostic keys only, do not interpret text as identity proof."""
    found=[]
    def rec(x,path="",depth=0):
        if len(found)>=32 or depth>7:return
        if isinstance(x,dict):
            for k,v in x.items():
                newpath=path+"."+str(k)
                if any(t in str(k).lower() for t in terms):
                    ss=json.dumps(v,ensure_ascii=False,default=str)[:500]
                    found.append({"key":newpath,"preview":ss})
                rec(v,newpath,depth+1)
        elif isinstance(x,list):
            for i,v in enumerate(x[:5]):rec(v,path+"["+str(i)+"]",depth+1)
    rec(obj)
    return found[:32]

def parse_ncbi_gene_report(data:bytes)->dict:
    j=json.loads(data)
    arr=j.get("reports") or []
    if not arr: return {"status":"NO_GENE_REPORT","annotations":[]}
    item=arr[0]
    gene=(item.get("gene") or {})
    return {"status":"REPORT_FOUND",
            "reported_gene_id":str(gene.get("gene_id") or ""),
            "reported_symbol":gene.get("symbol"),
            "reported_taxon":gene.get("tax_id"),
            "selected_annotations":_string_matches(item)}

def parse_old_assembly_report(data:bytes)->dict:
    j=json.loads(data)
    arr=j.get("reports") or []
    if not arr: return {"status":"NO_ASSEMBLY_REPORT","annotations":[]}
    obj=arr[0]
    return {"status":"ASSEMBLY_REPORT_FOUND","selected_annotations":_string_matches(obj)}

def parse_ncbi_gene_xml(data:bytes)->dict:
    root=ET.fromstring(data)
    accessions=[]
    intervals=[]
    for ele in root.iter("Gene-commentary"):
        acc=ele.findtext("Gene-commentary_accession")
        version=ele.findtext("Gene-commentary_version")
        if acc and len(accessions)<80:
            accessions.append((acc+("." + version if version else "")))
    for item in root.iter("Seq-interval"):
        acc=item.findtext("Seq-interval_id/Seq-id/Seq-id_other/Textseq-id/Textseq-id_accession")
        first=item.findtext("Seq-interval_from")
        last=item.findtext("Seq-interval_to")
        if first and last and len(intervals)<40:
            intervals.append({"accession":acc,"start_0based":first,"end_0based":last})
    return {"status":"XML_PARSED","accessions":list(dict.fromkeys(accessions))[:65],
            "intervals":intervals[:40]}

def parse_ucsc_window(data:bytes)->dict:
    j=json.loads(data)
    bases=str(j.get("dna") or j.get("sequence") or "")
    if not bases or not re.fullmatch("[ACGTNacgtn]+",bases):
        return {"status":"NO_VALID_SEQUENCE","message":str(j.get("error") or j.get("status") or "")[:250]}
    if len(bases)>500:
        raise ValueError("unexpected sequence length from UCSC")
    return {"status":"OLD_GENOME_WINDOW_FETCHED",
            "base_count":len(bases),"sequence_sha256":hashlib.sha256(bases.upper().encode()).hexdigest(),
            "sequence_first_30":bases[:30],"source_assembly":LEGACY["assembly"],
            "note":"Local old assembly sequence only, not aligned to modern NCBI gene."}

def build_probe(replies:dict,errors:dict)->dict:
    details={}
    parsers={"ncbi_gene_report":parse_ncbi_gene_report,
             "ncbi_old_assembly_report":parse_old_assembly_report,
             "ncbi_gene_xml":parse_ncbi_gene_xml,
             "ucsc_old_assembly_window":parse_ucsc_window}
    for k,(body,meta) in replies.items():
        try:details[k]={"download":meta,"parsed":parsers[k](body)}
        except Exception as e:errors[k+" parse"]=type(e).__name__+": "+str(e)[:200]
    return {
        "schema":"BIO-MIMIC-X/HAND2-ASSEMBLY-SEQUENCE-PROBE/1",
        "legacy_locus":LEGACY,"ncbi_gene_id":GENE_ID,"resources":details,"failures":errors,
        "old_locus_to_modern_gene_exact_sequence_identity":"UNVERIFIED",
        "why_unverified":"This is a provenance probe. It does not perform a reciprocal sequence alignment, paralog exclusion or a whole-genome locus-unique mapping.",
        "possible_next_step":"If genomic accessions and both sequence windows are available, run reciprocal HAND1/HAND2 sequence alignment with assembly coordinates.",
        "no_human_regeneration_claim":True,
        "status":"PARTIAL" if details else "UNVERIFIED",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args()
    replies={};errors={}
    for name,url in URLS.items():
        try:replies[name]=bounded_get(url)
        except Exception as e:errors[name]=type(e).__name__+": "+str(e)[:250]
    out=build_probe(replies,errors)
    canon=json.dumps(out,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    out["sha256"]=hashlib.sha256(canon.encode()).hexdigest()
    print("HAND2_SEQUENCE_PROBE "+json.dumps(out,ensure_ascii=False,sort_keys=True))
    if args.write:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
