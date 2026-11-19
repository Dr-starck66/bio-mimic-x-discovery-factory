#!/usr/bin/env python3
"""Verify seed-screen candidate windows against NCBI FASTA using a capped
semiglobal Levenshtein dynamic program. No genome-wide best-hit claim.
"""
from __future__ import annotations
import hashlib, json, urllib.request
from pathlib import Path

RC = bytes.maketrans(b"ACGTN",b"TGCAN")
MAX_EDIT=175
FLANK=250

def capped_semiglobal(query:bytes, reference:bytes, max_edits=MAX_EDIT, free_prefix=FLANK):
    """Minimum edit distance aligning all query to substring of reference,
    capped at max_edits; initial start must lie within free_prefix bases.
    A result None means no alignment within max_edits in this window.
    """
    n,m=len(query),len(reference)
    inf=max_edits+1
    previous=[0 if j<=free_prefix else inf for j in range(m+1)]
    for i in range(1,n+1):
        current=[inf]*(m+1)
        j0=max(1,i-max_edits)
        j1=min(m,i+free_prefix+max_edits)
        if j0==1:current[0]=min(inf,i)
        qi=query[i-1]
        for j in range(j0,j1+1):
            sub=previous[j-1]+(qi!=reference[j-1])
            dele=previous[j]+1
            ins=current[j-1]+1
            v=min(sub,dele,ins)
            current[j]=v if v<=max_edits else inf
        previous=current
    best=min(previous)
    return None if best>max_edits else best

def fetch_interval(acc:str,start:int,end:int):
    if start<1 or end<=start:raise ValueError("bad coordinates")
    url=("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
         f"db=nuccore&id={acc}&seq_start={start}&seq_stop={end}&rettype=fasta&retmode=text")
    payload=urllib.request.urlopen(urllib.request.Request(url,headers={
        "User-Agent":"BIO-MIMIC-X/1.0 contact dr.starck66@gmail.com"}),timeout=30).read()
    lines=payload.splitlines()
    if not lines or not lines[0].startswith(b">"+acc.encode()+b":"):raise ValueError("NCBI accession mismatch")
    seq=b"".join(lines[1:]).upper()
    if len(seq)!=end-start+1 or any(c not in b"ACGTN" for c in seq):
        raise ValueError("NCBI sequence failed validation")
    return seq, {"accession":acc,"start_1based":start,"end_1based":end,
                 "sequence_sha256":hashlib.sha256(seq).hexdigest(),
                 "source":url}

def target_candidates(scan_direction:dict):
    groups=scan_direction["top_clusters"]
    return [g for g in groups if g["hit_observations"]>=1]

def evaluate(scan_path:Path,root:Path):
    scan=json.loads(scan_path.read_text())
    results={}
    for key,query_file in [("old_to_modern","old_HAND2.fa"),
                           ("modern_to_old","modern_HAND2.fa")]:
        s=scan[key]
        query=b"".join((root/query_file).read_bytes().splitlines()[1:]).upper()
        outcomes=[]
        for candidate in target_candidates(s):
            projected=candidate["approx_start_0based_min"]
            # start in target is projected start +/- indel shift. Supply 250nt padding
            # each side; semiglobal start within the first 250nt plus edit cap.
            start=max(1,projected-FLANK+1)
            end=projected+len(query)+FLANK
            target,rec=fetch_interval(candidate["target"],start,end)
            strand=candidate["strand"]
            oriented=query if strand=="+" else query.translate(RC)[::-1]
            distance=capped_semiglobal(oriented,target,MAX_EDIT,FLANK+MAX_EDIT)
            outcomes.append({"target":candidate["target"],"strand":strand,
                             "anchor_support":candidate["unique_anchor_offsets"],
                             "approx_start_0based_min":projected,
                             "max_edits_allowed":MAX_EDIT,
                             "bounded_edit_distance":distance,
                             "status":("ALIGNMENT_WITHIN_CUTOFF" if distance is not None
                                       else "NO_ALIGNMENT_WITHIN_CUTOFF_IN_THIS_WINDOW"),
                             "window_source":rec})
        results[key]=outcomes
    return {"schema":"BIO-MIMIC-X/FULL-ASSEMBLY-SEED-HITS-BOUNDED-ALIGNMENT/1",
            "screen_sha256":hashlib.sha256(scan_path.read_bytes()).hexdigest(),
            "status":"PARTIAL_ALL_OBSERVED_SEEDED_CANDIDATES_TESTED_WITHIN_175",
            "candidate_windows":results,
            "genome_wide_uniqueness":"UNVERIFIED",
            "limitations":["Capped semiglobal threshold on preselected seed-hit neighborhoods only.",
                           "Candidates without a sampled exact 31-mer or spanning FASTA wraps may be missed.",
                           "Results do not establish exhaustive best and second-best whole-genome alignment.",
                           "An empty candidate set is not a validated negative for unseeded homologs."]}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--scan",type=Path,required=True)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    x=evaluate(a.scan,a.root)
    a.output.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
    for key,rows in x["candidate_windows"].items():
        print(key,len(rows),"tested",[(r["target"],r["anchor_support"],
              r["bounded_edit_distance"]) for r in rows])
if __name__=="__main__":main()
