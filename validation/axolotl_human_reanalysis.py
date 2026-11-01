#!/usr/bin/env python3
"""Exploratory, transparent transcriptomics on genuine GEO samples.

Inputs: GSE284768 (axolotl blastema anterior-vs-posterior, 15 dpa),
        GSE28914 (human skin intact-vs-day 3, paired patients), GPL570,
        AmexT_v47/AmexG_v6 GTF.
These contrasts are BIOLOGICALLY DIFFERENT. No cross-species effect-size
concordance or human regenerative efficacy is inferred.
"""
from __future__ import annotations

import csv, gzip, hashlib, io, json, math, re, statistics, sys, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"factory"))
from human_bridge import ncbi_exact_gene, ncbi_human_orthologs, norm

URLS={
 "GSE284768":"https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE284768&format=file&file=GSE284768_MatrixCounts.csv.gz",
 "GSE28914":"https://ftp.ncbi.nlm.nih.gov/geo/series/GSE28nnn/GSE28914/matrix/GSE28914_series_matrix.txt.gz",
 "GPL570":"https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz",
 "AmexT_v47":"https://www.axolotl-omics.org/dl/AmexT_v47-AmexG_v6.0-DD.gtf.gz",
}
EXPECTED_SHA256={
 "GSE284768":"959ba8dbc7c681fb90489c0896df33650dde2f8496f3fd28c4f0e0d108f96efa",
 "GSE28914":"b81da74c04ee8ec2f68f3b854b6dcff28297b87cd0282b807bdace41fe8fcb7e",
 "GPL570":"d7cd44352127b1e34f3a720ebea86093ef255a38f1612a85a2962b71bde8f394",
 "AmexT_v47":"cc0c3c4e39f3afedcbe2bc5aad1d63fc461714aeb75051f4d109390455874c5d",
}
PANEL=("HAND2","SHH","VEGFC","IL10","FSTL1","GPX7","CTHRC1","ACTA2","COL1A1","MMP9","TGFB1","CXCL8")
ORTHO_CHECK=("HAND2","SHH","VEGFC","FSTL1")
OUT=ROOT/"reports/factory/AXOLOTL-HUMAN-TRANSCRIPTOMIC-LATEST.json"


def validate_source_bytes(name,body):
    if name not in EXPECTED_SHA256:
        raise ValueError("unknown source not on verified manifest")
    if not body.startswith(b"\x1f\x8b"):
        raise ValueError("missing gzip header")
    sha=hashlib.sha256(body).hexdigest()
    if sha!=EXPECTED_SHA256[name]:
        raise ValueError("source SHA256 mismatch (possibly truncated or revised): "+name)
    return sha


def fetch(name,attempts=3):
    url=URLS[name]
    last=None
    for attempt in range(attempts):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"BIO-MIMIC-X/2026-11-01 research-and-QC"})
            with urllib.request.urlopen(req,timeout=60) as response:
                body=response.read(62_000_001)
            if len(body)>62_000_000:
                raise ValueError("download exceeds 62 MB cap")
            sha=validate_source_bytes(name,body)
            return body,{"source":url,"sha256":sha,"bytes":len(body)}
        except Exception as err:
            last=err
            if attempt+1<attempts:
                time.sleep(1+attempt)
    raise RuntimeError(f"{name}: {type(last).__name__}: {last}")


def parse_annotation(data):
    gene_to_probes={}
    reader=csv.reader(io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(data)),encoding="utf-8",errors="replace"),delimiter="\t")
    head=None
    for row in reader:
        if not row or row[0].startswith(("^","#","!")):continue
        if row[0]=="ID":
            head=row
            break
    if not head: raise ValueError("GPL570 header missing")
    i_id=head.index("ID")
    i_symbol=head.index("Gene symbol")
    for row in reader:
        if len(row)<=max(i_id,i_symbol):continue
        symbol=row[i_symbol].strip()
        if symbol in PANEL:
            gene_to_probes.setdefault(symbol,set()).add(row[i_id].strip())
    return gene_to_probes


def parse_gtf(data):
    """Only 'gene' rows; require exactly one clear human-tagged annotation."""
    candidates={}
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as fh:
        for raw in fh:
            line=raw.decode("utf-8",errors="replace")
            if line.startswith("#"):continue
            parts=line.rstrip("\n").split("\t")
            if len(parts)<9 or parts[2]!="gene":continue
            ids=re.findall(r'gene_id "([^"]+)"',parts[8])
            names=re.findall(r'gene_name "([^"]+)"',parts[8])
            if not ids or not names:continue
            hs=set(re.findall(r'([A-Za-z0-9-]+)\s*\[hs\]',names[0],re.I))
            if len(hs)!=1:continue
            symbol=next(iter(hs)).upper()
            # Distinct cross-reference symbols, e.g. HAND1 [nr] and HAND2 [hs],
            # make this locus ambiguous for gene-specific analysis.
            all_symbols={v.upper() for v in re.findall(
                r'([A-Za-z][A-Za-z0-9-]*)\s*\[(?:hs|nr)\]',names[0],re.I
            )}
            if all_symbols!={symbol}:continue
            if symbol in PANEL:
                candidates.setdefault(symbol,set()).add(ids[0])
    return {k:sorted(v) for k,v in candidates.items()}


