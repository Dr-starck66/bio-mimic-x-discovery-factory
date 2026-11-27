#!/usr/bin/env python3
"""Acquire only an explicitly linked original Nature/PMC XLSX; SHA-256 and fail-closed manifest."""
import argparse,hashlib,json,sys,urllib.parse,urllib.request,zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET
ARTICLE="https://www.nature.com/articles/s41467-022-30363-y"
PMC_XML="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9110368/fullTextXML"
ALLOW={"www.nature.com","static-content.springer.com","pmc.ncbi.nlm.nih.gov","www.ebi.ac.uk","cdn.ncbi.nlm.nih.gov"}
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.href=None
    def handle_starttag(self,tag,attrs):
        if tag=="a":self.href=dict(attrs).get("href")
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:self.links.append(self.href);self.href=None
def guard(uri):
    p=urllib.parse.urlparse(uri)
    if p.scheme!="https" or p.hostname not in ALLOW:raise ValueError(f"Forbidden source URL: {uri}")
    return uri
def from_html(html):
    a=Links();a.feed(html)
    return list(dict.fromkeys(guard(urllib.parse.urljoin(ARTICLE,x)) for x in a.links
      if urllib.parse.urljoin(ARTICLE,x).lower().split("?")[0].endswith(".xlsx")
      and urllib.parse.urlparse(urllib.parse.urljoin(ARTICLE,x)).hostname in ALLOW))
def from_xml(xml):
    root=ET.fromstring(xml);urls=[]
    for parent in root.iter():
        if parent.tag.rsplit("}",1)[-1]!="supplementary-material":continue
        for elem in parent.iter():
            name=elem.attrib.get("{http://www.w3.org/1999/xlink}href",elem.attrib.get("href",""))
            if name.lower().endswith(".xlsx"):
                url="https://pmc.ncbi.nlm.nih.gov/articles/PMC9110368/bin/"+urllib.parse.quote(name.split("/")[-1])
                urls.append(guard(url))
    return list(dict.fromkeys(urls))
def text_get(uri):
    req=urllib.request.Request(guard(uri),headers={"User-Agent":"BIO-MIMIC-X scientific source audit"})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read(20_000_001).decode("utf-8")
def download(uri,dest):
    req=urllib.request.Request(guard(uri),headers={"User-Agent":"BIO-MIMIC-X scientific source audit"})
    size=0
    with urllib.request.urlopen(req,timeout=50) as r:
        if r.status!=200 or urllib.parse.urlparse(r.url).hostname not in ALLOW:raise ValueError("Unsafe response")
        with dest.open("wb") as f:
            while True:
                chunk=r.read(1024*1024)
                if not chunk:break
                size+=len(chunk)
                if size>80_000_000:raise ValueError("Exceeds 80 MB limit")
                f.write(chunk)
    if not zipfile.is_zipfile(dest):raise ValueError("Not a ZIP/XLSX")
    with zipfile.ZipFile(dest) as z:
        if not {"[Content_Types].xml","xl/workbook.xml"}<=set(z.namelist()):raise ValueError("Not a workbook")
    return size
def main():
    p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    errors=[];candidates=[]
    try:candidates=from_html(text_get(ARTICLE))
    except Exception as e:errors.append(f"Nature discovery: {type(e).__name__}: {e}")
    if len(candidates)!=1:
        try:candidates=list(dict.fromkeys(candidates+from_xml(text_get(PMC_XML))))
        except Exception as e:errors.append(f"PMC discovery: {type(e).__name__}: {e}")
    manifest={"doi":"10.1038/s41467-022-30363-y","status":"FAIL","source_downloaded":False,
              "discovered_xlsx_urls":candidates,"errors":errors}
    if len(candidates)==1:
        out=a.output_dir/"kiweler2022_original_source_data.xlsx"
        try:
            size=download(candidates[0],out)
            manifest.update({"status":"PASS","source_downloaded":True,"bytes":size,
                "source_url":candidates[0],"sha256":hashlib.sha256(out.read_bytes()).hexdigest()})
        except Exception as e:
            out.unlink(missing_ok=True);errors.append(f"XLSX download: {type(e).__name__}: {e}")
    elif len(candidates)>1:errors.append("Ambiguous XLSX candidates; manual selection required")
    else:errors.append("No source link explicitly discovered: do not invent MOESM filename")
    (a.output_dir/"KIWELER2022-SOURCE-MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest));return 0 if manifest["status"]=="PASS" else 2
if __name__=="__main__":sys.exit(main())
