#!/usr/bin/env python3
"""One-shot public age-focused RNA expression adjustment (no protected data).

Uses only author-submitted GSE179848 normalized RNA and verified public
Figshare DNAm clock values joined at the same biological sampling condition.
No formal causal rejuvenation inference; only three control donor lines.
"""
import csv,gzip,hashlib,json,math,statistics,tempfile,urllib.request
from pathlib import Path

SRC="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE179nnn/GSE179848/suppl/GSE179848_processed_cell_lifespan_RNAseq_data.csv.gz"
EXPECTED=60622846
MARKERS=("COL1A1","COL1A2","DCN","LUM","FN1","THY1","CDKN1A","CDKN2A",
         "LMNB1","IL6","CXCL8","GDF15","ATF4","DDIT3")
FIBRO=("COL1A1","COL1A2","DCN","LUM","FN1","THY1")
INPUT=Path("qa-artifacts/GSE179849-PUBLISHED-AGE-RNA-GSM-BRIDGE.json")
OUT=Path("qa-artifacts/GSE179849-REAL-RNA-IDENTITY-AGE-ADJUSTMENT.json")
def retrieve(path):
    failures=[]
    attempts=[{},{"Range":"bytes=0-"+str(EXPECTED-1)}]
    for opts in attempts:
        headers={"User-Agent":"BIO-MIMIC-X-public-GEO-scientific/1","Accept-Encoding":"identity",**opts}
        req=urllib.request.Request(SRC,headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=100) as r,open(path,"wb") as dest:
                if r.status not in (200,206):raise ValueError("unexpected status")
                total=0; sha=hashlib.sha256()
                while chunk:=r.read(1<<20):
                    total+=len(chunk)
                    if total>EXPECTED:raise ValueError("exceeds exact original GEO source size")
                    sha.update(chunk);dest.write(chunk)
                if total!=EXPECTED:raise ValueError("truncated source file")
                if r.status==206 and r.headers.get("Content-Range")!=f"bytes 0-{EXPECTED-1}/{EXPECTED}":
                    raise ValueError("invalid original complete HTTP range")
            with gzip.open(path,"rb") as f:
                while f.read(1<<20):pass  # validate entire gzip CRC
            return {"sha256":sha.hexdigest(),"compressed_bytes":total,
                "gzip_crc":"PASS","http_status":r.status}
        except Exception as e:failures.append(type(e).__name__+": "+str(e)[:170])
    raise RuntimeError("public RNA GET/Range failed: "+repr(failures))
def extract(path,records):
    wanted=set("Sample_"+str(x["RNAseq_ID"]) for x in records)
    with gzip.open(path,"rt",encoding="utf-8-sig",newline="") as stream:
        rows=csv.reader(stream)
        hdr=next(rows)
        if hdr[0] not in ("","X"):raise ValueError("not R write.csv gene matrix")
        columns={x:i for i,x in enumerate(hdr) if i>0}
        if not wanted.issubset(columns):raise ValueError("source lacks RNA sample IDs in Figshare")
        labels={};genes_seen=set();gene_rows=0
        for row in rows:
            if not row:continue
            gene_rows+=1
            if len(row)!=len(hdr):raise ValueError("RNA matrix width changed")
            gene=row[0]
            if gene not in MARKERS:continue
            if gene in genes_seen:raise ValueError("duplicate gene marker "+gene)
            genes_seen.add(gene)
            expression={}
            for key in wanted:
                v=float(row[columns[key]])
                if not math.isfinite(v):raise ValueError("nonfinite real RNA expression")
                expression[key]=v
            labels[gene]=expression
    if gene_rows<10000 or len(set(FIBRO)&genes_seen)<4:
        raise ValueError("insufficient real fibro markers or gene rows")
    return labels,gene_rows
