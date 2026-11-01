#!/usr/bin/env python3
"""NCBI sequence-window alignment for historical axolotl AMEX60DD030069.

Quantifies alignments vs *both* modern HAND1 and HAND2. It is NOT a
genome-wide reciprocal best-hit test or a clinical efficacy claim.
Uses bounded exact-accession NCBI FASTA and an explicit sequence-hash manifest.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from validation.hand2_assembly_sequence_probe import fasta_from_ncbi,reverse_complement

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"reports/factory/HAND1-HAND2-ALIGNMENT-LATEST.json"
SEQUENCES={
 "historic": {
  "accession":"CM010932.2","start":632140538,"end":632169448,
  "sha256":"9d2c183a94e9feeb2ed6b413e1654e4d54a614f0ed5ada64b52db2dcaf2eb4ce",
  "gene":"AMEX60DD030069",
  "assembly":"GCA_002915635.3",
 },
 "hand1": {
  "accession":"NC_090926.1","start":348891291,"end":348920140,
  "sha256":"99058cb5ba540e21359efbdd2dd047efb692cb8f47d731ec775ba7cbfeef9d8c",
  "gene":"138582569",
  "assembly":"GCF_040938575.1",
 },
 "hand2": {
  "accession":"NC_090937.1","start":910028725,"end":910032936,
  "sha256":"eb707084770ecfd0c24538f10984563b8cddfc0fe467db96454a36fa516505b3",
  "gene":"138516365",
  "assembly":"GCF_040938575.1",
 },
}
CIGAR=re.compile(r"(\d+)([=XID])")


def check_input_bases(name,seq):
    m=SEQUENCES[name]
    if not re.fullmatch("[ACGTN]+",seq):
        raise ValueError("invalid DNA letters: "+name)
    if len(seq)!=(m["end"]-m["start"]+1):
        raise ValueError("unexpected sequence length: "+name)
    sha=hashlib.sha256(seq.encode()).hexdigest()
    if sha!=m["sha256"]:
        raise ValueError("sequence hash mismatch: "+name)
    return sha


def cigar_counts(cigar):
    """Summarize extended CIGAR without manufacturing an identity estimate."""
    if not isinstance(cigar,str) or not cigar:
        raise ValueError("missing extended CIGAR")
    parts=CIGAR.findall(cigar)
    if "".join(n+op for n,op in parts)!=cigar:
        raise ValueError("malformed extended CIGAR")
    counts={op:0 for op in "=XID"}
    for n,op in parts:
        counts[op]+=int(n)
    if not counts["="]:
        raise ValueError("no matching nucleotides")
    return counts


def align_window(query,target,edlib):
    """HW = align whole gene query against a substring of old locus target."""
    hits=[]
    for strand,sequence in (("+",query),("-",reverse_complement(query))):
        r=edlib.align(sequence,target,mode="HW",task="path")
        d=r.get("editDistance",-1)
        if d<0 or not r.get("locations") or not r.get("cigar"):
            raise ValueError("edlib could not align full query")
        counts=cigar_counts(r["cigar"])
        if d!=(counts["X"]+counts["I"]+counts["D"]):
            raise ValueError("extended CIGAR edit-distance mismatch")
        aligned_columns=sum(counts.values())
        if not aligned_columns:
            raise ValueError("empty alignment")
        spans=[{"start_0based":int(i),"end_0based_inclusive":int(j)}
               for i,j in r["locations"][:10]]
        hits.append({
            "strand":strand,"edit_distance":int(d),"counts":counts,
            "aligned_columns":aligned_columns,
            "fraction_matching_in_alignment":round(counts["="]/aligned_columns,6),
            "query_bases":len(sequence),"target_bases":len(target),
            "location_candidates":spans,
            "locations_truncated":len(r["locations"])>10,
        })
    hits.sort(key=lambda x:(x["edit_distance"],-x["fraction_matching_in_alignment"],x["strand"]))
    return {"best":hits[0],"other_strand":hits[1]}


def global_window(query,target,edlib):
    """Global alignment is supplementary and highly length-sensitive."""
    hits=[]
    for strand,seq in (("+",query),("-",reverse_complement(query))):
        result=edlib.align(seq,target,mode="NW",task="path")
        counts=cigar_counts(result["cigar"])
        if result["editDistance"] != counts["X"]+counts["I"]+counts["D"]:
            raise ValueError("NW extended CIGAR mismatch")
        hits.append({"strand":strand,"edit_distance":int(result["editDistance"]),
                     "matching_bases":counts["="],
                     "mismatches":counts["X"],
                     "indel_bases":counts["I"]+counts["D"],
                     "global_aligned_identity":round(counts["="]/sum(counts.values()),6)})
    return min(hits,key=lambda x:(x["edit_distance"],-x["global_aligned_identity"]))


def summarize(aligned):
    h1=aligned["hand1"]["local"]["best"]
    h2=aligned["hand2"]["local"]["best"]
    fav="HAND1" if (h1["fraction_matching_in_alignment"] >
                    h2["fraction_matching_in_alignment"]) else "UNRESOLVED"
    return {
        "schema":"BIO-MIMIC-X/NCBI-HAND-LOCUS-ALIGNMENT/1",
        "method":"edlib 1.3.9.post1 / HW both strands; NW global supplementary",
        "sequence_sources":SEQUENCES,
        "results":aligned,
        "stronger_local_alignment":fav,
        "old_locus_to_new_gene_exact_identity":"UNVERIFIED",
        "status":"PARTIAL_LOCUS_CANDIDATE_COMPARISON",
        "limitations":[
            "Only two modern gene windows; this is not a whole-genome reciprocal best-hit or unique-locus assignment.",
            "HW comparisons with different gene-window lengths can be biased: compare edit counts and matched-base fractions with coverage context.",
            "Gene-window identity is not transcript exon orthology and not biological/clinical efficacy.",
            "A successful alignment does not resolve provenance rights, assay reproducibility or commercial valuation.",
        ],
        "independent_curator_confirmation":"UNVERIFIED",
    }


def calculate(fetcher=fasta_from_ncbi):
    result={}
    seqs={}
    faults={}
    for name,m in SEQUENCES.items():
        try:
            seq,receipt=fetcher(m["accession"],m["start"],m["end"])
            check_input_bases(name,seq)
            seqs[name]=seq
            result[name]={"fasta":receipt,"length":len(seq),"sha256":m["sha256"]}
        except Exception as exc:
            faults[name]=type(exc).__name__+": "+str(exc)[:250]
    if faults:
        return {
            "schema":"BIO-MIMIC-X/NCBI-HAND-LOCUS-ALIGNMENT/1",
            "status":"PARTIAL_SOURCE_FAILURE",
            "sources":result,"failed_sources":faults,
            "old_locus_to_new_gene_exact_identity":"UNVERIFIED",
            "independent_curator_confirmation":"UNVERIFIED",
        }
    import edlib
    aligned={}
    for gene in ("hand1","hand2"):
        aligned[gene]={
            "local":align_window(seqs[gene],seqs["historic"],edlib),
            "global":global_window(seqs[gene],seqs["historic"],edlib),
        }
    out=summarize(aligned)
    out["sources"]=result
    out["edlib_version"]=getattr(edlib,"__version__","1.3.9.post1")
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",action="store_true")
    args=ap.parse_args()
    try:
        report=calculate()
    except Exception as exc:
        report={
            "schema":"BIO-MIMIC-X/NCBI-HAND-LOCUS-ALIGNMENT/1",
            "status":"FAIL_ALIGNMENT",
            "error":type(exc).__name__+": "+str(exc)[:300],
            "old_locus_to_new_gene_exact_identity":"UNVERIFIED",
            "independent_curator_confirmation":"UNVERIFIED",
        }
    report["sha256"]=hashlib.sha256(json.dumps(
        report,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
    print("HAND1_HAND2_ALIGNMENT "+json.dumps(report,sort_keys=True,ensure_ascii=False))
    if args.write:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        OUTPUT.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    return 0 if report["status"] in ("PARTIAL_SOURCE_FAILURE","PARTIAL_LOCUS_CANDIDATE_COMPARISON") else 1


if __name__=="__main__":
    raise SystemExit(main())
