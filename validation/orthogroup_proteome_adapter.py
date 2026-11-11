#!/usr/bin/env python3
"""Experimental whole-proteome protein-kmer reciprocal best hit baseline; NOT HAND2 orthology proof."""
import argparse,collections,hashlib,json,pathlib,time
def fasta(path):
 name=None;chunks=[]
 for line in pathlib.Path(path).read_text().splitlines():
  if line.startswith(">"):
   if name is not None:yield name,"".join(chunks)
   name=line[1:].split()[0];chunks=[]
  elif line.strip():
   if name is None:raise ValueError("FASTA header missing")
   chunks.append(line.strip().upper())
 if name is not None:yield name,"".join(chunks)
def kmers(seq,k):return set(seq[i:i+k] for i in range(len(seq)-k+1) if "X" not in seq[i:i+k])
def run(paths,k=4,min_similarity=.35):
 t=time.perf_counter();genes={};species={}
 for path in paths:
  sp=pathlib.Path(path).stem
  for name,seq in fasta(path):
   if not seq or any(c not in "ACDEFGHIKLMNPQRSTVWYBXZJUO*" for c in seq):raise ValueError("Invalid protein")
   key=f"{sp}|{name}"
   if key in genes:raise ValueError("Duplicate gene "+key)
   genes[key]=kmers(seq,k);species[key]=sp
 parent={x:x for x in genes}
 def root(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(a,b):
  a=root(a);b=root(b)
  if a!=b:parent[max(a,b)]=min(a,b)
 inverted=collections.defaultdict(set)
 for g,ks in genes.items():
  for s in ks:inverted[s].add(g)
 shared=collections.Counter()
 for members in inverted.values():
  members=sorted(members)
  for i,a in enumerate(members):
   for b in members[i+1:]:
    if species[a]!=species[b]:shared[(a,b)]+=1
 best={}
 for (a,b),intersection in shared.items():
  score=intersection/(len(genes[a])+len(genes[b])-intersection)
  if score<min_similarity:continue
  for x,y in ((a,b),(b,a)):
   key=(x,species[y]);cur=best.get(key)
   if cur is None or score>cur[0] or (score==cur[0] and y<cur[1]):best[key]=(score,y)
 edges=[]
 for (a,sp),(score,b) in sorted(best.items()):
  if a<b and best.get((b,species[a]),(None,None))[1]==a:
   union(a,b);edges.append((a,b,score))
 groups=collections.defaultdict(list)
 for g in genes:groups[root(g)].append(g)
 result=sorted((sorted(v) for v in groups.values()),key=lambda v:(-len(v),v))
 return result,{"n_genes":len(genes),"n_species":len(set(species.values())),"n_pairs_with_shared_kmers":len(shared),"n_reciprocal_edges":len(edges),"n_groups":len(result),"wall_seconds":round(time.perf_counter()-t,6),"method":"experimental protein kmer Jaccard reciprocal best hit; NOT validated orthology"}
def main():
 p=argparse.ArgumentParser();p.add_argument("fastas",nargs="+");p.add_argument("--out",required=True);p.add_argument("--receipt",required=True);p.add_argument("--k",type=int,default=4);p.add_argument("--threshold",type=float,default=.35);a=p.parse_args()
 if not 2<=a.k<=10 or not 0<a.threshold<=1:p.error("invalid parameters")
 groups,receipt=run(a.fastas,a.k,a.threshold)
 receipt["input_sha256"]={str(p):hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in a.fastas}
 pathlib.Path(a.out).write_text("".join(" ".join(g)+"\n" for g in groups))
 pathlib.Path(a.receipt).write_text(json.dumps(receipt,indent=2)+"\n");print(json.dumps(receipt))
if __name__=="__main__":main()
