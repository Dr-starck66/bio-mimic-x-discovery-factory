#!/usr/bin/env python3
"""Auditable NCBI HAND2 local flanking synteny test; never assert genome-wide uniqueness.

Independent of NCBI gene-dataset report endpoints (HTTP 500 in prior CI run).
Reads only exact nucleotide accession ranges.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

K = 31
NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
WINDOWS = {
    "old_left": ("CM010938.2", 884789726, 884794725),
    "old_right": ("CM010938.2", 884799067, 884804066),
    "modern_left": ("NC_090937.1", 910023725, 910028724),
    "modern_right": ("NC_090937.1", 910032937, 910037936),
}
EXPECTED_SHARED_31MERS = {
    ("old_left", "modern_right", "reverse_complement"): 3888,
    ("old_right", "modern_left", "reverse_complement"): 4268,
    ("old_left", "modern_left", "reverse_complement"): 0,
    ("old_right", "modern_right", "reverse_complement"): 0,
    ("old_left", "modern_left", "forward"): 0,
    ("old_left", "modern_right", "forward"): 0,
    ("old_right", "modern_left", "forward"): 0,
    ("old_right", "modern_right", "forward"): 0,
}
OUT = Path(__file__).resolve().parents[1] / "reports/factory/HAND2-LOCAL-SYNTENY-LATEST.json"

def fasta_url(accession: str, start: int, end: int) -> str:
    return NCBI + "?" + urlencode({
        "db": "nuccore", "id": accession, "seq_start": start, "seq_stop": end,
        "rettype": "fasta", "retmode": "text",
    })

def parse_fasta(data: bytes, accession: str, start: int, end: int) -> str:
    if len(data) > 20000:
        raise ValueError("Unexpectedly large NCBI window")
    txt = data.decode("ascii", errors="strict")
    rows = txt.splitlines()
    if not rows or not rows[0].startswith(">" + accession + ":" + str(start) + "-" + str(end)):
        raise ValueError("Accession or genomic interval mismatch")
    seq = "".join(rows[1:]).upper()
    if len(seq) != end - start + 1 or not re.fullmatch("[ACGTN]+", seq):
        raise ValueError("FASTA bases/length invalid")
    return seq

def fetch_window(accession: str, start: int, end: int) -> tuple[str, dict]:
    url = fasta_url(accession, start, end)
    req = Request(url, headers={"User-Agent": "BIO-MIMIC-X-HAND2-local-synteny/1.0"})
    with urlopen(req, timeout=45) as response:
        raw = response.read(20001)
    seq = parse_fasta(raw, accession, start, end)
    return seq, {"url": url, "length": len(seq), "sha256": hashlib.sha256(seq.encode()).hexdigest()}

def reverse_complement(seq: str) -> str:
    return seq.translate(str.maketrans("ACGTN", "TGCAN"))[::-1]

def indexed_kmers(seq: str, k: int = K) -> dict[str, int]:
    if not 1 <= k <= len(seq):
        raise ValueError("invalid k")
    return {seq[i:i + k]: i for i in range(len(seq) - k + 1) if "N" not in seq[i:i + k]}

def compare_flanks(old: str, modern: str, k: int = K) -> dict:
    old_k = indexed_kmers(old, k)
    new_k = indexed_kmers(modern, k)
    shared = set(old_k) & set(new_k)
    offsets = Counter(new_k[frag] - old_k[frag] for frag in shared)
    return {
        "distinct_old_kmers": len(old_k),
        "distinct_modern_kmers": len(new_k),
        "shared_distinct_kmers": len(shared),
        "fraction_of_old_distinct_kmers": round(len(shared) / len(old_k), 6) if old_k else 0,
        "top_offsets": [{"offset_bp": shift, "shared_kmers": count}
                        for shift, count in sorted(offsets.items(), key=lambda x: (-x[1], x[0]))[:5]],
    }

def evaluate(sequences: dict[str, str]) -> dict:
    if set(sequences) != set(WINDOWS):
        raise ValueError("missing or unexpected source window")
    for key, seq in sequences.items():
        if len(seq) != 5000 or not re.fullmatch("[ACGTN]+", seq):
            raise ValueError("invalid 5000-bp window: " + key)
    comparisons = []
    for old in ("old_left", "old_right"):
        for new in ("modern_left", "modern_right"):
            for orientation, s in (("forward", sequences[new]),
                                   ("reverse_complement", reverse_complement(sequences[new]))):
                proof = compare_flanks(sequences[old], s)
                key = (old, new, orientation)
                proof.update({"old_window": old, "modern_window": new,
                              "orientation": orientation,
                              "observed_count_matches_2026_11_05":
                              proof["shared_distinct_kmers"] == EXPECTED_SHARED_31MERS[key]})
                comparisons.append(proof)
    good = all(r["observed_count_matches_2026_11_05"] for r in comparisons) and any(
        r["shared_distinct_kmers"] >= 3000 for r in comparisons)
    return {
        "schema": "BIO-MIMIC-X/HAND2-FLANK-LOCAL-SYNTENY/1",
        "status": "PARTIAL_LOCAL_FLANK_SYNTENY_CONFIRMED" if good else "PARTIAL_SYNTENY_DISCREPANCY",
        "kmer_size": K,
        "window_size_bp": 5000,
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "gene_association": "AMEX60DD045298 vs NCBI Gene 138516365",
        "genome_wide_reciprocal_uniqueness": "UNVERIFIED",
        "curator_confirmation": "UNVERIFIED",
        "therapeutic_efficacy": "UNVERIFIED",
        "clinical_or_commercial_validation": "UNVERIFIED",
        "limitations": [
            "Local 5kb flanks only, not unique hit across the entire axolotl genome.",
            "Nearby gene identity and order were not independently curated.",
            "Shared 31-mers are exact local matches, not percent sequence identity.",
            "Repeated motifs can inflate matching k-mers; positional shifts retained.",
        ],
    }

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    source_receipts = {}
    seqs = {}
    failures = {}
    for name, (accession, start, end) in WINDOWS.items():
        try:
            seq, receipt = fetch_window(accession, start, end)
            seqs[name] = seq
            source_receipts[name] = receipt
        except Exception as error:
            failures[name] = type(error).__name__ + ": " + str(error)[:240]
        time.sleep(.35)
    if failures:
        report = {"schema": "BIO-MIMIC-X/HAND2-FLANK-LOCAL-SYNTENY/1",
                  "status": "UNVERIFIED_SOURCE_FAILURE", "source_failures": failures,
                  "genome_wide_reciprocal_uniqueness": "UNVERIFIED"}
    else:
        report = evaluate(seqs)
    report["sources"] = source_receipts
    report["receipt_sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True,
                               ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
    print("HAND2_FLANK_SYNTENY", json.dumps({"status": report["status"],
              "n_sources": len(source_receipts), "result_file": str(args.out)}))
    return 0 if report["status"] == "PARTIAL_LOCAL_FLANK_SYNTENY_CONFIRMED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
