#!/usr/bin/env python3
"""Falsifiable GPL16570-to-Acomys probe identity audit; no biological claims.

This tool uses *provided* 25-mer sequences and a provided Acomys FASTA.
It calls Bowtie 1 for up to three ungapped substitutions, reports ties, and
never treats an unmapped probe as proof of species-specific divergence.
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict, Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

REQUIRED_COLUMNS = ("probe_id", "gene_id", "sequence")
BANDS = {0: "high_ge96", 1: "high_ge96", 2: "intermediate_eq92", 3: "low_lt92"}


def read_probes(path: Path) -> dict[str, dict]:
    result = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if not set(REQUIRED_COLUMNS).issubset(reader.fieldnames or []):
            raise ValueError("required_columns_missing: probe_id,gene_id,sequence")
        for row in reader:
            probe = row["probe_id"].strip()
            seq = row["sequence"].strip().upper()
            gene = row["gene_id"].strip()
            if not probe or not gene or len(seq) != 25 or set(seq) - set("ACGT"):
                raise ValueError(f"invalid_probe:{probe}")
            if probe in result:
                raise ValueError(f"duplicate_probe_id:{probe}")
            result[probe] = {"gene_id": gene, "sequence": seq}
    if not result:
        raise ValueError("empty_probe_input")
    return result


def sam_best_matches(sam_lines, probes: dict[str, dict]):
    """Read Bowtie best-stratum SAM; count distinct locations at best NM."""
    matches = defaultdict(set)
    min_nm = {}
    for raw in sam_lines:
        if raw.startswith("@") or not raw.strip():
            continue
        cols = raw.rstrip("\n").split("\t")
        if len(cols) < 11:
            raise ValueError("malformed_sam")
        qname, flag, ref, pos, *_ = cols
        if qname not in probes:
            raise ValueError(f"unknown_probe_in_sam:{qname}")
        if int(flag) & 4:
            continue
        tags = {x[:2]: x[5:] for x in cols[11:] if len(x) >= 6 and x[2:5] == ":i:"}
        if "NM" not in tags:
            raise ValueError(f"missing_NM_tag:{qname}")
        nm = int(tags["NM"])
        if nm < 0 or nm > 3:
            raise ValueError(f"NM_outside_bowtie_v3:{qname}:{nm}")
        locus = (ref, int(pos), "reverse" if int(flag) & 16 else "forward")
        if nm < min_nm.get(qname, 100):
            matches[qname] = {locus}
            min_nm[qname] = nm
        elif nm == min_nm[qname]:
            matches[qname].add(locus)
    output = []
    for probe_id, meta in probes.items():
        nm = min_nm.get(probe_id)
        n_loci = len(matches[probe_id])
        band = BANDS[nm] if nm is not None else "unresolved_no_hit_within_3_mismatches"
        output.append({"probe_id": probe_id, "gene_id": meta["gene_id"],
                       "best_mismatches": nm, "identity_pct": round(100 * (25-nm)/25, 2) if nm is not None else None,
                       "n_best_loci": n_loci, "unique_best_locus": n_loci == 1,
                       "identity_band": band,
                       "interpretable_probe": nm is not None and n_loci == 1})
    return output


def write_report(probes, rows, out: Path, reference: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    counts = Counter(row["identity_band"] for row in rows)
    summary = {"status": "COMPUTATIONAL_MAPPING_ONLY_NOT_REPLICATION",
               "probe_count":len(rows), "unique_mapped":sum(x["interpretable_probe"] for x in rows),
               "ambiguous_best_hits":sum(x["n_best_loci"] > 1 for x in rows),
               "bands_all_probes":dict(counts),
               "probe_source_sha256":sha256(Path(probes).read_bytes()).hexdigest(),
               "reference_sha256":sha256(Path(reference).read_bytes()).hexdigest(),
               "limitations":["Substitutions only, max 3 mismatches", "No-hit does NOT establish <92% identity",
                              "Acomys Trinity assembly incompleteness and paralog ambiguity possible",
                              "No cross-platform ECM/macrophage covariance evaluated", "No biological replication PASS"]}
    summary_path=out.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return summary


def run_alignment(probe_tsv: Path, reference_fasta: Path, out_csv: Path):
    if not all(shutil.which(x) for x in ("bowtie", "bowtie-build")):
        raise RuntimeError("UNVERIFIED: bowtie1 and bowtie-build absent; install free Bowtie 1")
    probes = read_probes(probe_tsv)
    if not reference_fasta.exists() or reference_fasta.stat().st_size == 0:
        raise ValueError("missing_reference_fasta")
    with tempfile.TemporaryDirectory(prefix="astra_probe_") as td:
        td=Path(td); fasta=td/"probes.fasta"; index=td/"acomys_index"
        fasta.write_text("".join(f">{id}\n{meta['sequence']}\n" for id,meta in probes.items()),encoding="ascii")
        with (td/"bowtie_build.log").open("w") as log:
            subprocess.run(["bowtie-build",str(reference_fasta),str(index)],check=True,stdout=log,stderr=subprocess.STDOUT)
        sam=td/"alignments.sam"
        with sam.open("w") as dst:
            subprocess.run(["bowtie","-f","-v","3","-a","--best","--strata","-S",str(index),str(fasta)],
                           check=True,stdout=dst,stderr=subprocess.DEVNULL)
        with sam.open() as src:
            rows=sam_best_matches(src,probes)
    return write_report(probe_tsv,rows,out_csv,reference_fasta)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probes",type=Path,required=True,help="GPL16570 platform/vendor probe TSV: probe_id,gene_id,sequence")
    p.add_argument("--acomys-fasta",type=Path,required=True,help="GSE113081_Trinity.fasta or an independently pinned reference")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(run_alignment(args.probes,args.acomys_fasta,args.out),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
