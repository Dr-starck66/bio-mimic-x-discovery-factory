#!/usr/bin/env python3
"""HAND2 legacy AMEX60DD ↔ NCBI ↔ human evidence gate (not a therapy claim).

Distinguishes unique symbol annotation, verified NCBI species gene,
NCBI orthology and **unverified** exact old-locus/current-RefSeq linkage.
Read-only public sources, no speculative equivalences.
"""
from __future__ import annotations
import argparse, gzip, hashlib, io, json, re, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/factory/HAND2-LEGACY-CROSSWALK-2026-11-01.json"
GTF_URL="https://www.axolotl-omics.org/dl/AmexT_v47-AmexG_v6.0-DD.gtf.gz"
EXPECTED_GTF_SHA256="cc0c3c4e39f3afedcbe2bc5aad1d63fc461714aeb75051f4d109390455874c5d"
LEGACY="AMEX60DD030069"
EXPECTED_NCBI_GENE="138516365"
HUMAN_ENSEMBL="ENSG00000164107"
ALLOWED_HUMAN_SYMBOL="HAND2"

def collect_gtf_proof(data:bytes)->dict:
    """Read only gene/transcript evidence; avoid gene-name = cross-assembly identity."""
    found=[]
    all_hand2_gene_ids=set()
    target_gene_rows=[]
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
        for raw in stream:
            ln=raw.decode("utf-8",errors="replace").rstrip("\n")
            if ln.startswith("#"):continue
            cols=ln.split("\t")
            if len(cols)<9 or cols[2] not in {"gene","transcript"}:continue
            attributes=cols[8]
            g=re.search(r'gene_id "([^"]+)"',attributes)
            name=re.search(r'gene_name "([^"]+)"',attributes)
            if not g:continue
            gid=g.group(1)
            nm=name.group(1) if name else ""
            matched=re.findall(r'(?<![A-Za-z0-9])HAND2\s*\[hs\]',nm,re.I)
            if cols[2]=="gene" and matched:
                all_hand2_gene_ids.add(gid)
            if gid!=LEGACY:continue
            record={"feature":cols[2],"chr":cols[0],"start_1based":int(cols[3]),
                "end_1based":int(cols[4]),"strand":cols[6],"gene_id":gid,
                "gene_name":nm}
            tr=re.search(r'transcript_id "([^"]+)"',attributes)
            if tr:record["transcript_id"]=tr.group(1)
            if cols[2]=="gene":target_gene_rows.append(record)
            if len(found)<25:found.append(record)
    gene_row=(target_gene_rows[0] if len(target_gene_rows)==1 else None)
    status="UNIQUE_LEGACY_HAND2_SYMBOL_ANNOTATION" if (
        gene_row is not None
        and all_hand2_gene_ids=={LEGACY}
        and re.search(r'(?<![A-Za-z0-9])HAND2\s*\[hs\]',gene_row["gene_name"],re.I)
    ) else "UNVERIFIED_MULTIPLE_OR_MISSING_LEGACY_ANNOTATION"
    return {"status":status,"gene_rows_for_legacy":len(target_gene_rows),
        "distinct_hand2_human_tagged_gene_ids":sorted(all_hand2_gene_ids),
        "target_gene":gene_row,"target_records":found}

def fetch_gtf()->tuple[bytes,str]:
    req=urllib.request.Request(GTF_URL,headers={"User-Agent":"BIO-MIMIC-X/legacy-crosswalk/1.0","Accept":"application/gzip"})
    with urllib.request.urlopen(req,timeout=90) as r:
        raw=r.read(60_000_001)
    if len(raw)>60_000_000:raise RuntimeError("GTF exceeds size cap")
    if not raw.startswith(b"\x1f\x8b"):raise RuntimeError("GTF not gzip")
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=EXPECTED_GTF_SHA256:raise RuntimeError("unexpected GTF SHA256 revision")
    return raw,sha

