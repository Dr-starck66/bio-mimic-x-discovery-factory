#!/usr/bin/env python3
"""Actual public Gill et al. 2022 RNA-Seq measurements plus GEO DNAm sample mapping.

GSE165177 RNA expression: two authentic log2 RPM processed matrices (not
simulated). GSE165179 EPIC DNAm: publicly listed paired experimental
conditions; this script DOES NOT claim DNA beta values were downloaded.
No protected human data, paid service, or dbGaP data.
"""
from __future__ import annotations
import csv, gzip, hashlib, json, math, re, tempfile, urllib.request, urllib.error, zlib
from pathlib import Path
from statistics import mean
ROOT=Path(__file__).resolve().parents[1]
META=ROOT/"reports/factory/GSE165179-PUBLIC-DNAM-SAMPLE-METADATA-2026-11-02.json"
BASE="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE165nnn/GSE165177/suppl/"
RNA_FILES=[
 "GSE165177_Log2_RPM_Transient_reprogramming.txt.gz",
 "GSE165177_Log2_RPM_Transient_reprogramming_part2_170621.txt.gz",
]
FIBRO=("COL1A1","COL1A2","COL3A1","DCN","LUM","THY1","FAP","FN1")
PLURIPOTENT=("POU5F1","NANOG","SALL4","LIN28A","DPPA4","TDGF1","EPCAM","SOX2")
TARGET=set(FIBRO)|set(PLURIPOTENT)
DNAM_URL="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE165nnn/GSE165179/suppl/GSE165179_Matrix_processed_transient.txt.gz"
def guarded_download(uri: str, output:Path, max_bytes=20_000_000):
    """NCBI GEO may reject full GET but allow standard RFC7233 byte ranges.

    Never trust the range label alone. Verify HTTP206, exact Content-Range,
    every returned segment length, final sha+gzip CRC. Bounded source-only retries.
    """
    import time
    pos=0
    total=None
    chunk_size=1_000_000
    sha=hashlib.sha256()
    with output.open("wb") as dst:
        while total is None or pos<total:
            end=pos+chunk_size-1 if total is None else min(total-1,pos+chunk_size-1)
            last=None
            for retry in range(4):
                req=urllib.request.Request(uri,headers={
                    "User-Agent":"BIO-MIMIC-X-Gill2022-public-RNA/1",
                    "Range":f"bytes={pos}-{end}","Accept-Encoding":"identity"})
                try:
                    with urllib.request.urlopen(req,timeout=60) as r:
                        cr=r.headers.get("Content-Range","")
                        m=re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)",cr)
                        if r.status!=206 or not m or int(m[1])!=pos or int(m[2])!=end:
                            raise ValueError("NCBI RFC7233 Content-Range mismatch")
                        declared=int(m[3])
                        if declared>max_bytes or declared<=0:
                            raise ValueError("NCBI RNA source is outside permitted size bound")
                        if total is not None and total!=declared:
                            raise ValueError("NCBI RNA source changed content length in transit")
                        total=declared
                        data=r.read(end-pos+2)
                        if len(data)!=end-pos+1:raise ValueError("truncated NCBI byte range")
                        sha.update(data);dst.write(data);pos+=len(data)
                        last=None
                        break
                except urllib.error.HTTPError as e:
                    if e.code not in (403,408,429,500,502,503,504):
                        raise
                    last=e
                    if chunk_size>131072:
                        chunk_size=max(65536,chunk_size//2)
                        end=pos+chunk_size-1 if total is None else min(total-1,pos+chunk_size-1)
                    time.sleep(min(5,retry+1))
                except (TimeoutError,urllib.error.URLError) as e:
                    last=e
                    time.sleep(min(5,retry+1))
            if last is not None:
                raise RuntimeError(f"NCBI public source range blocked at offset {pos}: {last}")
    # Full gzip decoder must reach EOF/CRC; also checks null truncation.
    with gzip.open(output,"rb") as g:
        while g.read(1<<20):pass
    return {"url":uri,"bytes":total,"sha256":sha.hexdigest(),
            "gzip_crc":"PASS","verified_complete_http206":True}

def extract_rna(files):
    result={}
    measurements={}
    samples={}
    for fn,path in files:
        with gzip.open(path,"rt",encoding="utf-8-sig",errors="strict",newline="") as f:
            reader=csv.reader(f,delimiter="\t")
            header=next(reader)
            if len(header)<25 or header[:2]!=["Probe","Chromosome"] or header[5:7]!=["Feature","ID"]:
                raise ValueError("RNA processed GEO header not as expected")
            cols=header[12:]
            if len(cols)!=len(set(cols)) or set(cols)&set(samples):
                raise ValueError("duplicate RNA sample labels, cannot join")
            for i,label in enumerate(cols):samples[label]=fn
            observed_gene_names=set()
            rows=0
            for row in reader:
                if not row:continue
                rows+=1
                if len(row)!=len(header):raise ValueError("RNA row column count mismatch")
                gene=row[5].strip()
                if gene not in TARGET:continue
                if gene in observed_gene_names:
                    raise ValueError("multiple RNA gene rows, cannot interpret log2 RPM unambiguously: "+gene)
                observed_gene_names.add(gene)
                values={}
                for i,title in enumerate(cols):
                    try:val=float(row[12+i])
                    except ValueError:raise ValueError("RNA gene value nonnumeric "+gene)
                    if not math.isfinite(val):raise ValueError("RNA gene value nonfinite "+gene)
                    values[title]=round(val,7)
                measurements.setdefault(gene,{}).update(values)
            if rows<12000:
                raise ValueError("RNA GEO processed matrix unexpectedly short")
            result[fn]={"samples":len(cols),"gene_rows_examined":rows,"found_markers":sorted(observed_gene_names)}
    return samples,measurements,result

def make_report(meta,samples,measurements,files):
    dnAm=meta["rows"]
    if len(dnAm)!=96 or meta["vetted_count"]!=96:
        raise ValueError("DNAm GEO metadata missing verified 96 public GSM records")
    gsm_by_title={x["official_sample_title"]:x for x in dnAm}
    if len(gsm_by_title)!=len(dnAm):raise ValueError("repeated DNAm condition title")
    shared=sorted(set(gsm_by_title)&set(samples))
    if len(shared)<15:raise ValueError("insufficient true matched RNA and DNAm sample conditions")
    avail_f=[x for x in FIBRO if x in measurements]
    avail_p=[x for x in PLURIPOTENT if x in measurements]
    if len(avail_f)<4 or len(avail_p)<3:raise ValueError("predeclared RNA marker panel not available")
    gene_z={}
    for gene in avail_f+avail_p:
        xx=[measurements[gene][k] for k in samples]
        avg=mean(xx)
        sd=math.sqrt(mean((x-avg)**2 for x in xx))
        if sd<1e-5:raise ValueError("constant RNA marker "+gene)
        gene_z[gene]={s:(v-avg)/sd for s,v in measurements[gene].items()}
    rows=[]
    for label in shared:
        info=gsm_by_title[label]
        score=mean(gene_z[g][label] for g in avail_f)-mean(gene_z[g][label] for g in avail_p)
        rows.append({
            "experimental_label":label,
            "DNAm_GSM":info["methyl_gsm"],
            "DNA_methylation_chip":info["methyl_chip"],
            "donor":label.split("_")[0],
            "donor_age_metadata_years":info["donor_age"],
            "timepoint_days":info["timepoint_days"],
            "RNA_expression_units":"submitted GEO log2 reads per million",
            "RNA_fibroblast_minus_pluripotency_zscore":round(score,6),
            "RNA_markers_log2_RPM":{g:measurements[g][label] for g in avail_f+avail_p},
            "DNA_methylation_beta_acquired":False,
            "same_physical_aliquot_verified":False
        })
    # Mandatory donor+timepoint+experiment control vs reprogrammed pair, not stage-only.
    exact={}
    for x in rows:exact[x["experimental_label"]]=x
    pairs=[]
    pat=re.compile(r"^(O[123])_transiently_reprogrammed_(\d+)days_exp([12])$")
    for row in rows:
        m=pat.fullmatch(row["experimental_label"])
        if not m:continue
        control=f"{m.group(1)}_negative_control_{m.group(2)}days_exp{m.group(3)}"
        if control not in exact:continue
        y=exact[control]
        pairs.append({
            "donor":m.group(1),"timepoint_days":int(m.group(2)),"experiment":int(m.group(3)),
            "RNA_treated_DNAm_GSM":row["DNAm_GSM"],
            "RNA_control_DNAm_GSM":y["DNAm_GSM"],
            "RNA_identity_delta_reprogrammed_minus_control":round(row["RNA_fibroblast_minus_pluripotency_zscore"]-y["RNA_fibroblast_minus_pluripotency_zscore"],6),
            "RNA_only_clock_delta":"UNVERIFIED",
            "age_after_RNA_adjustment":"UNVERIFIED"
        })
    if len(pairs)<2:raise ValueError("few exact donor/experiment/day controls")
    return {
        "schema":"BIO-MIMIC-X/GILL2022-GSE165180-PUBLIC-RNA-DNAM-EXACT-CONDITION-JOIN/1",
        "status":"PASS_MEASURED_PUBLIC_RNA_AND_REAL_GEO_DNAM_CONDITION_METADATA_ONLY",
        "paper":"Gill et al., eLife 2022, DOI 10.7554/eLife.71624",
        "super_series":"GSE165180",
        "RNA_series":"GSE165177","DNA_methylation_series":"GSE165179",
        "RNA_files":files,"RNA_source_summary":source_summary,
        "DNAm_GEO_metadata_source":meta["source_geo"],
        "DNAm_public_metadata_source_sha":meta["source_third_party_blob_sha"],
        "RNA_sample_titles":len(samples),
        "DNAm_samples":len(dnAm),
        "matched_distinct_RNA_DNAm_sample_titles":len(shared),
        "matched_donors":sorted(set(x["donor"] for x in rows)),
        "RNA_fibroblast_markers":avail_f,
        "RNA_pluripotency_markers":avail_p,
        "real_RNA_values_acquired":True,
        "DNA_methylation_beta_values_acquired":False,
        "clock_adjusted_for_RNA_identity":"UNVERIFIED_PENDING_ACTUAL_DNAM_VALUES",
        "identity_score_status":"MEASURED_RNA_TRANSCRIPTOMIC_IDENTITY_IN_PUBLIC_SAME_CONDITION",
        "actual_RNA_sample_matched_DNAM_metadata":rows,
        "exact_donor_timepoint_control_treated_pairs":pairs,
        "negative_controls":{
            "n_same_donor_day_exp_pairs":len(pairs),
            "RNA_missing_series_titles":sorted(set(samples)-set(gsm_by_title)),
            "DNAm_missing_RNA_titles":sorted(set(gsm_by_title)-set(samples)),
            "biological_aging_causality":"UNVERIFIED",
            "RNA_MPTR_source_study_not_GSE295849":"TRUE_KEEP_AS_EXTERNAL_VALIDATION"
        }
    }
def probe_methyl():
    # Bounded byte inspections of official public EPIC matrix; failure is reported,
    # never circumvented with restricted access or fake beta values.
    probes={}
    urls={
      "ftp_range":DNAM_URL,
      "ncbi_geo_download":"https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE165179&file=GSE165179_Matrix_processed_transient.txt.gz&format=file",
    }
    for name,url in urls.items():
        for mode in ("HEAD","GET_RANGE","GET_BOUNDED"):
            try:
                hdr={"User-Agent":"Mozilla/5.0 BIO-MIMIC-X-PublicResearch/1","Accept-Encoding":"identity"}
                if mode=="GET_RANGE":hdr["Range"]="bytes=0-65535"
                req=urllib.request.Request(url,headers=hdr,method="HEAD" if mode=="HEAD" else "GET")
                with urllib.request.urlopen(req,timeout=20) as res:
                    b=res.read(65536) if mode!="HEAD" else b""
                    decoded=""
                    if b:
                        try:decoded=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(b).decode("utf-8-sig",errors="replace").splitlines()[0][:650]
                        except (zlib.error,UnicodeDecodeError): decoded="non-gzip-or-not-decompressible"
                    probes[name+"_"+mode]={"http":res.status,"range":res.headers.get("Content-Range",""),"first_header":decoded,"read_bytes":len(b),"content_type":res.headers.get("Content-Type","")}
            except urllib.error.HTTPError as exc:
                probes[name+"_"+mode]={"status":"HTTP_FAILURE","http":exc.code,
                     "body_excerpt":exc.read(350).decode("utf8",errors="replace")[:350]}
            except Exception as exc:
                probes[name+"_"+mode]={"status":"TRANSPORT_FAILURE","reason":f"{type(exc).__name__}: {str(exc)[:180]}"}
    return probes
if __name__=="__main__":
    public_meta=json.loads(META.read_text(encoding="utf-8"))
    source_summary={}
    with tempfile.TemporaryDirectory() as tmp:
        artifacts=[]
        for fn in RNA_FILES:
            target=Path(tmp)/fn
            source_summary[fn]=guarded_download(BASE+fn,target)
            artifacts.append((fn,target))
        sample_names,expression,files=extract_rna(artifacts)
        report=make_report(public_meta,sample_names,expression,files)
        report["methylation_source_head_tests"]=probe_methyl()
    out=ROOT/"qa-artifacts/GILL-MPTR-ACTUAL-PUBLIC-RNA-2026-11-02.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("BIO_MIMIC_GILL_PUBLIC_REAL_RNA "+json.dumps({k:v for k,v in report.items() if k not in ("actual_RNA_sample_matched_DNAM_metadata","exact_donor_timepoint_control_treated_pairs","negative_controls")},sort_keys=True)[:9000])
    print("BIO_MIMIC_GILL_PUBLIC_RNA_MATCHED_PAIRS "+json.dumps(report["exact_donor_timepoint_control_treated_pairs"])[:6500])
