#!/usr/bin/env python3
"""Published epigenetic clock values joined to GEO RNA experiment identifiers.
No protected gene counts, causal or same-aliquot assertions.
"""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validation.gse179849_public_multimodal_gate import (
    read_public,read_geo_matrix_metadata,join_series,GEO,FIG_API,FILE_ID,
)

def numeric(x):
    try:
        f=float(x)
        return round(f,5) if math.isfinite(f) else None
    except (TypeError,ValueError):
        return None

def main():
    meta_bytes,_=read_public(FIG_API,100_000)
    meta=json.loads(meta_bytes)
    assert meta["license"]["name"]=="CC BY 4.0" and meta["is_public"]
    file=next(f for f in meta["files"] if f["id"]==FILE_ID)
    raw,_=read_public(file["download_url"],5_000_000)
    assert hashlib.md5(raw).hexdigest()==file["computed_md5"]
    records=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    assert len(records)==1919
    bykey={}
    for row in records:
        key=(row.get("Unique_variable_name_new") or "").strip()
        if key:bykey.setdefault(key,[]).append(row)
    sources={}
    for assay,url in GEO.items():
        contents,_=read_public(url,3_000_000)
        sources[assay]=read_geo_matrix_metadata(contents)
    matches=join_series(sources["DNA"],sources["RNA"])
    if len(matches)!=109:raise ValueError("new GEO samples or sample title drift")
    results=[]
    for p in matches:
        for r in bykey.get(p["join_key"],[]):
            clocks={name:numeric(r.get(name)) for name in
                ("Horvath1","Horvath2","PhenoAge","PCHorvath2","PCPhenoAge","GrimAge")}
            seq=(r.get("RNAseq_ID") or "").strip()
            if not any(v is not None for v in clocks.values()) and not seq:
                continue
            results.append({"DNA_GSM":p["DNA_GSM"],"RNA_GSM":p["RNA_GSM"],
                "sample_key":p["join_key"],"RNAseq_ID":seq,
                "RNAseq_ID_present":bool(seq),
                "clocks":clocks,
                "cell_line":r.get("Cell_line_new"),
                "passage":numeric(r.get("Passage")),
                "same_physical_aliquot_proven":False})
    clocked=[x for x in results if any(v is not None for v in x["clocks"].values())]
    both=[x for x in clocked if x["RNAseq_ID_present"]]
    result={
        "schema":"BIO-MIMIC-X/GSE179849-GEO-PAIRED-CLOCKS/1",
        "source":"10.6084/m9.figshare.18441998.v2 CC BY 4.0; NCBI GEO GSE179847/GSE179848",
        "source_bytes_sha256":hashlib.sha256(raw).hexdigest(),
        "metadata_conditions_exactly_matched":len(matches),
        "figshare_rows":len(records),"rows_with_published_clock":len(clocked),
        "rows_with_published_clock_and_RNAseq_identifier":len(both),
        "RNA_expression_gene_counts_obtained":False,
        "methylation_individual_beta_values_obtained":False,
        "independent_identity_adjusted_aging":"UNVERIFIED",
        "status":"PASS_PUBLIC_CROSS_MODALITY_CONDITION_AND_PUBLISHED_CLOCK" if clocked else "PARTIAL_NO_PUBLISHED_CLOCK",
        "observations":results
    }
    out=Path("qa-artifacts/GSE179849-PUBLISHED-AGE-RNA-GSM-BRIDGE.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\\n",encoding="utf8")
    print("BIO_MIMIC_AGING_GEO_FIGSHARE_REAL_BRIDGE "+json.dumps({
        k:v for k,v in result.items() if k!="observations"},ensure_ascii=False))
    if not clocked:raise SystemExit(2)

if __name__=="__main__":main()