def collect_ncbi()->dict:
    # API wrappers are already used by the project for exact species and NCBI orthology.
    import sys
    sys.path.insert(0,str(ROOT/"factory"))
    from human_bridge import ncbi_exact_gene,ncbi_human_orthologs
    source=ncbi_exact_gene("Ambystoma mexicanum","HAND2")
    if not source:
        return {"status":"UNVERIFIED_SOURCE_GENE","reason":"No exact NCBI gene found"}
    # Ignore an apparently matching symbol from a different species or gene.
    if str(source.get("gene_id"))!=EXPECTED_NCBI_GENE or str(source.get("symbol","")).upper()!="HAND2":
        return {"status":"UNVERIFIED_ID_OR_SYMBOL","source_gene":source}
    orths=ncbi_human_orthologs(EXPECTED_NCBI_GENE)
    correct=[x for x in orths if
        x.get("ensembl_id")==HUMAN_ENSEMBL and
        str(x.get("symbol","")).upper()==ALLOWED_HUMAN_SYMBOL]
    return {"status":"NCBI_AXOLOTL_TO_HUMAN_ORTHOLOGY_VERIFIED" if len(correct)==1 else "UNVERIFIED_NCBI_HUMAN_ORTHOLOGY",
        "source_gene":source,"human_orthology_hits":correct,
        "other_human_hits_count":len(orths)-len(correct)}

def compile_receipt(gtf:dict,ncbi:dict,source_sha:str)->dict:
    legacy_annotation_verified=(gtf.get("status")=="UNIQUE_LEGACY_HAND2_SYMBOL_ANNOTATION")
    ncbi_orthology_verified=ncbi.get("status")=="NCBI_AXOLOTL_TO_HUMAN_ORTHOLOGY_VERIFIED"
    # No provider result in this pipeline cross-references the AMEX60DD gene ID
    # to the modern NCBI gene ID by sequence, reciprocal alignment, or liftover.
    old_new_exact_verified=False
    result={
       "schema":"BIO-MIMIC-X/HAND2-LEGACY-CROSSWALK/1",
       "legacy_assembly":"AmexG_v6.0-DD",
       "legacy_transcriptome":"AmexT_v47",
       "legacy_id":LEGACY,"modern_ncbi_gene_id":EXPECTED_NCBI_GENE,
       "human_ensembl":HUMAN_ENSEMBL,
       "reference_gtf":{"url":GTF_URL,"sha256":source_sha,"proof":gtf},
       "ncbi":ncbi,
       "legacy_annotation_status":"PASS" if legacy_annotation_verified else "UNVERIFIED",
       "ncbi_species_to_human_orthology_status":"PASS" if ncbi_orthology_verified else "UNVERIFIED",
       "legacy_id_to_modern_ncbi_gene_exact_identity":"UNVERIFIED",
       "reason":"A shared gene symbol across different assembly versions, even with NCBI orthology, is not an exact historic-to-modern gene-ID crosswalk; no reciprocal sequence-alignment or assembly liftover was performed.",
       "negative_control":"Do not upgrade exact crosswalk based only on any number of text-symbol coincidences.",
       "no_clinical_efficacy_claim":True,
       "decision":"PARTIAL" if legacy_annotation_verified and ncbi_orthology_verified else "UNVERIFIED",
       "required_next_proof":"Independent exact-sequence/accession link between AMEX60DD030069 and NCBI Gene 138516365, with paralog and reciprocal-hit controls.",
    }
    result["sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--write",action="store_true")
    a=p.parse_args()
    source=None; gtf={}; ncbi={}; faults={}
    try:
        raw,source=fetch_gtf()
        gtf=collect_gtf_proof(raw)
    except Exception as e:
        faults["gtf"]=type(e).__name__+": "+str(e)[:180]
    try:ncbi=collect_ncbi()
    except Exception as e:faults["ncbi"]=type(e).__name__+": "+str(e)[:180]
    report=compile_receipt(gtf,ncbi,source)
    report["upstream_failures"]=faults
    print("HAND2_CROSSWALK_EVIDENCE "+json.dumps(report,sort_keys=True,ensure_ascii=False))
    if a.write:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
