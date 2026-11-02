#!/usr/bin/env python3
"""Independent, OPEN 2018 RNA-seq identity reference: GSE117720 (Sheng et al.).

Never confuse these 19 public VST-normalized expression samples with the
six matched 2026 RNA profiles, which are restricted under dbGaP phs004047.
The 2018 sample labels R_107b and MJD33b are *not independently identified*
as the 2026 pseudonyms 107 and 33. No direct donor-level age correction.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
ROOT=Path(__file__).resolve().parents[1]
METADATA=ROOT/"reports/factory/GSE117720-PUBLIC-RNA-REFERENCE-METADATA-2026-11-02.json"
URL="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE117nnn/GSE117720/suppl/GSE117720_Sheng_2018_GEO_RNAseq_genes_vst.txt.gz"
OUT=ROOT/"reports/factory/GSE117720-REAL-RNA-REFERENCE-LATEST.json"
# Full original archive bytes independently retrieved on GitHub 2026-11-02,
# before parser repair; pin identity, not a merely plausible gzip.
GEO_OPEN_SOURCE_SHA256="6c3c366e26f5757a23bd81359d014aa7b7fe698f85f2c3961c925b4dfd9483dc"
GEO_OPEN_SOURCE_BYTES=2460476
NEURAL=("PAX6","NES","SOX1","SOX2","HES5","FABP7","SOX9")
ERYTHROID=("GATA1","KLF1","HBB","ALAS2","GYPA","EPOR","HBA1")
PINNED_MARKERS=NEURAL+ERYTHROID

def retrieve_open_source(url=URL):
    """Byte-bounded, HTTPS-only public processed data. No controlled SRA paths."""
    if url!=URL: raise ValueError("Only official public 2018 GEO supplementary URL allowed")
    failures=[]
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"BIO-MIMIC-X-public-GEO-reanalysis/1.0"})
            with urllib.request.urlopen(req,timeout=50) as response:
                if response.status!=200 or response.geturl()!=url:
                    raise ValueError("unverified source redirect or non-200 response")
                raw=response.read(5_000_001)
            if len(raw)!=GEO_OPEN_SOURCE_BYTES or hashlib.sha256(raw).hexdigest()!=GEO_OPEN_SOURCE_SHA256:
                raise ValueError("original public GEO RNA source SHA-256/length changed")
            if raw[:2]!=b'\x1f\x8b':raise ValueError("official RNA gzip magic mismatch")
            decoded=gzip.decompress(raw)  # checks full gzip CRC, not just header
            if len(decoded)>120_000_000:raise ValueError("decompressed RNA file budget exceeded")
            return raw,decoded,failures
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ConnectionResetError) as exc:
            failures.append(f"{type(exc).__name__}: {exc}"[:250])
            if attempt==2: raise RuntimeError("PUBLIC_2018_GEO_NETWORK_FAILURE "+str(failures)) from exc
            time.sleep(2*(attempt+1))

def parse_public_vst(txt: str, meta: dict):
    entries=meta["metadata_rows"]
    if len(entries)!=19 or len({x["RNA_library_id"] for x in entries})!=19:
        raise ValueError("expected 19 distinct verified GEO 2018 RNA libraries")
    first=txt.splitlines()[0]
    delim='\t' if first.count('\t')>=first.count(',') else ','
    rdr=csv.reader(io.StringIO(txt),delimiter=delim)
    header=next(rdr,None)
    if not header or len(header)<21 or len(header)>40:
        raise ValueError("unexpected GEO VST header: "+repr((header or [])[:40]))
    if header[:2] != ["ensembl_gene_id","hgnc_symbol"]:
        raise ValueError("GEO 2018 gene symbol columns not verified: "+repr(header[:3]))
    # Avoid positional guessing: library IDs must be uniquely matched by literal
    # sample token in RNA table heading, not fabricated or ordinal labels.
    colidx={}
    for s in entries:
        sample=s["RNA_library_id"]
        matches=[j for j,h in enumerate(header) if
                 re.search(r'(?<![A-Za-z0-9])'+re.escape(sample)+r'(?![0-9])',h)]
        if len(matches)!=1:
            raise ValueError("RNA VST sample-column ambiguity "+sample+": "+str(matches)+", header "+repr(header[:28]))
        colidx[sample]=matches[0]
    if len(set(colidx.values()))!=19:
        raise ValueError("RNA VST duplicate sample column join")
    sample_column_indices=set(colidx.values())
    if 0 in sample_column_indices or 1 in sample_column_indices:
        raise ValueError("RNA sample column overlaps a gene identifier")
    # The actual 2018 author's original matrix has 7 extra differential
    # expression comparison columns AFTER the 19 library columns; some
    # comparison headings repeat. They are NOT sample expression columns.
    # Their values are intentionally excluded, not silently reinterpreted.
    non_sample_cols=[i for i in range(len(header)) if i not in sample_column_indices]
    if non_sample_cols[:2]!=[0,1] or any(
        not re.fullmatch(r"[A-Za-z0-9]+_vs_[A-Za-z0-9]+",header[i])
        for i in non_sample_cols[2:]
    ):
        raise ValueError("unexpected non-sample GEO comparison columns: "+repr(
            [header[i] for i in non_sample_cols]))
    gene_symbol_cols=[1]
    genes={}
    ambiguous_symbols=set()
    n_gene_rows=0
    for line in rdr:
        if not line:continue
        if len(line)!=len(header):
            raise ValueError("GEO VST row width mismatch")
        # Do not guess Ensembl-to-gene-symbol mapping. Only literal gene symbol
        # cells are accepted, possibly alongside Ensembl identifiers.
        m=[(g,i) for g in PINNED_MARKERS for i in gene_symbol_cols
           if line[i].strip().upper()==g]
        if not m:continue
        for g,_ in m:
            # A symbol can annotate multiple Ensembl gene loci. VST log
            # values must NOT be summed or arbitrarily reassigned to one
            # gene: exclude *all* ambiguous mappings, retaining an audit.
            if g in ambiguous_symbols:
                continue
            if g in genes:
                ambiguous_symbols.add(g)
                del genes[g]
                continue
            vals=[]
            for s in entries:
                value=line[colidx[s["RNA_library_id"]]].strip()
                try:v=float(value)
                except ValueError:raise ValueError("missing/non-numeric true VST gene: "+g)
                if not math.isfinite(v):raise ValueError("nonfinite true VST expression")
                vals.append(v)
            genes[g]=vals
        n_gene_rows+=1
    neural=[g for g in NEURAL if g in genes]
    erythroid=[g for g in ERYTHROID if g in genes]
    if len(neural)<3 or len(erythroid)<3:
        raise ValueError("insufficient independent REAL RNA markers: neural "+
                         str(neural)+"; erythroid "+str(erythroid)+"; header "+repr(header[:5]))
    z={}
    for g,values in genes.items():
        ave=mean(values)
        std=math.sqrt(mean((v-ave)**2 for v in values))
        if std<0.001:raise ValueError("constant VST marker: "+g)
        z[g]=[(v-ave)/std for v in values]
    scores={}
    for i,s in enumerate(entries):
        scores[s["RNA_library_id"]]=mean(z[g][i] for g in neural)-mean(z[g][i] for g in erythroid)
    bytype=defaultdict(list)
    bydonor=defaultdict(lambda:defaultdict(list))
    bypassage=defaultdict(lambda:defaultdict(list))
    for s in entries:
        sc=scores[s["RNA_library_id"]]
        bytype[s["cell_type"]].append(sc)
        bydonor[s["donor_pseudonym"]][s["cell_type"]].append(sc)
        if s["cell_type"]=="iNSC":
            passage=int(s["passage"].lstrip('P'))
            if passage in (3,5,6):bypassage[s["donor_pseudonym"]]["early"].append(sc)
            if passage in (18,19,21):bypassage[s["donor_pseudonym"]]["late"].append(sc)
    contrast=[]
    for donor,groups in sorted(bydonor.items()):
        if "EPC" in groups and "iNSC" in groups:
            contrast.append({"donor":donor,"EPC_RNA_identity_score":round(mean(groups["EPC"]),6),
                             "iNSC_RNA_identity_score":round(mean(groups["iNSC"]),6),
                             "delta_neural_minus_erythroid":round(mean(groups["iNSC"])-mean(groups["EPC"]),6)})
    maturation=[]
    for donor,groups in sorted(bypassage.items()):
        if groups.get("early") and groups.get("late"):
            maturation.append({"donor":donor,"early_passage_RNA_identity":round(mean(groups["early"]),6),
                               "late_passage_RNA_identity":round(mean(groups["late"]),6),
                               "delta":round(mean(groups["late"])-mean(groups["early"]),6),
                               "n_early":len(groups["early"]),"n_late":len(groups["late"])})
    return {
      "source":"GSE117720","kind":"REAL_PUBLIC_INDEPENDENT_2018_NORMALIZED_RNA",
      "RNA_source_year":2018,"library_count":len(entries),
      "marker_counts":{"neural":len(neural),"erythroid":len(erythroid)},
      "present_neural":neural,"present_erythroid":erythroid,
      "excluded_ambiguous_marker_symbols":sorted(ambiguous_symbols),
      "ambiguous_symbol_handling":"EXCLUDED_ENTIRELY_NO_ARBITRARY_ENSEMBL_MAPPING",
      "identity_direction":"gene-wise standardized observed VST neural minus erythroid; score is assay-specific, not clinical age",
      "by_cell_type":{k:{"n_samples":len(v),"mean_RNA_identity_score":round(mean(v),6),
                         "median_RNA_identity_score":round(median(v),6)}
                        for k,v in sorted(bytype.items())},
      "paired_EPC_to_iNSC_same_2018_donor":contrast,
      "paired_iNSC_early_to_late_same_2018_donor":maturation,
      "2018_to_2026_genetic_identity":"UNVERIFIED_NO_GENOTYPE_CROSSWALK",
      "2018_RNA_expression_matched_to_six_2026_donors":False,
      "2026_age_clock_adjusted_with_RNA":"UNVERIFIED_NOT_IDENTIFIABLE",
      "fate_confounded_by_conversion":True,
      "RNA_measurements_manufactured":False
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=OUT)
    p.add_argument("--local-gzip",type=Path,help="Synthetic or already independently verified GEO .gz file")
    args=p.parse_args(argv)
    report={"schema":"BIO-MIMIC-X/GSE117720-2018-OPEN-RNA-REFERENCE/1",
            "status":"PARTIAL_SOURCE_UNAVAILABLE",
            "reference_is_different_from_2026_six_donors":True,
            "2026_RNA_ADJUSTED_AGE":"UNVERIFIED",
            "source_url":URL}
    try:
        if args.local_gzip:
            raw=args.local_gzip.read_bytes()
            decoded=gzip.decompress(raw)
            attempts=[]
        else:
            raw,decoded,attempts=retrieve_open_source()
        metadata=json.loads(METADATA.read_text(encoding="utf8"))
        report["source_sha256"]=hashlib.sha256(raw).hexdigest()
        report["source_bytes"]=len(raw)
        report["remote_source_hash_pinned_verified"]=(not bool(args.local_gzip)) and report["source_sha256"]==GEO_OPEN_SOURCE_SHA256
        report["source_transport_failures_before_success"]=attempts
        report["independent_2018_RNA"]=parse_public_vst(decoded.decode("utf-8-sig"),metadata)
        report["status"]=("PASS_INDEPENDENT_PUBLIC_2018_RNA_REFERENCE_ONLY" if report["remote_source_hash_pinned_verified"] else "PASS_LOCAL_FIXTURE_NOT_REMOTE_SOURCE")
        rc=0
    except Exception as e:
        report["reason"]=f"{type(e).__name__}: {e}"
        rc=1
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
    print("BIO_MIMIC_REAL_PUBLIC_RNA "+json.dumps(report,sort_keys=True)[:15000])
    return rc

if __name__=="__main__":
    raise SystemExit(main())