def read_axolotl(data,candidates):
    ids={g for vv in candidates.values() for g in vv}
    rows={}
    names=None
    total=None
    count=0
    with gzip.open(io.BytesIO(data),"rt",encoding="utf-8",errors="replace",newline="") as fh:
        for rec in csv.reader(fh):
            if not rec: continue
            if names is None:
                names=rec[1:]
                total=[0.0]*len(names)
                continue
            if len(rec)!=len(names)+1:continue
            try:
                values=[float(x) for x in rec[1:]]
                if not all(math.isfinite(x) and x>=0 for x in values):continue
            except ValueError:continue
            for i,v in enumerate(values):total[i]+=v
            count+=1
            if rec[0] in ids:rows[rec[0]]=values
    if not names or not count:raise ValueError("no usable axolotl count rows")
    if any(v<=0 for v in total):raise ValueError("zero RNA-seq library")
    anterior=[i for i,n in enumerate(names) if re.fullmatch(r"AnteriorBlastemaHI_Rep[1-4]",n)]
    posterior=[i for i,n in enumerate(names) if re.fullmatch(r"PosteriorBlastemaHI_Rep[1-4]",n)]
    if len(anterior)!=4 or len(posterior)!=4:
        raise ValueError("axolotl experimental sample groups incorrect")
    def effect(v):
        a=[math.log2(1+1_000_000*v[i]/total[i]) for i in anterior]
        p=[math.log2(1+1_000_000*v[i]/total[i]) for i in posterior]
        return round(statistics.mean(p)-statistics.mean(a),4)
    genes={}
    for symbol,gene_ids in candidates.items():
        usable=[g for g in gene_ids if g in rows]
        if len(gene_ids)==1 and len(usable)==1:
            genes[symbol]={"axolotl_gene_id":usable[0],"log2_cpm_posterior_minus_anterior":effect(rows[usable[0]])}
        else:
            genes[symbol]={"status":"AMBIGUOUS_OR_UNQUANTIFIED_GENE_ID","candidate_ids":len(gene_ids),"quantified_ids":len(usable)}
    return {"features":count,"samples":len(names),"anterior_replicates":len(anterior),"posterior_replicates":len(posterior),"genes":genes}


def read_human(data,probes):
    sample_titles=[]
    sample_accessions=[]
    values={}
    selected_probes={p for r in probes.values() for p in r}
    in_table=False
    samples=[]
    found_rows=0
    with gzip.open(io.BytesIO(data),"rt",encoding="utf-8",errors="replace",newline="") as fh:
        for raw in fh:
            line=raw.strip()
            if line.startswith("!Sample_title"):
                sample_titles=next(csv.reader([line],delimiter="\t"))[1:]
            elif line.startswith("!Sample_geo_accession"):
                sample_accessions=next(csv.reader([line],delimiter="\t"))[1:]
            elif line=="!series_matrix_table_begin":
                in_table=True
            elif line=="!series_matrix_table_end":
                break
            elif in_table:
                rec=next(csv.reader([line],delimiter="\t"))
                if not samples:
                    samples=rec[1:]
                    continue
                found_rows+=1
                if rec[0] in selected_probes:
                    try:
                        v=[float(x) for x in rec[1:]]
                        if len(v)==len(samples) and all(math.isfinite(x) for x in v):
                            values[rec[0]]=v
                    except ValueError:continue
    title_by_gsm=dict(zip(sample_accessions,sample_titles))
    idx={}
    for i,s in enumerate(samples):
        title=title_by_gsm.get(s,"")
        m=re.search(r"Patient\s+(\d+),\s*(intact skin sample|3rd post-operative day sample)",title,re.I)
        if not m:continue
        patient=int(m.group(1))
        phase="baseline" if "intact" in m.group(2).lower() else "day3"
        idx.setdefault(patient,{})[phase]=i
    pairs={k:v for k,v in idx.items() if {"baseline","day3"}.issubset(v)}
    if len(pairs)<3:raise ValueError("fewer than three paired human patients")
    genes={}
    for gene,gene_probes in probes.items():
        usable=sorted(p for p in gene_probes if p in values)
        if not usable:
            genes[gene]={"status":"NO_ANNOTATED_QUANTIFIED_PROBE"}
            continue
        paired_changes=[]
        for p,s in sorted(pairs.items()):
            # Median of probe-level differences, not pseudoreplication of probes.
            effects=[values[q][s["day3"]]-values[q][s["baseline"]] for q in usable]
            paired_changes.append(statistics.median(effects))
        genes[gene]={
            "paired_patients":len(paired_changes),
            "probes_used":len(usable),
            "log2_array_day3_minus_intact":round(statistics.median(paired_changes),4),
            "patient_effects":[round(z,4) for z in paired_changes],
            "statistic":"median of patient-paired changes; probe median per patient",
        }
    return {"features":found_rows,"samples":len(samples),"paired_patients":len(pairs),"genes":genes}


