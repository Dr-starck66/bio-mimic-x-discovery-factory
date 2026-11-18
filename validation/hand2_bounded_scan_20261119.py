#!/usr/bin/env python3
"""Bounded-memory exact k-mer FASTA preflight; not a whole-genome alignment."""
import argparse, gzip, json
from collections import defaultdict
def rc(s):
    return s.translate(str.maketrans("ACGTN","TGCAN"))[::-1]
def kmers(s,k):
    return {s[i:i+k] for i in range(len(s)-k+1) if all(c in "ACGT" for c in s[i:i+k])}
def scan(path,query,k=31,cap=5):
    if k<1 or cap<0: raise ValueError("invalid k or cap")
    query=query.upper(); forward=kmers(query,k); reverse=kmers(rc(query),k)
    if not forward: raise ValueError("query has no valid k-mers")
    hits=defaultdict(lambda:{"forward_count":0,"reverse_count":0,"forward_positions":[],"reverse_positions":[]})
    opener=gzip.open if str(path).endswith(".gz") else open
    name=None; tail=""; offset=0; total=0
    with opener(path,"rt") as f:
        for line in f:
            if line.startswith(">"):
                name=line[1:].split()[0];tail="";offset=0;continue
            if name is None: raise ValueError("FASTA missing header")
            s=line.strip().upper(); chunk=tail+s; base=offset-len(tail)
            for i in range(max(0,len(chunk)-k+1)):
                word=chunk[i:i+k]; pos=base+i+1
                for strand,valid in (("forward",word in forward),("reverse",word in reverse)):
                    if valid:
                        h=hits[name];h[strand+"_count"]+=1
                        a=h[strand+"_positions"]
                        if len(a)<cap:a.append(pos)
            tail=chunk[-(k-1):] if k>1 else ""
            offset+=len(s);total+=len(s)
    return {"bases_scanned":total,"k":k,"query_kmers":len(forward),"contigs":dict(hits),
            "scope":"exact k-mer preflight only; no proof of genomic uniqueness or best hit"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("assembly_fasta");p.add_argument("query_fasta")
    p.add_argument("--k",type=int,default=31);p.add_argument("--output",default="hand2_kmer_scan.json")
    a=p.parse_args()
    with open(a.query_fasta) as f:q="".join(x.strip() for x in f if not x.startswith(">"))
    with open(a.output,"w") as f:json.dump(scan(a.assembly_fasta,q,a.k),f,indent=2)
