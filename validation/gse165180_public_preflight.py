#!/usr/bin/env python3
"""Preflight public Gill 2022 MPTR GEO RNA/DNAm correspondence without downloading 530 MB.

All downloads strictly GEO public HTTPS. No external credentials, no dbGaP.
GSE165177 = transient RNA log2 RPM, GSE165179 = transient EPIC methylation.
"""
import csv,gzip,json,re,urllib.request,urllib.error,zlib,hashlib,time
from pathlib import Path
BASE="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE165nnn"
SERIES=("GSE165176","GSE165177","GSE165178","GSE165179")
FILES={
"GSE165176":"GSE165176_Log2_RPM_Sendai_reprogramming.txt.gz",
"GSE165177a":"GSE165177_Log2_RPM_Transient_reprogramming.txt.gz",
"GSE165177b":"GSE165177_Log2_RPM_Transient_reprogramming_part2_170621.txt.gz",
"GSE165178":"GSE165178_Matrix_processed_sendai.txt.gz",
"GSE165179":"GSE165179_Matrix_processed_transient.txt.gz"}
def request(uri,byte_limit):
    req=urllib.request.Request(uri,headers={"User-Agent":"BIO-MIMIC-X/MPTR-external-validation/1.0","Range":f"bytes=0-{byte_limit-1}","Accept-Encoding":"identity"})
    with urllib.request.urlopen(req,timeout=45) as resp:
        data=resp.read(byte_limit)
        return data,resp.status,resp.headers.get("Content-Range",""),resp.headers.get("Content-Length","")
def gz_prefix(data):
    x=zlib.decompressobj(16+zlib.MAX_WBITS)
    return x.decompress(data).decode("utf-8-sig",errors="replace")
def series_matrix(gse):
    u=f"{BASE}/{gse}/matrix/{gse}_series_matrix.txt.gz"
    data,status,rng,cl=request(u,2_000_000)
    raw=gz_prefix(data)
    lines=raw.splitlines()
    titles=next((row for row in lines if row.startswith("!Sample_title\t")),None)
    ids=next((row for row in lines if row.startswith("!Sample_geo_accession\t")),None)
    if not titles or not ids:
        raise ValueError("missing authoritative sample metadata "+gse)
    t=next(csv.reader([titles],delimiter="\t"))
    k=next(csv.reader([ids],delimiter="\t"))
    if len(t)!=len(k) or len(k)<10:
        raise ValueError("different sample metadata columns "+gse)
    vals={key:val for key,val in zip(k[1:],t[1:])}
    if len(vals)!=len(k)-1:raise ValueError("duplicate geo accessions "+gse)
    return {"series":gse,"source":u,"n":len(vals),"samples":vals,"prefix_complete":raw.endswith("\n")}
def file_prefix(name, gse):
    u=f"{BASE}/{gse}/suppl/{name}"
    data,status,rng,cl=request(u,100000)
    raw=gz_prefix(data)
    lines=raw.splitlines()
    return {"source":u,"http":status,"content_range":rng,"content_length":cl,
            "header_lines":lines[:4],"header_count_tab_fields":len(lines[0].split("\t")) if lines else 0,
            "downloaded_bytes":len(data),"decompressed_prefix_chars":len(raw)}
def main():
    reports={}
    for s in SERIES:
        try:
            reports[s]=series_matrix(s)
        except Exception as e:reports[s]={"error":f"{type(e).__name__}: {e}"}
    result={"schema":"BIO-MIMIC-X/MPTR-ORTHOGONAL-PUBLIC-PREFLIGHT/1",
            "sources":reports,"files":{},"status":"PARTIAL"}
    for name in FILES:
        gse="GSE165177" if name.startswith("GSE165177") else name
        try:result["files"][name]=file_prefix(FILES[name],gse)
        except Exception as e:result["files"][name]={"error":f"{type(e).__name__}: {e}"}
    if all("samples" in reports[s] for s in SERIES):
        for a,b,label in [("GSE165177","GSE165179","transient"),("GSE165176","GSE165178","sendai")]:
            p=reports[a]["samples"]; q=reports[b]["samples"]
            titles_a={v:k for k,v in p.items()}
            titles_b={v:k for k,v in q.items()}
            shared=sorted(set(titles_a)&set(titles_b))
            if len(titles_a)!=len(p) or len(titles_b)!=len(q):
                raise ValueError("ambiguous duplicated public sample titles")
            result[label+"_matched_titles"]=[{"title":x,"RNA_GSM":titles_a[x],"DNAm_GSM":titles_b[x]} for x in shared]
            result[label+"_exact_match_count"]=len(shared)
            result[label+"_distinct_donors"]=sorted({x.split("_")[0] for x in shared})
        result["status"]="PASS_PUBLIC_GEO_CONDITION_LEVEL_JOIN_ONLY"
    p=Path("qa-artifacts/GILL-MPTR-PREFLIGHT-2026-11-02.json")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("BIO_MIMIC_MPTR_PUBLIC_PREFLIGHT "+json.dumps({k:v for k,v in result.items() if k not in ("sources","files","transient_matched_titles","sendai_matched_titles")},sort_keys=True))
    for x in result["files"].items():
        print("MPTR_COMPRESSED_SOURCE_HEADER "+json.dumps(x,sort_keys=True)[:5800])
    for name in ("transient_matched_titles","sendai_matched_titles"):
        if name in result:print(name,json.dumps(result[name][:15]))
if __name__=="__main__":main()
