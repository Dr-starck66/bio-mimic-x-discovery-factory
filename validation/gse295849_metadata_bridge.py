#!/usr/bin/env python3
"""GSE295849: join official GEO sample records to physical EPIC chip identifiers.

Never match donors by order, nearest age, or chip-row adjacency.
A valid sample-to-chip mapping needs the literal 12-digit Illumina chip + position
appearing in the metadata of ONE GEO sample, or an explicit external accession
crosswalk whose provenance has been verified separately.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import urllib.request
from pathlib import Path

BASE = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE295nnn/GSE295849/"
SERIES_URL = BASE + "matrix/GSE295849_series_matrix.txt.gz"
FILELIST_URL = BASE + "suppl/filelist.txt"
CLOCK_REPORT = Path(__file__).resolve().parents[1] / "reports/factory/GSE295849-HORVATH2018-REAL-CLOCK-3.json"
CHIP_RE = re.compile(r"\b\d{12}_R\d{2}C\d{2}\b", flags=re.I)
GSM_RE = re.compile(r"\bGSM\d+\b", flags=re.I)

def retrieve(url, max_bytes=2_000_000):
    req = urllib.request.Request(url, headers={"User-Agent":"BIO-MIMIC-X-public-science-sample-join/1.0","Accept-Encoding":"identity"})
    with urllib.request.urlopen(req, timeout=35) as response:
        if response.status!=200 or response.url!=url:
            raise ValueError("unexpected redirect or HTTP status")
        length=int(response.headers.get("Content-Length") or 0)
        if length and length>max_bytes:
            raise ValueError("content-length exceeds budget")
        data=response.read(max_bytes+1)
        if length and len(data)!=length:
            raise ValueError("truncated HTTP body")
        if not data or len(data)>max_bytes:
            raise ValueError("empty or oversized source")
    if not data.startswith(b"\x1f\x8b") and url.endswith(".gz"):
        raise ValueError("gzip magic missing")
    if url.endswith(".gz"):
        data_decoded=gzip.decompress(data)
    else:
        data_decoded=data
    return data_decoded, {"url":url,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
                          "uncompressed_bytes":len(data_decoded)}

def parse_matrix_metadata(text):
    """Parse GEO's tab-separated '!Sample_*' metadata, respecting quoted fields."""
    vectors={}
    for row in csv.reader(io.StringIO(text),delimiter="\t",quotechar='"'):
        if not row or not row[0].startswith("!Sample_"):
            continue
        key=row[0][len("!Sample_"):].lower()
        vectors.setdefault(key,[]).append([x.strip() for x in row[1:]])
    gm=vectors.get("geo_accession",[])
    if len(gm)!=1 or not gm[0]:
        raise ValueError("GEO series matrix missing unique Sample_geo_accession")
    gsms=gm[0]
    if any(not re.fullmatch(r"GSM\d+",v) for v in gsms) or len(set(gsms))!=len(gsms):
        raise ValueError("duplicated or invalid GSM accessions")
    records=[]
    for i,gsm in enumerate(gsms):
        entry={"gsm":gsm,"fields":{}}
        for key,vecs in vectors.items():
            vals=[vv[i] for vv in vecs if len(vv)==len(gsms) and vv[i]]
            if vals:entry["fields"][key]=vals
        # Sample record must have a title; if not, do not falsely infer state.
        if not entry["fields"].get("title"):
            raise ValueError("missing GEO sample title: "+gsm)
        literal="\n".join(x for values in entry["fields"].values() for x in values)
        entry["chip_ids"]=sorted(set(CHIP_RE.findall(literal)))
        records.append(entry)
    return records

