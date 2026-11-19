#!/usr/bin/env python3
"""Checkpoint partial strict-candidate evaluation from a growing FASTA.
This audit is deliberately PARTIAL unless every manifest candidate appears.
"""
import argparse,hashlib,json
from pathlib import Path
from collections import Counter
from hand2_all_strict_windows import score_one,RC

def scan(filename:Path,manifest:Path,queryfile:Path):
    m=json.loads(manifest.read_text())
    query=b"".join(queryfile.read_bytes().splitlines()[1:]).upper()
    if len(query)!=m["query_length"]:raise ValueError("QUERY_LENGTH")
    rev=query.translate(RC)[::-1]
    counts=Counter();matches=[];seen=set();read=0;tested_bytes=0
    with filename.open("rb") as inp:
        while True:
            header=inp.readline()
            if not header:break
            if not header.endswith(b"\n"):break
            sequence=inp.readline()
            if not sequence.endswith(b"\n"):break
            if not header.startswith(b">cand_"):raise ValueError("FASTA_NAME")
            i=int(header.strip().split(b"_")[1])
            if i in seen or i>=len(m["candidates"]) or i<0:raise ValueError("DUPLICATE_OR_UNKNOWN_ID")
            seen.add(i)
            c=m["candidates"][i]
            seq=sequence.strip().upper()
            if len(seq)!=c["reference_interval_0based"][1]-c["reference_interval_0based"][0]:raise ValueError("WINDOW_LENGTH")
            if any(letter not in b"ACGTN" for letter in seq):raise ValueError("FASTA_DNA")
            q=query if c["strand"]=="+" else rev
            result=score_one(q,seq,175)
            counts[result["status"]]+=1
            read+=1;tested_bytes+=len(seq)
            if result["status"]=="MATCH_WITHIN_CUTOFF":
                matches.append({"candidate_id":i,"accession":c["reference"],"strand":c["strand"],"edit_distance":result["distance"],"role":c["role"],"interval_0based":c["reference_interval_0based"]})
            if read%1000==0:
                print("PROGRESS",filename.name,read,"of",len(m["candidates"]),"matches",len(matches),flush=True)
    if seen!=set(range(read)):raise ValueError("CANDIDATE_OUTPUT_NONPREFIX")
    return {"schema":"BIO-MIMIC-X/STRICT-SEED-PARTIAL-WINDOW-SCORE/1",
            "status":"PASS_ALL_CANDIDATES_EVALUATED" if read==len(m["candidates"]) else "PARTIAL_EVALUATED_PREFIX_ONLY",
            "tested_candidate_windows":read,
            "total_candidate_windows":len(m["candidates"]),
            "tested_window_bases":tested_bytes,
            "complete_count":read==len(m["candidates"]),
            "method_counts":dict(counts),"passing_windows":matches,
            "candidate_manifest_sha256":hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "query_sha256":hashlib.sha256(query).hexdigest(),
            "limits":"Cannot conclude all-genome uniqueness without evaluating all manifest windows. Only whole-query <=175 semiglobal edits."}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 for arg in ("windows","manifest","query","output"):p.add_argument("--"+arg,required=True,type=Path)
 a=p.parse_args()
 x=scan(a.windows,a.manifest,a.query)
 a.output.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
 print("FINAL",a.output.name,x["status"],"tested",x["tested_candidate_windows"],"matches",len(x["passing_windows"]))
