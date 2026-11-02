#!/usr/bin/env python3
"""Probe actual public GSE179848 RNA gene-abundance file headers, not proxy QC.
Read only bounded range 0-131071; fail closed on HTTP403, record negatives.
"""
import json
import urllib.request
import urllib.error
import zlib
from pathlib import Path
from validation.gse179849_public_multimodal_gate import norm_label

BASE="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE179nnn/GSE179848/suppl/"
FILES=("GSE179848_txi_gene_abundance.csv.gz",
       "GSE179848_processed_cell_lifespan_RNAseq_data.csv.gz")
def probe(name):
    url=BASE+name
    req=urllib.request.Request(url,headers={
        "User-Agent":"BIO-MIMIC-X-public-research","Range":"bytes=0-131071",
        "Accept-Encoding":"identity"})
    try:
        with urllib.request.urlopen(req,timeout=22) as res:
            data=res.read(131072)
            if res.status!=206 or not res.headers.get("Content-Range","").startswith("bytes 0-"):
                raise ValueError("Source did not honor HTTP206 byte range")
            if data[:2]!=b"\x1f\x8b":raise ValueError("Source is not gzip")
            first=zlib.decompressobj(31).decompress(data).decode("utf-8-sig",errors="replace").splitlines()[0]
            comma=first.split(",")
            tab=first.split("\t")
            delimiter="comma" if len(comma)>len(tab) else "tab"
            fields=comma if delimiter=="comma" else tab
            return {"status":"PASS_OFFICIAL_GZIP_RNA_HEADER_ONLY","source":url,
                    "content_range":res.headers.get("Content-Range"),
                    "field_count":len(fields),
                    "header_first_8":fields[:8],
                    "header_last_5":fields[-5:],
                    "part_of_gene_matrix":True,
                    "full_gene_expression_matrix_acquired":False}
    except Exception as e:
        return {"status":"PARTIAL_OFFICIAL_RNA_SOURCE_UNAVAILABLE","source":url,
                "reason":f"{type(e).__name__}: {str(e)[:240]}",
                "full_gene_expression_matrix_acquired":False}

if __name__=="__main__":
    out={"study":"GSE179849","RNA_series":"GSE179848",
         "results":[probe(filename) for filename in FILES],
         "RNA_gene_values_acquired":False,
         "RNA_identity_adjusted_aging":"UNVERIFIED",
         "overall_status":"PARTIAL_SOURCE_HEADER_ONLY"}
    path=Path("qa-artifacts/GSE179848-PUBLIC-RNA-GENE-HEADER-ACCESS.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out,indent=2),encoding="utf8")
    print("BIO_MIMIC_RNA_SOURCE_HEADERS "+json.dumps(out)[:3500])
