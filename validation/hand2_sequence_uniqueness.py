#!/usr/bin/env python3
"""Fail-closed sequence-only candidate screen; not exhaustive whole-genome alignment."""
import argparse, hashlib, json, re
from pathlib import Path

RC = str.maketrans("ACGTN", "TGCAN")
def reverse_complement(seq): return seq.translate(RC)[::-1]

def fasta(path):
    name, parts = None, []
    with open(path, encoding="ascii") as handle:
        for line in handle:
            line = line.strip()
            if line.startswith(">"):
                if name is not None: yield name, "".join(parts)
                name, parts = line[1:].split()[0], []
            elif line:
                if name is None or re.fullmatch("[ACGTNacgtn]+", line) is None:
                    raise ValueError("Invalid FASTA")
                parts.append(line.upper())
    if name is not None: yield name, "".join(parts)

def scan(query, assemblies, k=31, stride=97):
    if k < 15 or stride < 1 or len(query) < k or not re.fullmatch("[ACGTN]+", query):
        raise ValueError("Invalid query or parameters")
    strands = {"+": query, "-": reverse_complement(query)}
    seeds = {}
    for strand, oriented in strands.items():
        for offset in range(0, len(oriented)-k+1, stride):
            seed = oriented[offset:offset+k]
            if "N" not in seed: seeds.setdefault(seed, []).append((strand, offset))
    if not seeds: raise ValueError("No valid seeds")
    matcher = re.compile("(?=(" + "|".join(re.escape(s) for s in sorted(seeds)) + "))")
    hits, bases, contigs = [], 0, 0
    for assembly in assemblies:
        for chrom, seq in fasta(assembly):
            contigs += 1; bases += len(seq)
            candidates = set()
            for m in matcher.finditer(seq):
                for strand, offset in seeds[m.group(1)]:
                    start = m.start()-offset
                    if 0 <= start <= len(seq)-len(query):
                        candidates.add((strand, start))
            for strand, start in sorted(candidates):
                fragment = seq[start:start+len(query)]
                mismatches = sum(a != b for a,b in zip(strands[strand], fragment))
                if mismatches <= max(2, int(.05*len(query))):
                    hits.append({"assembly": str(assembly), "chromosome": chrom,
                                 "strand": strand, "start_1based": start+1,
                                 "end_1based": start+len(query), "substitutions": mismatches})
    return {"schema":"BIO-MIMIC-X/HAND2-SEED-SCREEN/2",
            "status":"PARTIAL_EXACT_SEED_SCREEN_NOT_WHOLE_GENOME_UNIQUENESS",
            "assembly_sha256":[{"path":str(p),"sha256":hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in assemblies],
            "query_sha256":hashlib.sha256(query.encode()).hexdigest(),
            "bases_scanned":bases,"contigs_scanned":contigs,"k":k,"stride":stride,
            "candidate_count":len(hits),"candidates":hits,
            "whole_genome_unique":"UNVERIFIED",
            "limitations":["Requires complete assemblies","Indels and seedless hits can be missed",
                           "One hit does not prove uniqueness","No official curator confirmation"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--query",type=Path,required=True)
    p.add_argument("--assembly",type=Path,nargs="+",required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--k",type=int,default=31)
    p.add_argument("--stride",type=int,default=97)
    a=p.parse_args()
    q=list(fasta(a.query))
    if len(q)!=1: raise ValueError("Exactly one query sequence required")
    result=scan(q[0][1],a.assembly,a.k,a.stride)
    result["query_name"]=q[0][0]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"],result["candidate_count"])
if __name__=="__main__": main()
