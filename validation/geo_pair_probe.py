#!/usr/bin/env python3
"""Read-only manifest probe of real GEO expression inputs. No scientific claims."""
from __future__ import annotations
import csv, gzip, hashlib, io, json, urllib.request
URLS={
 "axolotl_counts": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE284nnn/GSE284768/suppl/GSE284768_MatrixCounts.csv.gz",
 "human_matrix": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE28nnn/GSE28914/matrix/GSE28914_series_matrix.txt.gz",
 "human_platform": "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz",
 "axolotl_geo_243137": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE243nnn/GSE243137/suppl/GSE243137_MatrixCounts_allsamples.txt.gz",
 "axolotl_geo_185593": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE185nnn/GSE185593/suppl/GSE185593_10072021_normalized_and_filtered_for_analysis.txt.gz",
 "axolotl_geo_111213_small": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE111nnn/GSE111213/suppl/GSE111213_Dividing_cell-enriched_transcripts.csv.gz",
 "axolotl_geo_237864": "https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE237864&format=file&file=GSE237864_count_matrix.txt.gz",
 "axolotl_counts_alt": "https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE284768&format=file&file=GSE284768_MatrixCounts.csv.gz",
}
def probe(name,url,max_bytes=35_000_000):
    req=urllib.request.Request(url,headers={"User-Agent":"BIO-MIMIC-X research-only evidence-check/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r:
        data=r.read(max_bytes+1)
        if len(data)>max_bytes: raise ValueError("dataset exceeds data budget")
        if not data.startswith(b"\x1f\x8b"):
            raise ValueError("expected gzip; final_url="+r.geturl()+" content_type="+str(r.headers.get("Content-Type"))+" first_bytes="+repr(data[:120]))
    digest=hashlib.sha256(data).hexdigest()
    decompressed=gzip.decompress(data)
    head=decompressed.decode("utf-8",errors="replace").splitlines()
    print("GEO_RAW_MANIFEST "+json.dumps({
      "dataset":name,"url":url,"compressed_size":len(data),"sha256":digest,
      "first_rows":[line[:400] for line in head[:8]],
      "row_count":len(head),
      "first_data":next((ln[:400] for ln in head if ln and not ln.startswith(("!", "#", "^"))), ""),
    },sort_keys=True))
def main():
    for key,url in URLS.items():
        try:probe(key,url)
        except Exception as e:print("GEO_INPUT_FAILURE "+json.dumps({"dataset":key,"reason":type(e).__name__+": "+str(e)[:250]}))
if __name__=="__main__":main()
