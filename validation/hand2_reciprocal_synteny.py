#!/usr/bin/env python3
"""HAND2 old chr6q: source-locked synteny flank screen and reciprocal SHORTLIST alignment.
Not a whole-genome reciprocal best hit, curator identity or clinical result.
"""
from __future__ import annotations
import argparse,gzip,hashlib,io,json,re,time
from pathlib import Path
from validation.hand2_chr6q_preflight import _verified_source,fetch_pinned_gtf
from validation.axolotl_paralog_panel import parse_current_gene
from validation.hand2_assembly_sequence_probe import bounded_get,fasta_from_ncbi
from validation.hand1_hand2_global_alignment import align_window,SEQUENCES,check_input_bases

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/factory/HAND2-RECIPROCAL-SYNTENY-LATEST.json"
CHROM="chr6q"
OLD_ACC="CM010938.2"
MOD_ACC="NC_090937.1"
ASSEMBLY="GCF_040938575.1"
ANCHORS=("GALNT7","SAP30","SCRG1","FBXO8","HPGD","HMGB2")
NEGATIVE=("SAP30L","GALNT10")
NAME=re.compile(r'gene_name "([^"]+)"')
GENE=re.compile(r'gene_id "([^"]+)"')
TAGS=re.compile(r'([A-Za-z][A-Za-z0-9-]*)\s*\[(?:hs|nr)\]',re.I)
PLAIN_SYMBOL=re.compile(r"^[A-Za-z][A-Za-z0-9-]*$")
MAX_CANDIDATES=8

def parse_old_chr6q(raw:bytes,verify=True):
    if verify:_verified_source(raw)
    genes=[]
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
        for line in f:
            if line.startswith(b"#"):continue
            p=line.decode("utf8","replace").rstrip("\r\n").split("\t")
            if len(p)!=9 or p[0].lower()!=CHROM or p[2]!="gene":continue
            g=GENE.search(p[8]); n=NAME.search(p[8])
            if not g:continue
            label=n.group(1) if n else ""
            symbols=set(x.upper() for x in TAGS.findall(label))
            if not symbols and PLAIN_SYMBOL.fullmatch(label):
                symbols.add(label.upper())
            genes.append({"gene_id":g.group(1),"start":int(p[3]),"end":int(p[4]),
             "strand":p[6],"symbols":sorted(symbols),
             "legacy_name":label})
    return sorted(genes,key=lambda g:(g["start"],g["gene_id"]))

def verified_modern_anchors(fetcher=bounded_get):
    modern={};failures={};receipts={}
    for sym in ANCHORS+NEGATIVE:
        url=f"https://api.ncbi.nlm.nih.gov/datasets/v2/gene/symbol/{sym}/taxon/8296/dataset_report"
        try:
            payload,receipt=fetcher(url,400000)
            model=parse_current_gene(payload,sym)
            if model["accession"]!=MOD_ACC:
                raise ValueError("Modern gene not on exact chr6q accession")
            modern[sym]=model
            receipts[sym]=receipt
        except Exception as e:
            failures[sym]=type(e).__name__+": "+str(e)[:160]
        time.sleep(.35)
    return modern,receipts,failures

def find_flanking_candidates(genes:list[dict],modern:dict,limit=MAX_CANDIDATES):
    evidence={"status":"UNVERIFIED_NO_FLANKING_ANCHORS","anchors":[],
              "anchor_failures":{},"candidates":[],"total_eligible":0}
    t=sum((SEQUENCES["hand2"]["start"],SEQUENCES["hand2"]["end"]))/2
    anchors=[]
    for s in ANCHORS:
        matches=[g for g in genes if s in g["symbols"]]
        if len(matches)!=1:
            evidence["anchor_failures"][s]="LEGACY_ANCHOR_COUNT_"+str(len(matches));continue
        if s not in modern:
            evidence["anchor_failures"][s]="MODERN_REFSEQ_MISSING";continue
        if any(x in matches[0]["symbols"] for x in NEGATIVE) or sum(x in matches[0]["symbols"] for x in ANCHORS)>1:
            evidence["anchor_failures"][s]="AMBIGUOUS_OLD_PARALOG_TAG";continue
        anchors.append({"symbol":s,"old":matches[0],"modern":modern[s]})
    evidence["anchors"]=anchors
    left=sorted((x for x in anchors if x["modern"]["end"]<t),key=lambda x:t-x["modern"]["end"])
    right=sorted((x for x in anchors if x["modern"]["start"]>t),key=lambda x:x["modern"]["start"]-t)
    if not left or not right:return evidence
    a,b=left[0],right[0]
    olda=(a["old"]["start"]+a["old"]["end"])/2
    oldb=(b["old"]["start"]+b["old"]["end"])/2
    newa=(a["modern"]["start"]+a["modern"]["end"])/2
    newb=(b["modern"]["start"]+b["modern"]["end"])/2
    if olda==oldb or newa==newb:return evidence
    pred=olda+(t-newa)/(newb-newa)*(oldb-olda)
    lo,hi=sorted((olda,oldb))
    eligible=[g for g in genes if lo<(g["start"]+g["end"])/2<hi
         and 250<=g["end"]-g["start"]+1<=40000
         and g["gene_id"] not in (a["old"]["gene_id"],b["old"]["gene_id"])]
    eligible.sort(key=lambda g:(abs((g["start"]+g["end"])/2-pred),g["gene_id"]))
    evidence.update({"status":"PARTIAL_TWO_SYNTENIC_FLANKS","selected_flanks":[a["symbol"],b["symbol"]],
     "reversed_old_order":olda>oldb,"old_flank_interval":[int(lo),int(hi)],
     "interpolated_old_target":int(pred),"total_eligible":len(eligible),
     "candidates":eligible[:limit],"excluded_by_shortlist_limit":max(0,len(eligible)-limit)})
    return evidence

