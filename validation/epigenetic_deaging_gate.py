#!/usr/bin/env python3
"""BIO-MIMIC X: fail-closed evidence gate for Berg et al. (2026).

Metadata and author-reported observations are NOT a reproduction. This module
never downloads human controlled-access data, triggers wet-lab work, or infers
human rejuvenation from DNA-methylation clocks.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

DOI = "10.1111/acel.70751"
PAPER = "https://pmc.ncbi.nlm.nih.gov/articles/PMC13634082/"
DATASETS = {
    "GSE295849": {
        "kind": "human DNA methylation", "registry": "GEO",
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE295849",
        "access": "PUBLIC_METADATA_RAW_UNVERIFIED",
    },
    "E-MTAB-5808": {
        "kind": "earlier published human DNA methylation", "registry": "BioStudies/ArrayExpress",
        "url": "https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-5808",
        "access": "PUBLIC_METADATA_RAW_UNVERIFIED",
    },
    "phs004047.v1.p1": {
        "kind": "human RNA sequencing", "registry": "dbGaP",
        "url": "https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs004047.v1.p1",
        "access": "AUTHORIZATION_REQUIRED",
    },
}


def check_local_gzip(path: str | Path, expected_sha256: str, min_compressed_bytes: int = 1024) -> dict:
    """Check entire local source; SHA alone does not prove scientific provenance.

    A known SHA-256 digest from a separately verified primary-source manifest is
    mandatory; this function cannot authenticate an arbitrary caller-supplied hash.
    """
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(
        c not in "0123456789abcdef" for c in expected_sha256.lower()
    ):
        raise ValueError("a pinned 64-digit SHA-256 digest is required")
    if min_compressed_bytes < 1:
        raise ValueError("minimum compressed size must be positive")
    raw = Path(path).read_bytes()
    if len(raw) < min_compressed_bytes:
        raise ValueError("compressed data below the independently expected size")
    if not raw.startswith(b"\x1f\x8b"):
        raise ValueError("gzip magic header missing")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256.lower():
        raise ValueError("source SHA-256 mismatch; truncated or revised bytes")
    try:
        # Consume ALL members, detect EOF/CRC errors, not just the gzip header.
        decoded = gzip.decompress(raw)
    except (EOFError, OSError, ValueError) as exc:
        raise ValueError("invalid or truncated gzip stream") from exc
    if not decoded:
        raise ValueError("empty decompressed source")
    return {
        "status": "PASS_INTEGRITY_ONLY",
        "bytes": len(raw), "uncompressed_bytes": len(decoded), "sha256": digest,
        "scientific_reproduction": "UNVERIFIED",
    }


def candidate_cross_species_gate(candidate: dict) -> dict:
    """Refuse gene symbol and sign-only cross-species 'confirmation'."""
    required = ("human_study", "axolotl_study", "orthology_evidence",
                "biological_replicates", "negative_controls")
    missing = [field for field in required if not candidate.get(field)]
    if missing:
        return {"status": "UNVERIFIED", "missing": missing,
                "claim": "no cross-species regeneration inference"}
    if candidate["orthology_evidence"] != "RECIPROCAL_SEQUENCE_VERIFIED":
        return {"status": "UNVERIFIED", "reason": "symbol/annotation is not orthology proof",
                "claim": "no cross-species regeneration inference"}
    # Even a verified one-to-one ortholog is insufficient: blood->iNSC and
    # blastema vs skin are nonmatched biological systems and contrasts.
    return {"status": "PARTIAL", "reason": "non-equivalent species, tissues and experiments",
            "claim": "exploratory hypothesis only; no rejuvenation or therapy validated"}


def build_report(local_gzip_audit: dict | None = None) -> dict:
    integrity = local_gzip_audit or {"status": "UNVERIFIED", "reason": "raw human datasets not independently validated"}
    return {
        "schema": "BIO-MIMIC-X/EPIGENETIC-DEAGING-EVIDENCE/1",
        "article": {"doi": DOI, "primary_source": PAPER,
                    "finding": "author-reported epigenetic de-aging during blood-to-iNSC conversion",
                    "published_result_not_replicated": True},
        "sources": DATASETS,
        "local_source_integrity": integrity,
        "independent_age_clock_reproduction": "UNVERIFIED",
        "axolotl_human_mechanism": "UNVERIFIED",
        "human_tissue_regeneration": "UNVERIFIED",
        "clinical_anti_aging_efficacy": "UNVERIFIED",
        "retained_negative_control": {"dataset": "GSE74387",
            "legacy_result": "FAIL", "not_overridden_by_this_report": True},
        "status": "PARTIAL",
        "next_required_evidence": (
            "verified public sample-level methylation matrix with provenance and donor/time metadata; "
            "recompute DNAm clocks with matched controls; compare only orthologs independently "
            "validated by reciprocal sequence mapping and biologically comparable experiments"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--local-gzip", type=Path, help="already-authorized local dataset")
    p.add_argument("--sha256", help="independently pinned digest for local dataset")
    p.add_argument("--min-bytes", type=int, default=1024)
    p.add_argument("--out", type=Path, help="optional JSON report path")
    args = p.parse_args(argv)
    verified = None
    if args.local_gzip or args.sha256:
        if not (args.local_gzip and args.sha256):
            p.error("both --local-gzip and --sha256 are required")
        try:
            verified = check_local_gzip(args.local_gzip, args.sha256, args.min_bytes)
        except (OSError, ValueError) as exc:
            verified = {"status": "FAIL", "reason": str(exc)}
    report = build_report(verified)
    body = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding="utf-8")
    print(body, end="")
    return 1 if verified and verified.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
