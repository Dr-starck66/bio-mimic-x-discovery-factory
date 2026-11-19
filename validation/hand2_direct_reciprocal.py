#!/usr/bin/env python3
"""HAND2 axolotl candidate: exact-accession pairwise reciprocal window comparison.
Uses observed GTF candidate manifest (not name-based inferred identity).
Reciprocal here is *two alignment directions on two chosen windows*,
NOT reciprocal best hit across a whole genome or a curator confirmation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from validation.hand2_assembly_sequence_probe import fasta_from_ncbi
from validation.hand1_hand2_global_alignment import align_window,SEQUENCES,check_input_bases

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"reports/factory/HAND2-CHR6Q-OBSERVED-CANDIDATE-2026-11-05.json"
OUTPUT=ROOT/"reports/factory/HAND2-DIRECT-RECIPROCAL-LATEST.json"
EXPECTED_GTF_SHA="cc0c3c4e39f3afedcbe2bc5aad1d63fc461714aeb75051f4d109390455874c5d"
OLD_ID="AMEX60DD045298"
OLD_ACCESSION="CM010938.2"
OLD_BEGIN,OLD_END=884794726,884799066
MODERN_ID="138516365"
MODERN_ACCESSION="NC_090937.1"
MODERN_BEGIN,MODERN_END=910028725,910032936

def check_manifest(x:dict):
    old=x.get("candidate") or {}
    modern=x.get("modern") or {}
    neg=x.get("negative_control") or {}
    expected_old=("id","chromosome","accession","start_1based","end_1based","strand")
    actual_old=tuple(old.get(k) for k in expected_old)
    if actual_old!=(OLD_ID,"chr6q",OLD_ACCESSION,OLD_BEGIN,OLD_END,"+"):
        raise ValueError("Historic candidate provenance or coordinates changed")
    if old.get("assembly")!="GCA_002915635.3" or old.get("symbol")!="HAND2":
        raise ValueError("Historic source gene label/assembly mismatched")
    actual_mod=tuple(modern.get(k) for k in ("gene_id","accession","start_1based","end_1based","strand"))
    if actual_mod!=(MODERN_ID,MODERN_ACCESSION,MODERN_BEGIN,MODERN_END,"-"):
        raise ValueError("Modern HAND2 RefSeq provenance changed")
    if neg.get("gene_id")!="138582569" or neg.get("accession")!="NC_090926.1":
        raise ValueError("HAND1 negative control changed")
    if x.get("gtf_sha256")!=EXPECTED_GTF_SHA or x.get("scientific_identity")!="UNVERIFIED":
        raise ValueError("GTF source hash / proof-gate mismatch")
    if int(x.get("observed_artifact_id",0))!=13411887589:
        raise ValueError("Original GitHub run artifact provenance changed")
    return True

def _validate_bases(seq,expected_length,name):
    import re
    if not isinstance(seq,str) or len(seq)!=expected_length or not re.fullmatch("[ACGTN]+",seq):
        raise ValueError("Unexpected FASTA bases or genomic interval for "+name)
    return hashlib.sha256(seq.encode()).hexdigest()

def score_windows(old,modern_h2,modern_h1,aligner=align_window,edlib_module=None):
    if edlib_module is None:
        import edlib as edlib_module
    metrics={}
    for symbol,seq in (("HAND2",modern_h2),("HAND1_CONTROL",modern_h1)):
        modern_to_old=aligner(seq,old,edlib_module)["best"]
        old_to_modern=aligner(old,seq,edlib_module)["best"]
        metrics[symbol]={
          "modern_to_old":modern_to_old,
          "old_to_modern":old_to_modern,
          "modern_to_old_edit_rate":round(modern_to_old["edit_distance"]/len(seq),6),
          "old_to_modern_edit_rate":round(old_to_modern["edit_distance"]/len(old),6),
        }
    h2=metrics["HAND2"];h1=metrics["HAND1_CONTROL"]
    candidate_favored=(
        h2["modern_to_old_edit_rate"]<=0.10
        and h2["old_to_modern_edit_rate"]<=0.10
        and h1["old_to_modern_edit_rate"]-h2["old_to_modern_edit_rate"]>=0.20
    )
    return {"status":"PARTIAL_TARGETED_RECIPROCAL_WINDOWS",
            "metrics":metrics,"favors_HAND2_over_HAND1_in_tested_windows":candidate_favored,
            "whole_genome_uniqueness":"UNVERIFIED",
            "independent_curator_confirmation":"UNVERIFIED",
            "genome_wide_reciprocal_best_hit":"UNVERIFIED",
            "limitations":[
              "Selected two modern gene windows and one old candidate; not a genome-wide search.",
              "Edlib HW optimizes local placement of whole query; unequal lengths must be considered.",
              "Two directions do not prove orthology, exon structure, synteny or genome-wide uniqueness.",
              "HAND1 is a necessary negative control; it does not test all other paralogs.",
            ]}

def evaluate(manifest,fetcher=fasta_from_ncbi,aligner=align_window,edlib_module=None):
    check_manifest(manifest)
    specs={
      "legacy_HAND2_candidate":(OLD_ACCESSION,OLD_BEGIN,OLD_END),
      "modern_HAND2":(MODERN_ACCESSION,MODERN_BEGIN,MODERN_END),
      "modern_HAND1_control":(SEQUENCES["hand1"]["accession"],SEQUENCES["hand1"]["start"],SEQUENCES["hand1"]["end"]),
    }
    out={"schema":"BIO-MIMIC-X/HAND2-DIRECT-RECIPROCAL/1","status":"UNVERIFIED_SOURCE_FAILURE",
         "source_manifest_sha256":hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest(),
         "candidates":[OLD_ID],"fasta_source_receipts":{},"fasta_sha256":{},"source_failures":{},
         "scientific_identity":"UNVERIFIED","whole_genome_uniqueness":"UNVERIFIED",
         "curator_confirmation":"UNVERIFIED"}
    seqs={}
    for name,(accession,start,end) in specs.items():
        try:
            dna,proof=fetcher(accession,start,end)
            sha=_validate_bases(dna,end-start+1,name)
            if name=="modern_HAND2":check_input_bases("hand2",dna)
            if name=="modern_HAND1_control":check_input_bases("hand1",dna)
            seqs[name]=dna
            out["fasta_sha256"][name]=sha
            out["fasta_source_receipts"][name]=proof
        except Exception as ex:
            out["source_failures"][name]=type(ex).__name__+": "+str(ex)[:240]
    if out["source_failures"]:
        return out
    try:
        out["comparisons"]=score_windows(seqs["legacy_HAND2_candidate"],seqs["modern_HAND2"],
            seqs["modern_HAND1_control"],aligner,edlib_module)
        out["status"]="PARTIAL_TARGETED_RECIPROCAL_WINDOWS"
    except Exception as ex:
        out["status"]="FAIL_ALIGNMENT"
        out["alignment_error"]=type(ex).__name__+": "+str(ex)[:240]
    return out

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,default=MANIFEST)
    parser.add_argument("--out",type=Path,default=OUTPUT)
    args=parser.parse_args(argv)
    try:
        manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
        result=evaluate(manifest)
    except Exception as e:
        result={"schema":"BIO-MIMIC-X/HAND2-DIRECT-RECIPROCAL/1","status":"FAIL_INPUT_OR_IMPLEMENTATION",
         "error":type(e).__name__+": "+str(e)[:300],"scientific_identity":"UNVERIFIED"}
    result["receipt_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("HAND2_DIRECT_ALIGNMENT",json.dumps({"status":result["status"],
       "old_gene":OLD_ID,"fasta_sources_ok":len(result.get("fasta_sha256",{})),
       "failures":result.get("source_failures",{}),
       "favored":result.get("comparisons",{}).get("favors_HAND2_over_HAND1_in_tested_windows",None)}))
    return 0 if result["status"] in ("UNVERIFIED_SOURCE_FAILURE","PARTIAL_TARGETED_RECIPROCAL_WINDOWS") else 1

if __name__=="__main__":
    raise SystemExit(main())
