#!/usr/bin/env python3
"""Project every exact necessary seed hit onto its accession, including unplaced
scaffolds; prepare genome-coordinate windows for bounded or bitparallel checks.
Cannot itself claim uniqueness without evaluating every resulting window.
"""
from __future__ import annotations
import argparse,bisect,hashlib,json
from collections import defaultdict, Counter
from pathlib import Path

CHUNK=1048576
OVERLAP=31
MARGIN=350
def assembly_inventory(path:Path,is_refseq:bool):
 table={}
 for row in path.read_text().splitlines():
  if row.startswith("#") or not row.strip():continue
  p=row.split("\t")
  if len(p)<9:raise ValueError("bad assembly report")
  acc=p[6] if is_refseq and p[6]!="na" else p[4]
  if acc in table:raise ValueError("duplicated assembly accession")
  table[acc]={"length":int(p[8]),"role":p[1]}
 return table

def fasta_order(sparse:Path,inventory:dict):
 names=[]
 for row in sparse.read_text().splitlines():
  _,sep,seq=row.partition(":")
  if not sep:raise ValueError("invalid prior FASTA ripgrep output")
  if seq.startswith(">"):
   acc=seq[1:].split()[0]
   if acc not in inventory or acc in names:raise ValueError("unexpected reference header")
   names.append(acc)
 if set(names)!=set(inventory):
  raise ValueError("FASTA header list not complete")
 offsets=[];cum=0
 for name in names:
  offsets.append(cum)
  cum+=inventory[name]["length"]
 return names,offsets,cum

def mapped_hits(path:Path,manifest:dict,names:list,offsets:list,inv:dict):
 desc=defaultdict(list)
 for i in manifest["items"]:
  desc[i["seed"].upper()].append((i["strand"],i["offset"]))
 line_count=0;duplicates=0;cross=0;unknown=0
 mapped=set()
 by=defaultdict(list)
 total=offsets[-1]+inv[names[-1]]["length"]
 for row in path.open():
  line_count+=1
  pieces=row.strip().split(":",2)
  if len(pieces)!=3 or not pieces[0].isdigit() or not pieces[1].isdigit():
   raise ValueError("bad --only-matching ripgrep line")
  lineno,col,mer=int(pieces[0]),int(pieces[1]),pieces[2].upper()
  if mer not in desc:unknown+=1;continue
  globalpos=(lineno-1)*(CHUNK-OVERLAP)+(col-1)
  if globalpos<0 or globalpos+len(mer)>total:
   raise ValueError("seed coordinate outside validated genome inventory")
  unique=(globalpos,mer)
  if unique in mapped:duplicates+=1;continue
  mapped.add(unique)
  idx=bisect.bisect_right(offsets,globalpos)-1
  acc=names[idx];localpos=globalpos-offsets[idx]
  if localpos+len(mer)>inv[acc]["length"]:
   cross+=1;continue
  for strand,qoffset in desc[mer]:
   projected=localpos-qoffset
   by[acc,strand].append((projected,localpos))
 return by,{"match_lines":line_count,"unique_seed_locations":len(mapped),
            "duplicate_overlap_locations":duplicates,
            "cross_scaffold_junction_seeds_rejected":cross,
            "unrecognized_match_patterns":unknown,
            "loci_with_any_necessary_seed":len(by)}

def cluster(by,inv,offset_by_name,querylen,span=350):
 candidates=[];skipped=0
 for (acc,strand),vals in by.items():
  vals.sort()
  groups=[]
  for v in vals:
   if not groups or v[0]-groups[-1][0][0]>span:
    groups.append([v])
   else:groups[-1].append(v)
  for g in groups:
   left_proj=g[0][0];right_proj=g[-1][0]
   start=max(0,left_proj-MARGIN)
   end=min(inv[acc]["length"],right_proj+querylen+MARGIN)
   if end-start < querylen-175:
    # A reference contig shorter than querylen-max_edits cannot contain a
    # complete <=175-edit alignment, but a projected window clipped at
    # chromosome ends must be expanded rather than silently rejected.
    if inv[acc]["length"]>=querylen-175:
      start=max(0,min(start,inv[acc]["length"]-(querylen+MARGIN)))
      end=min(inv[acc]["length"],max(end,start+querylen+MARGIN))
    if end-start < querylen-175:
      skipped+=1;continue
   candidates.append({"reference":acc,"role":inv[acc]["role"],"strand":strand,
    "projection_min_0based":left_proj,"projection_max_0based":right_proj,
    "seed_hit_count":len(g),
    "reference_interval_0based":[start,end],
    "global_interval_0based":[offset_by_name[acc]+start,offset_by_name[acc]+end]})
 candidates.sort(key=lambda x:(x["global_interval_0based"][0],x["reference"],x["strand"]))
 for i,x in enumerate(candidates):x["candidate_id"]=i
 return candidates,skipped

def prepare(matches:Path,manifest_path:Path,sparse:Path,report:Path,is_refseq:bool,expected_acc:str,out:Path):
 manifest=json.loads(manifest_path.read_text())
 if manifest["max_edits"]!=175 or manifest["block_count_per_strand"]!=176:
  raise ValueError("no guarantee for expected 175 edit threshold")
 seed_path=Path(str(manifest_path).replace(".manifest.json",".seeds"))
 if not seed_path.exists() or hashlib.sha256(seed_path.read_bytes()).hexdigest()!=manifest["seed_file_sha256"]:
  raise ValueError("SEED_MANIFEST_SHA_MISMATCH")
 inv=assembly_inventory(report,is_refseq)
 names,offsets,total=fasta_order(sparse,inv)
 by,stats=mapped_hits(matches,manifest,names,offsets,inv)
 candidates,skipped=cluster(by,inv,dict(zip(names,offsets)),manifest["query_length"])
 result={"schema":"BIO-MIMIC-X/WHOLE-GENOME-NECESSARY-SEED-CANDIDATES/1",
  "complete_reference_inventory":len(names),"reference_bases":total,
  "unplaced_unlocalized_references":sum(
   v["role"] in ("unplaced-scaffold","unlocalized-scaffold") for v in inv.values()),
  "source_matches_sha256":hashlib.sha256(matches.read_bytes()).hexdigest(),
  "source_manifest_sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
  "source_sparse_header_list_sha256":hashlib.sha256(sparse.read_bytes()).hexdigest(),
  "query_length":manifest["query_length"],"max_edits":175,
  "expected_accession":expected_acc,
  "stats":stats,"short_reference_windows_rejected":skipped,
  "candidate_windows":len(candidates),
  "expected_candidate_windows":sum(x["reference"]==expected_acc for x in candidates),
  "candidates":candidates,
  "scope":"NECESSARY_SEEDS_ALL_FASTA_ENTRIES_NOT_YET_ALL_WINDOW_ALIGNMENTS"}
 out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
 print("STRICT_CANDIDATES",matches.name,"referenced",len(names),"bases",total,
       "observed_lines",stats["match_lines"],"candidate_windows",len(candidates),
       "expected",result["expected_candidate_windows"],"skipped_short",skipped)
 return result

if __name__=="__main__":
 p=argparse.ArgumentParser()
 for field in ["matches","manifest","sparse","report","output"]:
  p.add_argument("--"+field,type=Path,required=True)
 p.add_argument("--refseq",action="store_true")
 p.add_argument("--expected",required=True)
 a=p.parse_args()
 prepare(a.matches,a.manifest,a.sparse,a.report,a.refseq,a.expected,a.output)