def compare_reciprocal(synteny,fetcher=fasta_from_ncbi,aligner=align_window):
    out={"status":"UNVERIFIED_NO_CANDIDATES","whole_genome_unique":"UNVERIFIED",
         "curator_mapping":"UNVERIFIED","records":[],"failed_sources":{}}
    if synteny["status"]!="PARTIAL_TWO_SYNTENIC_FLANKS" or not synteny["candidates"]:
        return out
    seqs={}
    for key in ("hand1","hand2"):
        x=SEQUENCES[key]
        try:
            seq,proof=fetcher(x["accession"],x["start"],x["end"])
            check_input_bases(key,seq)
            seqs[key]=seq
            out.setdefault("modern_fasta_provenance",{})[key]=proof
        except Exception as e:out["failed_sources"][key]=type(e).__name__+": "+str(e)[:160]
    if len(seqs)!=2:return out
    import edlib
    for g in synteny["candidates"]:
        try:
            dna,proof=fetcher(OLD_ACC,g["start"],g["end"])
            if not re.fullmatch("[ACGTN]+",dna) or len(dna)!=g["end"]-g["start"]+1:
                raise ValueError("Invalid historical FASTA length / DNA")
            scores={}
            for key in ("hand1","hand2"):
                forward=aligner(seqs[key],dna,edlib)["best"]
                backward=aligner(dna,seqs[key],edlib)["best"]
                scores[key]={"modern_to_old_edits_per_base":round(forward["edit_distance"]/len(seqs[key]),6),
                             "old_to_modern_edits_per_base":round(backward["edit_distance"]/len(dna),6),
                             "modern_to_old_strand":forward["strand"],"old_to_modern_strand":backward["strand"]}
            out["records"].append({"legacy_gene":g["gene_id"],"start":g["start"],"end":g["end"],
                "old_fasta_provenance":proof,"scores":scores})
        except Exception as e:out["failed_sources"][g["gene_id"]]=type(e).__name__+": "+str(e)[:160]
        time.sleep(.35)
    candidates=sorted(out["records"],key=lambda x:(x["scores"]["hand2"]["modern_to_old_edits_per_base"],x["legacy_gene"]))
    if candidates:
        first=candidates[0]; h2=first["scores"]["hand2"];h1=first["scores"]["hand1"]
        margin= (candidates[1]["scores"]["hand2"]["modern_to_old_edits_per_base"]-
                 h2["modern_to_old_edits_per_base"]) if len(candidates)>1 else None
        evidence=h2["modern_to_old_edits_per_base"]<=.10 and h2["old_to_modern_edits_per_base"]<=.10 and (
            h1["old_to_modern_edits_per_base"]-h2["old_to_modern_edits_per_base"]>=.20)
        out.update({"status":"PARTIAL_RECIPROCAL_SHORTLIST_SCREEN",
           "best_shortlist_candidate":first["legacy_gene"],
           "candidate_is_hand2_like":bool(evidence),
           "top_two_margin":margin,
           "unique_within_tested_shortlist":bool(evidence and margin is not None and margin>=.20 and not out["failed_sources"])})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,default=OUT)
    ap.add_argument("--gtf",type=Path,help="Previously verified GTF from same CI job")
    args=ap.parse_args()
    result={"schema":"BIO-MIMIC-X/HAND2-SYNTENY-RECIPROCAL/1",
            "historic_HAND2_gene_id":"UNVERIFIED","whole_genome_reciprocal":"UNVERIFIED",
            "independent_curator":"UNVERIFIED","status":"UNVERIFIED"}
    try:
        if args.gtf:
            raw=args.gtf.read_bytes()
            source={"url":"verified-ci-local-cache","sha256":_verified_source(raw)}
        else: raw,source=fetch_pinned_gtf()
        genes=parse_old_chr6q(raw)
        modern,receipt,failures=verified_modern_anchors()
        synteny=find_flanking_candidates(genes,modern)
        alignment=compare_reciprocal(synteny)
        result.update({"gtf_source":source,"total_old_chr6q_gene_features":len(genes),
            "modern_anchor_source_receipts":receipt,"modern_anchor_failures":failures,
            "synteny":synteny,"alignment":alignment,
            "status":alignment["status"] if alignment["status"].startswith("PARTIAL") else synteny["status"]})
    except Exception as e:result.update({"status":"UNVERIFIED_SOURCE_OR_COMPUTE_FAILURE",
                                         "error":type(e).__name__+": "+str(e)[:250]})
    result["receipt_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False,
                       separators=(",",":")).encode()).hexdigest()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("HAND2_SYNTENY_RECIPROCAL "+json.dumps({"status":result["status"],
             "old_chr6q_genes":result.get("total_old_chr6q_gene_features"),
             "shortlist_n":len(result.get("synteny",{}).get("candidates",[])),
             "aligned_n":len(result.get("alignment",{}).get("records",[]))}))
    return 0 if result["status"].startswith("PARTIAL") else 1
if __name__=="__main__":raise SystemExit(main())
