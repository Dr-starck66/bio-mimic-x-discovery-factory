#!/usr/bin/env python3
"""Generate a necessary exact-seed covering set for Levenshtein distance <= D.
Pigeonhole: D+1 pairwise-disjoint blocks; <=D edits cannot disrupt all blocks.
For arbitrary edits in full-query-to-substring semiglobal alignment, at least
one block appears unchanged in the reference, on its mapped orientation.
The genome scanner must search across all FASTA and artificial line breaks.
"""
from pathlib import Path
import argparse, hashlib, json
RC=bytes.maketrans(b"ACGTN",b"TGCAN")

def blocks(query:bytes,d:int):
    if d<0 or len(query)<(d+1)*10 or any(c not in b"ACGT" for c in query):
        raise ValueError("query must be ACGT with >=10 bases per disjoint block")
    k=len(query)//(d+1)
    out=[]
    for strand,seq in [("+",query),("-",query.translate(RC)[::-1])]:
        for i in range(d+1):
            seed=seq[i*k:(i+1)*k]
            assert len(seed)==k
            out.append({"seed":seed.decode("ascii"),"strand":strand,"offset":i*k})
    return out

def write(query_path:Path,d:int,out_path:Path,manifest_path:Path):
    dna=b"".join(query_path.read_bytes().splitlines()[1:]).upper()
    items=blocks(dna,d)
    seeds=sorted(set(v["seed"] for v in items))
    out_path.write_text("\n".join(seeds)+"\n")
    manifest={"schema":"BIO-MIMIC-X/LEVENSHTEIN-PIGEONHOLE-SEED-SET/1",
              "max_edits":d,"query_length":len(dna),"block_len":len(dna)//(d+1),
              "block_count_per_strand":d+1,
              "number_distinct_patterns":len(seeds),
              "query_sha256":hashlib.sha256(dna).hexdigest(),
              "seed_file_sha256":hashlib.sha256(out_path.read_bytes()).hexdigest(),
              "items":items,
              "guarantee":"Necessary anchor exists if some whole-query semiglobal DNA alignment has <=max_edits, PROVIDED every reference base and boundary is searched."}
    manifest_path.write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    return manifest

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--query",type=Path,required=True)
 p.add_argument("--max-edits",type=int,default=175)
 p.add_argument("--seeds",type=Path,required=True)
 p.add_argument("--manifest",type=Path,required=True)
 a=p.parse_args()
 result=write(a.query,a.max_edits,a.seeds,a.manifest)
 print("GUARANTEED_SEED_SET",result["query_length"],result["block_len"],result["block_count_per_strand"],result["number_distinct_patterns"])
