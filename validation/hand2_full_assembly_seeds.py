#!/usr/bin/env python3
"""Audit exhaustive *file traversal* of seed matches from both true assembly FASTA.
Not a sensitivity-guaranteed whole-genome alignment or a proof of unique orthology.
Input lines are: `ripgrep -ni --text -F -f seeds.txt` against decompressed FASTA.
Every FASTA header is included because seeds.txt contains literal '>'.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

RC = bytes.maketrans(b"ACGTN", b"TGCAN")
OLD, MODERN = ("CM010938.2", 884794725), ("NC_090937.1", 910028724)

def inventory(path: Path, use_refseq: bool) -> dict:
    table = {}
    for line in path.read_text().splitlines():
        if line.startswith("#") or not line.strip(): continue
        p = line.split("\t")
        if len(p) < 9: raise ValueError("malformed assembly report")
        acc = p[6] if use_refseq and p[6] != "na" else p[4]
        if acc in table: raise ValueError("duplicated accession in assembly report")
        if not acc or acc == "na": raise ValueError("missing accession")
        table[acc] = {"role":p[1], "length":int(p[8])}
    return table

def anchors(query: bytes, stride=97, k=31):
    if not query or k < 10: raise ValueError("invalid query")
    out = defaultdict(list)
    for strand, seq in (("+",query),("-",query.translate(RC)[::-1])):
        for i in range(0, len(seq)-k+1, stride):
            m = seq[i:i+k]
            if b"N" not in m: out[m].append((strand,i))
    if not out: raise ValueError("no usable seeds")
    return out

def parse_matches(lines, seed_map, target_table, line_width=80):
    """Offset is approximate: reference FASTA must be wrapped at line_width bases.
    Never present these approximate coordinates as independently verified breakpoints.
    """
    if line_width < 31: raise ValueError("line width must accommodate exact seed")
    headers, hits = set(), []
    current, firstline = None, None
    for row in lines:
        line_no, sep, text = row.rstrip("\r\n").partition(":")
        if not sep or not line_no.isdecimal(): raise ValueError("invalid ripgrep line")
        line_no = int(line_no)
        if text.startswith(">"):
            current = text[1:].split()[0]
            firstline = line_no
            if current in headers or current not in target_table:
                raise ValueError("duplicated or unexpected genome accession")
            headers.add(current)
            continue
        if current is None or line_no <= firstline:
            raise ValueError("seed hit without preceding FASTA header")
        upper = text.encode("ascii").upper()
        for mer, descriptors in seed_map.items():
            start = 0
            while (i := upper.find(mer,start)) != -1:
                base_pos = (line_no-firstline-1)*line_width+i
                for strand,qoffset in descriptors:
                    projected = base_pos-qoffset
                    hits.append({"target":current, "role":target_table[current]["role"],
                                 "strand":strand,"seed_offset":qoffset,
                                 "target_pos_0based":base_pos,
                                 "projected_query_start_0based":projected})
                start = i+1
    if headers != set(target_table):
        missing = sorted(set(target_table)-headers)
        raise ValueError("INCOMPLETE_ASSEMBLY_INVENTORY: %d missing, examples=%s" %
                         (len(missing),",".join(missing[:3])))
    return hits, {"headers_observed":len(headers),
                  "unplaced_and_unlocalized_observed":
                   sum(v["role"] in ("unplaced-scaffold","unlocalized-scaffold")
                       for v in target_table.values()),
                  "roles":dict(Counter(v["role"] for v in target_table.values()))}

def clusters(hits, window=320):
    by = defaultdict(list)
    for h in hits: by[h["target"],h["strand"]].append(h)
    out = []
    for (target,strand), rows in by.items():
        rows.sort(key=lambda h:h["projected_query_start_0based"])
        groups = []
        for h in rows:
            if not groups or h["projected_query_start_0based"]-groups[-1][-1]["projected_query_start_0based"] > window:
                groups.append([h])
            else: groups[-1].append(h)
        for g in groups:
            offsets = {x["seed_offset"] for x in g}
            vals = [x["projected_query_start_0based"] for x in g]
            out.append({"target":target,"role":g[0]["role"],"strand":strand,
                        "unique_anchor_offsets":len(offsets),"hit_observations":len(g),
                        "approx_start_0based_min":min(vals),
                        "approx_start_0based_max":max(vals)})
    return sorted(out,key=lambda c:(-c["unique_anchor_offsets"],
                c["target"],c["approx_start_0based_min"]))

def audit(matches_path, assembly_path, query_path, use_refseq, expected_acc, expected_start, stride=97, width=80):
    query = b"".join(query_path.read_bytes().splitlines()[1:]).upper()
    seed_map = anchors(query,stride=stride)
    reference = inventory(assembly_path,use_refseq)
    with matches_path.open(encoding="ascii") as f:
        hits, coverage = parse_matches(f,seed_map,reference,line_width=width)
    groups = clusters(hits)
    expected = [g for g in groups if g["target"]==expected_acc and
                g["strand"]=="-" and
                g["approx_start_0based_min"]-300 <= expected_start <=
                  g["approx_start_0based_max"]+300]
    strong_alternatives = [g for g in groups if g not in expected and
                           g["unique_anchor_offsets"]>=4]
    return {"schema":"BIO-MIMIC-X/REAL-FULL-ASSEMBLY-EXACT-SEED-SCREEN/1",
            "status":"PARTIAL_COMPLETE_FASTA_SEED_SCREEN_NOT_UNIQUE_ALIGNMENT",
            "archive_md5_validation":"RECORDED_SEPARATELY_NOT_RECOMPUTED_BY_THIS_SCRIPT",
            "source_inventory_sha256":hashlib.sha256(assembly_path.read_bytes()).hexdigest(),
            "source_matches_sha256":hashlib.sha256(matches_path.read_bytes()).hexdigest(),
            "query_sha256":hashlib.sha256(query).hexdigest(),
            "reference_inventory":coverage,
            "query_length":len(query),"seed_count":len(seed_map),"seed_stride":stride,
            "target_reference_line_width_assumed":width,
            "detected_anchor_hits":len(hits),"clusters":len(groups),
            "expected_candidate_support":expected[:5],
            "other_clusters_with_4_or_more_distinct_anchors":strong_alternatives[:100],
            "other_strong_cluster_count":len(strong_alternatives),
            "top_clusters":groups[:30],
            "genome_wide_uniqueness":"UNVERIFIED",
            "limitations":[
              "Only exact sampled 31-mers (both strands), NOT all possible alignments.",
              "FASTA line wraps split some exact seeds: false negatives possible.",
              "175 edit differences can destroy every selected stride-97 seed.",
              "Approximate positions assume 80-base FASTA line width; confirm by locus sequence.",
              "A single unique seeded cluster is NOT exhaustive uniqueness.",
              "No Liftoff/Minimap2 full-assembly alignment performed here."
            ]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--modern-matches",type=Path,required=True)
    p.add_argument("--old-matches",type=Path,required=True)
    p.add_argument("--modern-report",type=Path,required=True)
    p.add_argument("--old-report",type=Path,required=True)
    p.add_argument("--old-query",type=Path,required=True)
    p.add_argument("--modern-query",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report={"schema":"BIO-MIMIC-X/DOUBLE-ASSEMBLY-REAL-SCAN/1",
            "old_to_modern":audit(a.modern_matches,a.modern_report,a.old_query,True,*MODERN),
            "modern_to_old":audit(a.old_matches,a.old_report,a.modern_query,False,*OLD),
            "conclusion":"PARTIAL_ANCHOR_SCREEN_ONLY"}
    a.output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("PARTIAL_BOTH_FULL_FASTA_SEED_SCREENS",
          "old_to_modern",report["old_to_modern"]["reference_inventory"],
          "modern_to_old",report["modern_to_old"]["reference_inventory"])
    print("EXPECTEDS", len(report["old_to_modern"]["expected_candidate_support"]),
          len(report["modern_to_old"]["expected_candidate_support"]))
    print("ALTERNATIVES",
          report["old_to_modern"]["other_strong_cluster_count"],
          report["modern_to_old"]["other_strong_cluster_count"])
if __name__=="__main__": main()