def slopes(obs):
    groups={}
    for x in obs:
        if "_Normal_Control_" in x["sample_key"]:
            groups.setdefault(x["sample_key"].rsplit("_p",1)[0],[]).append(x)
    control=[v for items in groups.values() if len(items)>=3 for v in items]
    if len(control)<25:raise ValueError("unverifiable healthy replicative series")
    x=[v["passage"] for v in control]
    y=[v["clocks"]["Horvath1"] for v in control]
    z=[v["RNA_fibroblast_score"] for v in control]
    if any(v is None for v in y):raise ValueError("published clock missing")
    keys=[v["sample_key"].rsplit("_p",1)[0] for v in control]
    def within(vec):
        means={k:statistics.mean(v for key,v in zip(keys,vec) if key==k) for k in set(keys)}
        return [v-means[k] for k,v in zip(keys,vec)]
    a,b,c=within(x),within(y),within(z)
    sxx=sum(v*v for v in a);sxz=sum(v*w for v,w in zip(a,c))
    szz=sum(v*v for v in c);sxy=sum(v*w for v,w in zip(a,b))
    szy=sum(v*w for v,w in zip(c,b))
    if sxx<0.1 or szz<1e-4:raise ValueError("RNA/culture time not identifiable")
    det=sxx*szz-sxz*sxz
    if det<1e-6:raise ValueError("multicollinear RNA identity and passage")
    unadjusted=sxy/sxx
    adjusted=(sxy*szz-szy*sxz)/det
    return {"n_control_samples":len(control),"n_control_series":len(set(keys)),
            "n_independent_healthy_donors":len(set(v["cell_line"] for v in control)),
            "published_Horvath1_slope_years_per_passage_before":round(unadjusted,6),
            "slope_after_independent_real_RNA_fibroblast_identity":round(adjusted,6),
            "method":"series-fixed-effect within-transform + 2-covariate OLS; descriptive only",
            "causal_rejuvenation":"UNVERIFIED","same_physical_aliquot":"UNVERIFIED"}
def main():
    result={"schema":"BIO-MIMIC-X/GSE179849-AGE-FOCUSED-RNA-ADJUSTMENT/1",
        "source":SRC,"status":"PARTIAL_SOURCE_UNAVAILABLE",
        "actual_RNA_gene_expression_values_obtained":False,
        "age_after_orthogonal_RNA_adjustment":"UNVERIFIED"}
    try:
        o=json.loads(INPUT.read_text())
        obs=o["observations"]
        if len(obs)!=102 or not all(v["RNAseq_ID"] for v in obs):
            raise ValueError("age-clock matched RNA identifiers are incomplete")
        with tempfile.TemporaryDirectory() as tmp:
            source=retrieve(Path(tmp)/"public_rna_vst.csv.gz")
            genes,gene_rows=extract(Path(tmp)/"public_rna_vst.csv.gz",obs)
        result["source_integrity"]=source
        result["RNA_gene_rows"]=gene_rows
        result["real_marker_genes"]=sorted(genes)
        fibro=[g for g in FIBRO if g in genes]
        for gene in fibro:
            vals=[genes[gene]["Sample_"+str(v["RNAseq_ID"])] for v in obs]
            mn=statistics.mean(vals);sd=statistics.stdev(vals)
            if sd<1e-7:raise ValueError("zero variance fibroblast gene")
            for entry,val in zip(obs,vals):
                entry.setdefault("RNA_fibroblast_components",{})[gene]=(val-mn)/sd
        for entry in obs:
            entry["RNA_fibroblast_score"]=statistics.mean(entry["RNA_fibroblast_components"].values())
        result["n_real_RNA_DNAM_clock_sample_conditions"]=len(obs)
        result["real_RNA_fibroblast_markers"]=fibro
        result["real_public_clock_and_RNA_sample_scores"]=obs
        result["control_aging_trajectory"]=slopes(obs)
        result["actual_RNA_gene_expression_values_obtained"]=True
        result["age_after_orthogonal_RNA_adjustment"]="PASS_DESCRIPTIVE_REPLICATIVE_FIBROBLAST_AGE_ASSOCIATION"
        result["status"]="PASS_REAL_AGE_FOCUSED_PUBLIC_RNA_AND_DNAM_CLOCK_ADJUSTMENT_NOT_CAUSAL"
    except Exception as exc:
        result["failure_reason"]=f"{type(exc).__name__}: {exc}"[:320]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding="utf8")
    print("BIO_MIMIC_AGE_FOCUSED_PUBLIC_ORTHOGONAL_RNA "+json.dumps({
        k:v for k,v in result.items() if k not in ("real_public_clock_and_RNA_sample_scores",)},ensure_ascii=False)[:3300])
if __name__=="__main__":main()
