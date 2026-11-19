#!/usr/bin/env python3
"""Exact necessary q-gram bound + bitparallel semiglobal Levenshtein on every
window identified by a necessary pigeonhole seed from an authenticated assembly.
No source FASTA is uploaded; report contains summary only.

If all of (a) verified complete reference, (b) exhaustive 176 disjoint seeds,
(c) all seed-hit windows, and (d) every window evaluated pass, then no unreported
alignment with <=175 edits can exist under the selected DNA semiglobal model.
This does NOT prove biological orthology or exclude distant/partial homologs.
"""
import argparse,hashlib,json,sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
RC=bytes.maketrans(b"ACGTN",b"TGCAN")

@lru_cache(maxsize=8)
def _cached_qgram_counts(query:bytes,k:int):
    return Counter(query[i:i+k] for i in range(len(query)-k+1))

def necessary_qgram_count(query:bytes,target:bytes,k=12):
    qcount=_cached_qgram_counts(query,k)
    available={target[i:i+k] for i in range(len(target)-k+1)}
    observed=sum(count for kmer,count in qcount.items() if kmer in available)
    return observed,len(query)-k+1

def myers_semiglobal(query:bytes,target:bytes):
    """Fully align all query to a contiguous substring of target, free target ends.
    Bitparallel DP using Python arbitrary-width integers, substitution/indel=1.
    """
    n=len(query);allbits=(1<<n)-1;top=1<<(n-1)
    peq={}
    for i,c in enumerate(query):peq[c]=peq.get(c,0)|(1<<i)
    vp=allbits;vn=0;score=n;best=score
    for c in target:
        eq=peq.get(c,0)
        x=eq|vn
        d0=(((eq&vp)+vp)^vp)|eq|vn
        hp=vn|~(d0|vp)
        hn=vp&d0
        if hp&top:score+=1
        elif hn&top:score-=1
        hp<<=1;hn<<=1
        vp=(hn|~(x|hp))&allbits
        vn=(d0&hp)&allbits
        if score<best:best=score
    return best

def score_one(query,window,threshold=175,qgram_k=12):
    necessary,allq=necessary_qgram_count(query,window,qgram_k)
    lower=allq-threshold*qgram_k
    if necessary<lower:
        return {"status":"EXCLUDED_BY_NECESSARY_QGRAM_BOUND",
                "qgram_count":necessary,"qgram_cutoff":lower,"distance":None}
    distance=myers_semiglobal(query,window)
    return {"status":"MATCH_WITHIN_CUTOFF" if distance<=threshold else "EXCLUDED_BY_EXACT_EDIT_DISTANCE",
            "qgram_count":necessary,"qgram_cutoff":lower,"distance":distance}

def fasta_records(path):
    with path.open("rb") as f:
        while True:
            h=f.readline()
            if not h:break
            if not h.startswith(b">cand_"):raise ValueError("candidate header mismatch")
            try:i=int(h.strip().split(b"_")[1])
            except Exception as e:raise ValueError("bad candidate id") from e
            seq=f.readline().strip().upper()
            if not seq or any(c not in b"ACGTN" for c in seq):
                raise ValueError("invalid candidate DNA")
            yield i,seq
def run(query_path,windows_path,candidates_path,max_edits=175):
    reference=json.loads(candidates_path.read_text())
    if reference["max_edits"]!=max_edits:raise ValueError("threshold mismatch")
    seq=b"".join(query_path.read_bytes().splitlines()[1:]).upper()
    if len(seq)!=reference["query_length"]:raise ValueError("query length mismatch")
    if any(c not in b"ACGT" for c in seq):raise ValueError("non-ACGT query")
    reverse=seq.translate(RC)[::-1]
    candidates=reference["candidates"]
    seen=set();passing=[];stats=Counter();min_distance=None
    for i,target in fasta_records(windows_path):
        if i in seen or i<0 or i>=len(candidates):
            raise ValueError("duplicate/unknown candidate id")
        seen.add(i)
        c=candidates[i]
        if c["candidate_id"]!=i:raise ValueError("candidate mismatch")
        if len(target)!=(c["reference_interval_0based"][1]-c["reference_interval_0based"][0]):
            raise ValueError("candidate extracted sequence length mismatch")
        oriented=seq if c["strand"]=="+" else reverse
        result=score_one(oriented,target,max_edits)
        stats[result["status"]]+=1
        if result["distance"] is not None:
            if min_distance is None or result["distance"]<min_distance:min_distance=result["distance"]
        if result["status"]=="MATCH_WITHIN_CUTOFF":
            passing.append({"candidate_id":i,"accession":c["reference"],"role":c["role"],
                "strand":c["strand"],"edit_distance":result["distance"],
                "reference_interval_0based":c["reference_interval_0based"],
                "seed_hit_count":c["seed_hit_count"],
                "extracted_window_sha256":hashlib.sha256(target).hexdigest()})
    if len(seen)!=len(candidates):raise ValueError("NOT_ALL_CANDIDATES_TESTED")
    return {"schema":"BIO-MIMIC-X/WHOLE-GENOME-175-EDIT-NECESSARY-SEED-EXHAUSTIVE-WINDOW-GATE/1",
        "status":"PASS_ALL_SEEDED_WINDOWS_TESTED" if seen else "UNVERIFIED_NO_SEEDS",
        "reference_bases":reference["reference_bases"],
        "reference_accessions":reference["complete_reference_inventory"],
        "unplaced_unlocalized_accessions":reference["unplaced_unlocalized_references"],
        "query_sha256":hashlib.sha256(seq).hexdigest(),
        "candidates_manifest_sha256":hashlib.sha256(candidates_path.read_bytes()).hexdigest(),
        "windows_fasta_sha256":hashlib.sha256(windows_path.read_bytes()).hexdigest(),
        "threshold":max_edits,"total_candidates_tested":len(seen),
        "method_counts":dict(stats),"passing":passing,
        "min_distance_among_exactly_evaluated":min_distance,
        "genome_wide_necessary_seed_coverage":"PENDING_PAIRED_STREAM_BASE_COUNT_AND_FAILURE_GATE",
        "biological_orthology_or_function":"UNVERIFIED",
        "limitations":["Exact whole-query DNA semiglobal <=175 unit-edit screen only.",
         "This does NOT exclude truncated genes, alignments with >175 edits, complex rearrangements, structural differences, or distant paralogs.",
         "Genome completeness and accession provenance must be checked separately from this scoring stage.",
         "Liftoff annotation comparison and independent biological curation have not been performed."]}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 for item in ["query","windows","candidates","output"]:p.add_argument("--"+item,required=True,type=Path)
 a=p.parse_args()
 result=run(a.query,a.windows,a.candidates)
 a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print("STRICT_EVALUATION",result["status"],"tested",result["total_candidates_tested"],
       "passes",len(result["passing"]),"counts",result["method_counts"])
 for x in result["passing"][:30]:print("MATCH",x["accession"],x["strand"],x["edit_distance"],x["reference_interval_0based"])