def orthology_check(candidates):
    results={}
    for gene in ORTHO_CHECK:
        if len(candidates.get(gene,[]))!=1:
            results[gene]={"status":"UNVERIFIED_GTF_AMBIGUITY"}
            continue
        try:
            source=ncbi_exact_gene("Ambystoma mexicanum",gene)
            if not source or norm(source.get("symbol"))!=norm(gene):
                results[gene]={"status":"UNVERIFIED_NCBI_AXOLOTL_EXACT"}
                continue
            matches=ncbi_human_orthologs(source["gene_id"])
            targets=sorted({r["ensembl_id"] for r in matches if norm(r.get("symbol"))==norm(gene)})
            results[gene]={
                "status":"NCBI_ORTHOLOGY_SUPPORTED" if len(targets)==1 else "UNVERIFIED_ORTHOLOGY_MULTIPLICITY",
                "ncbi_source_gene_id":source["gene_id"],"human_ensembl_ids":targets,
                "caveat":"No exact sequence/accession mapping of historical AMEX60DD to NCBI reference established; not a fully verified gene-pair identity.",
            }
        except Exception as e:
            results[gene]={"status":"UNVERIFIED_PROVIDER_UNAVAILABLE","error_type":type(e).__name__}
    return results


def build(data,metadata):
    annot=parse_annotation(data["GPL570"])
    cross=parse_gtf(data["AmexT_v47"])
    axolotl=read_axolotl(data["GSE284768"],cross)
    human=read_human(data["GSE28914"],annot)
    ortho=orthology_check(cross)
    table=[]
    for gene in PANEL:
        table.append({
            "gene":gene,
            "axolotl":axolotl["genes"].get(gene,{"status":"NOT_ANNOTATED_WITH_UNIQUE_HUMAN_TAG"}),
            "human":human["genes"].get(gene,{"status":"NOT_QUANTIFIED"}),
            "orthology":ortho.get(gene,{"status":"NOT_IN_INDEPENDENT_VERIFICATION_PANEL"}),
            "contrast_comparability":"NOT_COMPARABLE",
        })
    report={
        "schema":"BIO-MIMIC-X/EXPLORATORY-TRANSCRIPTOMIC/1",
        "date":"2026-11-01",
        "status":"PARTIAL_NOT_COMPARABLE",
        "datasets":metadata,
        "data_type":"actual raw axolotl counts + publicly processed human microarray, NOT synthetic",
        "experimental_comparisons":{
            "axolotl":"15 dpa anterior vs posterior blastema cells, 4 vs 4 biological replicate labels",
            "human":"intact vs day-3 wound human whole skin, paired patients",
        },
        "quality":{"axolotl_features":axolotl["features"],"axolotl_samples":axolotl["samples"],
                   "axolotl_4x4_verified":axolotl["anterior_replicates"]==4 and axolotl["posterior_replicates"]==4,
                   "human_features":human["features"],"human_samples":human["samples"],
                   "human_paired_patients":human["paired_patients"],
                   "axolotl_human_orthology":"HISTORICAL_GTF_HUMAN_TAG_ONLY_WITH_NCBI_SYMBOL_CHECK; EXACT AMEX IDENTIFIER LINK UNVERIFIED"},
        "panel_genes":list(PANEL),
        "results":table,
        "interpretation":"Within-species exploratory contrasts quantified. Due to different tissues, sampling times and biological contrasts, no valid cross-species correlation or regenerative-efficacy claim.",
        "whole_human_limb_regeneration":"UNVERIFIED",
        "negative_control":"No cross-species concordance statistic computed for non-matched injury-vs-positional contrasts.",
        "independent_replication":"UNVERIFIED",
    }
    report["sha256"]=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    return report


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--write",action="store_true")
    args=p.parse_args()
    raw={}
    metadata={}
    failures={}
    for name in URLS:
        try:
            raw[name],metadata[name]=fetch(name)
            print("INPUT_VERIFIED "+json.dumps({"name":name,**metadata[name]},sort_keys=True))
        except Exception as e:
            failures[name]=str(e)[:200]
            print("INPUT_FAILED "+json.dumps({"name":name,"error":failures[name]}))
    if failures:
        result={"status":"PARTIAL_SOURCE_FAILURE","failed_sources":failures,"verified_sources":metadata,"whole_human_limb_regeneration":"UNVERIFIED"}
    else:
        try: result=build(raw,metadata)
        except Exception as e:
            result={"status":"FAIL_ANALYSIS","exception":type(e).__name__,"detail":str(e)[:200],"verified_sources":metadata}
    print("AXOLOTL_HUMAN_RESULT "+json.dumps(result,sort_keys=True,ensure_ascii=False))
    if args.write:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return 0 if result["status"] in {"PARTIAL_NOT_COMPARABLE","PARTIAL_SOURCE_FAILURE"} else 1


if __name__=="__main__":
    raise SystemExit(main())
