#!/usr/bin/env python3
"""Public human fibroblast lifespan multiomic preflight, without dbGaP.

Primary sources:
 - GSE179847 Illumina EPIC beta, 479 samples.
 - GSE179848 RNA-seq, 345 samples.
 - Figshare article 18441998, file 33207965, published metadata CC BY 4.0.
 
Never call a same *donor/culture condition* the same physical aliquot.
Only exact series-matrix normalized assay label overlaps are candidates.
A publicly available reference to a 2 GB methylation matrix != bytes acquired.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

FIG_API="https://api.figshare.com/v2/articles/18441998"
FILE_ID=33207965
GEO={
    "DNA":"https://ftp.ncbi.nlm.nih.gov/geo/series/GSE179nnn/GSE179847/matrix/GSE179847_series_matrix.txt.gz",
    "RNA":"https://ftp.ncbi.nlm.nih.gov/geo/series/GSE179nnn/GSE179848/matrix/GSE179848_series_matrix.txt.gz",
}
SOURCE_LICENSE="CC BY 4.0"

def read_public(url,limit=5_000_000):
    req=urllib.request.Request(url,headers={"User-Agent":"BIO-MIMIC-X/1.1 scientific-public-multiomics/2026","Accept-Encoding":"identity"})
    with urllib.request.urlopen(req,timeout=28) as response:
        if response.status!=200:
            raise RuntimeError(f"unexpected HTTP {response.status}")
        body=response.read(limit+1)
        if len(body)>limit:
            raise ValueError("public source exceeds stated limit")
        return body,response.geturl()

def norm_label(title):
    """Conservative modality-prefix removal only, case-preserving otherwise."""
    s=title.strip().strip('"').replace(" ","_")
    s=re.sub(r"^(?:Methylation|RNAseq|RNA_seq|RNA)_","",s,flags=re.I)
    return s

def read_geo_matrix_metadata(raw:bytes):
    if raw[:2]!=b"\x1f\x8b":raise ValueError("not GEO gzip")
    with gzip.GzipFile(fileobj=io.BytesIO(raw),mode="rb") as f:
        src=f.read(5_000_000).decode("utf-8-sig","strict")
    wanted={"!Sample_title","!Sample_geo_accession"}
    metadata={}
    for line in src.splitlines():
        key=line.split("\t",1)[0]
        if key in wanted:
            cells=next(csv.reader([line],delimiter="\t",quotechar='"'))
            metadata[key]=cells[1:]
    if set(metadata)!=wanted:raise ValueError("required GEO sample columns missing")
    names=metadata["!Sample_title"]
    ids=metadata["!Sample_geo_accession"]
    if len(names)!=len(ids) or not names or len(names)!=len(set(ids)):
        raise ValueError("incomplete or duplicated public GEO sample metadata")
    if not all(re.fullmatch(r"GSM[0-9]+",x) for x in ids):
        raise ValueError("GEO accession IDs invalid")
    return [{"GSM":gsm,"title":name,"join_key":norm_label(name)} for gsm,name in zip(ids,names)]

def join_series(dna,rna):
    """Only join exact normalized culture/time/treatment title; never fabricate."""
    bykey={}
    duplicates=[]
    for d in dna:
        if d["join_key"] in bykey:
            duplicates.append(d["join_key"])
        bykey.setdefault(d["join_key"],[]).append(d)
    if duplicates:raise ValueError(f"ambiguous DNA assay sample labels: {duplicates[:3]}")
    matched=[]
    rna_seen=set()
    for r in rna:
        key=r["join_key"]
        if key in rna_seen:raise ValueError("ambiguous RNA assay sample label "+key)
        rna_seen.add(key)
        if key in bykey:
            d=bykey[key][0]
            matched.append({"join_key":key,"DNA_GSM":d["GSM"],"RNA_GSM":r["GSM"],
                            "same_donor_treatment_and_passage_title":True,
                            "same_physical_aliquot_verified":False})
    return matched

def csv_inspect(blob):
    raw=blob.decode("utf-8-sig","strict")
    line=next((x for x in raw.splitlines() if x.strip()),"")
    if not line:raise ValueError("empty lifespan source")
    sep="\t" if line.count("\t")>line.count(",") else ","
    reader=csv.DictReader(io.StringIO(raw),delimiter=sep)
    if not reader.fieldnames or len(reader.fieldnames)<2:
        raise ValueError("Figshare CSV has no usable data header")
    count=0
    preview=[]
    for row in reader:
        if count<3:preview.append({key:(row.get(key) or "")[:100] for key in reader.fieldnames[:9]})
        count+=1
    columns=reader.fieldnames
    if count<10:raise ValueError("implausibly few lifespan entries")
    interesting=[key for key in columns if re.search(r"RNA|gene|DNAm|meth|age|pass|doubl|donor|sex|cell|treat|time|culture|condition",key,re.I)]
    return {"rows":count,"columns":len(columns),"column_names":columns,
            "aging_or_multiomic_columns":interesting,"first_three_rows_subset":preview,
            "real_transcriptomic_gene_matrix":False,
            "real_methylation_beta_matrix":False}

def main():
    output={"schema":"BIO-MIMIC-X/GSE179849-PUBLIC-LONGITUDINAL-MULTIOMICS-PREFLIGHT/1",
        "GEO_super_series":"GSE179849",
        "RNA_series":"GSE179848","DNA_series":"GSE179847",
        "RNA_claimed_public_samples":345,"DNA_claimed_public_samples":479,
        "study_context":"cellular replicative aging in primary human fibroblasts",
        "RNA_protected_dbGaP_data_obtained":False,
        "RNA_matrix_obtained":False,"DNA_matrix_obtained":False,
        "paired_numeric_assay_observation_obtained":False,
        "aging_RNA_identity_adjusted_effect":"UNVERIFIED",
        "checks":{},"status":"PARTIAL"}
    try:
        fig,real_url=read_public(FIG_API,100_000)
        meta=json.loads(fig)
        if meta.get("id")!=18441998 or not meta.get("is_public") or meta["license"]["name"]!=SOURCE_LICENSE:
            raise ValueError("unexpected license or public publication status")
        entry=next(x for x in meta["files"] if x["id"]==FILE_ID)
        if not 1000 < entry["size"] < 5_000_000:
            raise ValueError("not expected small public figshare file")
        output["checks"]["figshare_article"]={"status":"PASS_OFFICIAL_PUBLIC_METADATA",
          "doi":meta.get("doi"),"license":meta["license"]["name"],
          "file_id":FILE_ID,"file_size_bytes":entry["size"],
          "official_md5":entry.get("computed_md5"),"actual_download_url":entry["download_url"]}
        raw,verified_url=read_public(entry["download_url"],5_000_000)
        md5=hashlib.md5(raw).hexdigest()
        if len(raw)!=entry["size"] or md5!=entry.get("computed_md5"):
            raise ValueError("Figshare checksum and file-size mismatch")
        output["checks"]["figshare_actual_data"]={
           "status":"PASS_ACTUAL_CCBY_DATA_ACQUIRED_MD5_VERIFIED",
           "size_bytes":len(raw),"md5":md5,"sha256":hashlib.sha256(raw).hexdigest(),
           "source_url":verified_url,**csv_inspect(raw)}
    except Exception as exc:
        output["checks"]["figshare_actual_data"]={"status":"PARTIAL_OR_FAIL_SOURCE",
            "error":f"{type(exc).__name__}: {exc}"[:220]}
    matrix={}
    for kind,url in GEO.items():
        try:
            raw,final=read_public(url,3_000_000)
            samples=read_geo_matrix_metadata(raw)
            output["checks"]["GEO_"+kind]={"status":"PASS_PUBLIC_METADATA_ACQUIRED",
                "sha256":hashlib.sha256(raw).hexdigest(),"total":len(samples),
                "source":final,"first_samples":samples[:3]}
            matrix[kind]=samples
        except Exception as exc:
            output["checks"]["GEO_"+kind]={"status":"PARTIAL_GEO_TRANSPORT",
                "source":url,"error":f"{type(exc).__name__}: {exc}"[:180]}
    if len(matrix)==2:
        paired=join_series(matrix["DNA"],matrix["RNA"])
        output["candidate_matching_keys"]=paired
        output["candidate_exact_title_pair_count"]=len(paired)
        output["status"]="PASS_PUBLIC_SAME_CONDITION_RNA_DNAM_METADATA" if paired else "PARTIAL_ZERO_EXACT_KEYS"
    if output["checks"].get("figshare_actual_data",{}).get("status","").startswith("PASS"):
        if output["status"]=="PARTIAL":
            output["status"]="PASS_LIFESPAN_CCBY_COMPACT_SOURCE_ONLY"
    out=Path("qa-artifacts/GSE179849-PUBLIC-OPEN-MULTIOMICS-PREFLIGHT.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(output,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    compact={k:v for k,v in output.items() if k not in ("candidate_matching_keys",)}
    print("BIO_MIMIC_LIFESPAN_GSE179849_SOURCE_AUDIT "+json.dumps(compact,ensure_ascii=False)[:7500])
    print("BIO_MIMIC_LIFESPAN_PAIRS "+json.dumps(output.get("candidate_matching_keys",[])[:12])[:2500])
    if not output["status"].startswith("PASS"):raise SystemExit(2)

if __name__=="__main__":main()
