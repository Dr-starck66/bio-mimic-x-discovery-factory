#!/usr/bin/env python3
"""Download exact GEO gzip bytes, validate CRC, hash and accession; never decode binary via scraper."""
import argparse,gzip,hashlib,json,os,pathlib,tempfile,urllib.request
BASE="https://ftp.ncbi.nlm.nih.gov/geo/series"
ACCESSIONS=("GSE179847","GSE179848","GSE246954","GSE247179")
def url(acc):
 if acc not in ACCESSIONS:raise ValueError("accession not allowlisted")
 return f"{BASE}/{acc[:-3]}nnn/{acc}/matrix/{acc}_series_matrix.txt.gz"
def fetch(acc,directory,timeout=60):
 directory=pathlib.Path(directory);directory.mkdir(parents=True,exist_ok=True)
 target=directory/(acc+"_series_matrix.txt.gz")
 fd,tmp=tempfile.mkstemp(prefix=acc+".",suffix=".partial",dir=directory)
 h=hashlib.sha256();count=0;lines=0;accession_found=False
 try:
  with os.fdopen(fd,"wb") as f,urllib.request.urlopen(urllib.request.Request(url(acc),headers={"User-Agent":"ASTRA-BIO-MIMIC-X-research/1.0"}),timeout=timeout) as r:
   if r.status!=200:raise ValueError(f"HTTP {r.status}")
   while True:
    chunk=r.read(1024*1024)
    if not chunk:break
    f.write(chunk);h.update(chunk);count+=len(chunk)
  if count<100:raise ValueError("unexpectedly small gzip")
  with gzip.open(tmp,"rb") as f:
   for line in f:
    lines+=1
    if line.startswith(b"!Series_geo_accession") and acc.encode() in line:accession_found=True
  if not accession_found:raise ValueError("accession missing from decompressed GEO matrix")
  os.replace(tmp,target)
  return {"accession":acc,"url":url(acc),"file":str(target),"bytes":count,"sha256":h.hexdigest(),"decompressed_lines":lines,"gzip_crc":"PASS","accession_match":"PASS"}
 except BaseException:
  if os.path.exists(tmp):os.unlink(tmp)
  raise
def main():
 p=argparse.ArgumentParser();p.add_argument("--out",default="data/geo_independent");p.add_argument("--accessions",nargs="+",choices=ACCESSIONS,default=list(ACCESSIONS));a=p.parse_args()
 results=[]
 for acc in a.accessions:
  try:results.append({"status":"PASS",**fetch(acc,a.out)})
  except Exception as e:results.append({"accession":acc,"status":"FAIL","error":str(e)})
 pathlib.Path(a.out).mkdir(parents=True,exist_ok=True)
 (pathlib.Path(a.out)/"manifest.json").write_text(json.dumps(results,indent=2)+"\n")
 print(json.dumps(results,indent=2))
 if any(r["status"]!="PASS" for r in results):raise SystemExit(1)
if __name__=="__main__":main()
