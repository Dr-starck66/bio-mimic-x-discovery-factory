#!/usr/bin/env python3
"""Fail-closed HAND1/HAND2 annotation preflight against pinned AmexT_v47 GTF.
Text-label scan only; never infer a historic HAND2 identity from a name.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import re
import urllib.request
from pathlib import Path

GTF_SHA256 = "cc0c3c4e39f3afedcbe2bc5aad1d63fc461714aeb75051f4d109390455874c5d"
ZENODO_MD5 = "62b2c2911a7c7b5dcb5d6bb7f9d09282"
SOURCES = (
    "https://www.axolotl-omics.org/dl/AmexT_v47-AmexG_v6.0-DD.gtf.gz",
    "https://zenodo.org/records/10728952/files/AmexT_v47-AmexG_v6.0-DD.gtf.gz?download=1",
)
MAX_BYTES = 60_000_000
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/factory/HAND2-CHR6Q-PREFLIGHT-LATEST.json"
GENE_ID = re.compile(r'\bgene_id "([^"]+)"')
GENE_NAME = re.compile(r'\bgene_name "([^"]+)"')
HAND = re.compile(r'(?<![A-Za-z0-9_-])HAND[12](?![A-Za-z0-9_-])', re.I)

def _verified_source(raw: bytes) -> str:
    if len(raw) > MAX_BYTES or not raw.startswith(b"\x1f\x8b"):
        raise ValueError("Not a bounded gzip GTF")
    sha = hashlib.sha256(raw).hexdigest()
    if sha != GTF_SHA256:
        raise ValueError("Historic GTF SHA256 mismatch")
    return sha

def fetch_pinned_gtf():
    """Original source first; immutable Zenodo mirror is a checksum-gated fallback."""
    failures = []
    for url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BIO-MIMIC-X/hand2-chr6q/1.0"})
            with urllib.request.urlopen(req, timeout=90) as response:
                raw = response.read(MAX_BYTES + 1)
            sha = _verified_source(raw)
            if "zenodo.org" in url and hashlib.md5(raw).hexdigest() != ZENODO_MD5:
                raise ValueError("Zenodo published MD5 checksum mismatch")
            return raw, {"url": url, "sha256": sha, "md5": hashlib.md5(raw).hexdigest(), "source_failures": failures}
        except Exception as exc:
            failures.append({"url": url, "error": type(exc).__name__, "message": str(exc)[:160]})
    raise RuntimeError("All pinned GTF sources unavailable or unverified: " + json.dumps(failures))

def scan_gene_features(raw: bytes, expected_sha: str | None = GTF_SHA256):
    if expected_sha is not None and hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("GTF SHA256 mismatch")
    if not raw.startswith(b"\x1f\x8b"):
        raise ValueError("Invalid GTF compression")
    total_genes = 0
    chr6q_genes = 0
    hand_rows = []
    seen = set()
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        for line in stream:
            if line.startswith(b"#"):
                continue
            cols = line.decode("utf-8", errors="replace").rstrip("\r\n").split("\t")
            if len(cols) != 9 or cols[2] != "gene":
                continue
            total_genes += 1
            if cols[0].casefold() == "chr6q":
                chr6q_genes += 1
            gid = GENE_ID.search(cols[8])
            name = GENE_NAME.search(cols[8])
            if not gid or not name:
                continue
            symbols = sorted(set(x.upper() for x in HAND.findall(name.group(1))))
            if not symbols:
                continue
            key = (gid.group(1), cols[0], int(cols[3]), int(cols[4]))
            if key in seen:
                continue
            seen.add(key)
            hand_rows.append({
                "gene_id": gid.group(1), "gene_name": name.group(1),
                "chromosome": cols[0], "start_1based": int(cols[3]),
                "end_1based": int(cols[4]), "strand": cols[6],
                "tagged_symbols": symbols,
            })
    hand_rows.sort(key=lambda x: (x["chromosome"], x["start_1based"], x["gene_id"]))
    chr6q_hand2 = [x for x in hand_rows if x["chromosome"].casefold() == "chr6q" and "HAND2" in x["tagged_symbols"]]
    disputed = [x for x in hand_rows if "HAND1" in x["tagged_symbols"] and "HAND2" in x["tagged_symbols"]]
    return {
        "gene_feature_count": total_genes,
        "chr6q_gene_feature_count": chr6q_genes,
        "historical_hand_labeled_gene_features": hand_rows,
        "chr6q_hand2_labeled_candidates": chr6q_hand2,
        "mixed_hand1_hand2_labeled_features": disputed,
        "historic_hand2_identity": "UNVERIFIED",
        "warning": "A missing chr6q HAND2 text label does NOT mean the biological HAND2 gene is absent. Reciprocal sequence and synteny mapping remain necessary.",
        "status": "PARTIAL_CHR6Q_LABEL_SCAN" if chr6q_hand2 else "PARTIAL_NO_CHR6Q_HAND2_LABEL",
    }

def build_receipt(raw: bytes, source: dict):
    _verified_source(raw)
    record = {
        "schema": "BIO-MIMIC-X/HAND2-CHR6Q-PREFLIGHT/1",
        "source": source,
        "legacy_assembly": "GCA_002915635.3",
        "modern_assembly": "GCF_040938575.1",
        "modern_hand1_ncbi_id": "138582569",
        "modern_hand2_ncbi_id": "138516365",
        "independent_curator_confirmation": "UNVERIFIED",
        "reciprocal_genomic_alignment": "UNVERIFIED",
        **scan_gene_features(raw),
    }
    canon = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    record["receipt_sha256"] = hashlib.sha256(canon.encode()).hexdigest()
    return record

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gtf", type=Path, help="Local exact pinned GTF; no network")
    ap.add_argument("--out", type=Path, default=OUTPUT)
    args = ap.parse_args(argv)
    try:
        if args.gtf:
            raw = args.gtf.read_bytes()
            source = {"url": str(args.gtf), "sha256": _verified_source(raw), "md5": hashlib.md5(raw).hexdigest(), "source_failures": []}
        else:
            raw, source = fetch_pinned_gtf()
        out = build_receipt(raw, source)
    except Exception as exc:
        out = {"schema": "BIO-MIMIC-X/HAND2-CHR6Q-PREFLIGHT/1", "status": "UNVERIFIED_SOURCE_FAILURE", "error": type(exc).__name__ + ": " + str(exc)[:1200], "historic_hand2_identity": "UNVERIFIED"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print("HAND2_CHR6Q_PREFLIGHT " + json.dumps({"status": out["status"], "historic_hand2_identity": out["historic_hand2_identity"], "out": str(args.out)}))
    return 0 if out["status"].startswith("PARTIAL_") else 1

if __name__ == "__main__":
    raise SystemExit(main())