def explicit_join(records, clock_samples):
    source_lookup={}
    for sample in records:
        for chip in sample["chip_ids"]:
            source_lookup.setdefault(chip,[]).append(sample)
    matched=[]
    for age in clock_samples:
        chip=age["chip_sample_id"]
        hits=source_lookup.get(chip,[])
        if len(hits)==1:
            matched.append({
                "chip_sample_id":chip,"age_years":age["age_years"],"gsm":hits[0]["gsm"],
                "metadata_fields":hits[0]["fields"],
                "provenance":"literal_chip_id_in_GEO_metadata",
                "status":"SOURCE_EXACT_SAMPLE_MATCH",
            })
        else:
            matched.append({
                "chip_sample_id":chip,"age_years":age["age_years"],"gsm":None,
                "candidate_gsms":[h["gsm"] for h in hits],
                "status":"UNVERIFIED_NO_UNIQUE_SOURCE_MATCH",
            })
    return matched

def filelist_crosswalk(text, chips):
    """Raw filename lines are diagnostic hints, never proof of GSM mapping."""
    lines=text.splitlines()
    return {chip:[line[:350] for line in lines if chip.lower() in line.lower()][:5] for chip in chips}

def build_report(records, clock, manifest=None, filelist=None):
    ages=clock["computed_ages_years"]
    expected_chips=[x["chip_sample_id"] for x in ages]
    if not ages or len(set(expected_chips)) != len(ages):
        raise ValueError("invalid stored age report")
    mapped=explicit_join(records,ages)
    return {
        "schema":"BIO-MIMIC-X/GSE295849-GEO-METADATA-JOIN/1",
        "series":"GSE295849",
        "source":manifest,
        "filelist_source":filelist[1] if filelist else None,
        "reported_gsm_count":len(records),
        "found_chip_ids_in_gsm_metadata":sum(bool(x["chip_ids"]) for x in records),
        "total_unique_chip_ids":len(set(c for r in records for c in r["chip_ids"])),
        "clock_samples":len(ages),
        "literal_gsm_matches":sum(x["status"]=="SOURCE_EXACT_SAMPLE_MATCH" for x in mapped),
        "joined_clock_samples":mapped,
        "filelist_hints":filelist_crosswalk(filelist[0],expected_chips) if filelist else None,
        "geo_sample_metadata":records,
        "donor_condition_passage_pairs":"UNVERIFIED",
        "independent_paired_deaging":"UNVERIFIED",
        "clinical_rejuvenation":"UNVERIFIED",
        "historical_negative_control":{"GSE74387":"FAIL_RETAINED"},
        "decision":"PARTIAL_METADATA_JOIN" if all(x["status"]=="SOURCE_EXACT_SAMPLE_MATCH" for x in mapped) else "PARTIAL_UNMAPPED_CHIPS",
        "rule":"No donor or stage inferred from adjacent chip positions; require literal accession crosswalk and explicit biological conditions before age subtraction.",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    clock=json.loads(CLOCK_REPORT.read_text(encoding="utf-8"))
    result={"schema":"BIO-MIMIC-X/GSE295849-GEO-METADATA-JOIN/1","decision":"PARTIAL_SOURCE_FAILURE"}
    code=1
    try:
        raw,meta=retrieve(SERIES_URL,1_000_000)
        records=parse_matrix_metadata(raw.decode("utf-8-sig"))
        try:
            m,mt=retrieve(FILELIST_URL,1_000_000)
            filelist=(m.decode("utf-8-sig"),mt)
        except Exception as e:
            filelist=None
            print("FILELIST_SOURCE_WARNING",type(e).__name__,str(e)[:200])
        result=build_report(records,clock,meta,filelist)
        code=0
    except Exception as e:
        result["failure"]=f"{type(e).__name__}: {e}"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    a.out.write_text(payload,encoding="utf-8")
    # Keep all sample records as a small retained artifact, print an excerpt for review.
    summary={k:v for k,v in result.items() if k not in ("geo_sample_metadata","joined_clock_samples","filelist_hints")}
    summary["joined_clock_samples"]=result.get("joined_clock_samples",[])
    summary["first_gsm_records"]=result.get("geo_sample_metadata",[])[:3]
    print("GSE295849_METADATA_JOIN "+json.dumps(summary,ensure_ascii=False,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
