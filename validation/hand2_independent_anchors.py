#!/usr/bin/env python3
"""Independent GTF/GFF3 HAND2 neighborhood anchors; not genome-wide proof."""
import argparse,gzip,hashlib,json,re
from pathlib import Path
def genes(path,chrom,center,radius):
    out={}
    op=gzip.open if str(path).endswith(".gz") else open
    with op(path,"rt") as stream:
        for line in stream:
            if line.startswith("#"): continue
            x=line.rstrip().split("\t")
            if len(x)<9 or x[0]!=chrom or x[2].lower()!="gene": continue
            try: start,end=int(x[3]),int(x[4])
            except ValueError: continue
            if end<center-radius or start>center+radius: continue
            attrs=dict(re.findall(r'([\w.-]+)\\s+"([^"]+)"',x[8]))
            for item in x[8].split(";"):
                if "=" in item:
                    k,v=item.strip().split("=",1);attrs.setdefault(k,v)
            name=next((attrs[k] for k in ("gene_name","Name","gene","gene_symbol") if attrs.get(k)),None)
            if name:
                out.setdefault(name.upper(),[]).append({"start":start,"end":end,"strand":x[6],"gene_id":attrs.get("gene_id",attrs.get("ID",""))})
    return {k:v[0] for k,v in out.items() if len(v)==1}
def side(g,center):
    return "L" if g["end"]<center else "R" if g["start"]>center else "OVERLAP"
def evaluate(old,modern,old_center,modern_center):
    rows=[]
    for symbol in sorted(set(old)&set(modern)-{"HAND1","HAND2"}):
        a,b=old[symbol],modern[symbol];sa,sb=side(a,old_center),side(b,modern_center)
        rows.append({"symbol":symbol,"old":a,"modern":b,"old_side":sa,"modern_side":sb,"opposite_flanks":(sa,sb) in (("L","R"),("R","L")),"opposite_strands":a["strand"] in "+-" and b["strand"] in "+-" and a["strand"]!=b["strand"]})
    good=[r for r in rows if r["opposite_flanks"] and r["opposite_strands"]]
    bilateral=any(r["old_side"]=="L" for r in good) and any(r["old_side"]=="R" for r in good)
    return {"status":"PARTIAL_ANNOTATION_ANCHORS" if bilateral else "UNVERIFIED_INSUFFICIENT_BILATERAL_ANCHORS","matched_unique_symbols":len(rows),"consistent_anchors":len(good),"anchors":rows,"genome_wide_uniqueness":"UNVERIFIED","curator_confirmation":"UNVERIFIED","limitations":["Same symbol does not prove orthology","Gene annotation may be incomplete","Both flanks required; full-genome uniqueness untested"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--old-gtf",type=Path,required=True);p.add_argument("--modern-gtf",type=Path,required=True)
    p.add_argument("--old-chrom",default="CM010938.2");p.add_argument("--modern-chrom",default="NC_090937.1")
    p.add_argument("--old-center",type=int,default=884796896);p.add_argument("--modern-center",type=int,default=910030830)
    p.add_argument("--radius",type=int,default=2000000);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();old=genes(a.old_gtf,a.old_chrom,a.old_center,a.radius);modern=genes(a.modern_gtf,a.modern_chrom,a.modern_center,a.radius)
    result=evaluate(old,modern,a.old_center,a.modern_center)
    result["input_sha256"]={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (a.old_gtf,a.modern_gtf)}
    result["gene_counts"]={"old":len(old),"modern":len(modern)}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"],result["consistent_anchors"])
    return 0 if result["status"]=="PARTIAL_ANNOTATION_ANCHORS" else 2
if __name__=="__main__":raise SystemExit(main())
