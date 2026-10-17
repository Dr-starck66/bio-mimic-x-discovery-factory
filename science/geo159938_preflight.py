#!/usr/bin/env python3
"""Fail-closed metadata gate for GSE159938 before any biological analysis.

No statistical claims; no substitute for original preregistration or a wet-lab.
Uses only Python stdlib and verifies biological sample labels, not gene values.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ACCESSION = "GSE159938"
SOURCE = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE159nnn/GSE159938/soft/GSE159938_family.soft.gz"
SPECIES = {"Acomys cahirinus": "Acomys", "Mus musculus": "Mus"}
DAYS = (0, 7, 14)


def parse_soft(content: str) -> list[dict]:
    samples: list[dict] = []
    current: dict | None = None
    for line in content.splitlines():
        if line.startswith("^SAMPLE ="):
            if current is not None:
                samples.append(current)
            accession = line.split("=", 1)[1].strip()
            if not re.fullmatch(r"GSM\d+", accession):
                raise ValueError(f"Invalid sample accession: {accession!r}")
            current = {"gsm": accession, "attrs": {}}
        elif line.startswith("^"):
            if current is not None:
                samples.append(current)
                current = None
        elif current is not None and line.startswith("!Sample_") and " = " in line:
            key, value = line.split(" = ", 1)
            if key == "!Sample_organism_ch1":
                current["organism"] = value.strip()
            elif key == "!Sample_title":
                current["title"] = value.strip()
            elif key.startswith("!Sample_characteristics_ch1"):
                if ":" not in value:
                    raise ValueError(f"Unparseable sample characteristic: {current['gsm']}: {value!r}")
                name, val = value.split(":", 1)
                name = name.strip().lower()
                if name in current["attrs"] and current["attrs"][name] != val.strip():
                    raise ValueError(f"Conflicting {name} on {current['gsm']}")
                current["attrs"][name] = val.strip()
    if current is not None:
        samples.append(current)
    ids = [s["gsm"] for s in samples]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate GEO sample accession")
    return samples


def standardize(s: dict) -> dict:
    a = s["attrs"]
    organism = s.get("organism", "")
    if organism not in SPECIES:
        raise ValueError(f"Unknown organism for {s['gsm']}: {organism!r}")
    tissue = a.get("tissue", "").strip().lower()
    if tissue not in {"dorsal dermis", "dorsal epidermis"}:
        raise ValueError(f"Unknown tissue for {s['gsm']}: {tissue!r}")
    day_str = a.get("post-wound day (pwd)", "").strip()
    if not re.fullmatch(r"\d+", day_str):
        raise ValueError(f"Invalid/missing post-wound day for {s['gsm']}: {day_str!r}")
    genotype = a.get("genotype", "").strip().upper()
    if genotype not in {"WT", "KO"}:
        raise ValueError(f"Unknown genotype for {s['gsm']}: {genotype!r}")
    region = a.get("region", "").strip().lower()
    if not region:
        raise ValueError(f"Missing region for {s['gsm']}")
    return {"gsm": s["gsm"], "species": SPECIES[organism], "tissue": tissue,
            "day": int(day_str), "genotype": genotype, "region": region,
            "region_unspecified": region in {"n.a.", "na", "n/a", "unknown"}}


def audit(soft: bytes, *, expected_samples: int = 25) -> dict:
    sha = hashlib.sha256(soft).hexdigest()
    if soft.startswith(b"\x1f\x8b"):
        raw = gzip.decompress(soft)
    else:
        raw = soft
    items = [standardize(s) for s in parse_soft(raw.decode("utf-8"))]
    if len(items) != expected_samples:
        return {"accession": ACCESSION, "status": "UNVERIFIED_METADATA_INCOMPLETE",
                "sample_count": len(items), "expected_samples": expected_samples,
                "input_sha256": sha, "source": SOURCE,
                "reason": "Not all official GEO samples were present; no extrapolation permitted"}
    counts = Counter((s["species"], s["tissue"], s["day"], s["genotype"], s["region"]) for s in items)
    by_subgroup: dict[tuple, dict] = defaultdict(dict)
    for (species, tissue, day, genotype, region), n in counts.items():
        by_subgroup[(tissue, genotype, region)].setdefault(species, {})[day] = n
    # Matching tissue/genotype/region/day required for six cells.
    # Even >=3 GSM/cell does not demonstrate >=3 independent biological donors.
    candidates = []
    for (tissue, genotype, region), g in sorted(by_subgroup.items()):
        cells = {sp: {str(d): g.get(sp, {}).get(d, 0) for d in DAYS} for sp in ("Acomys", "Mus")}
        has_three_gsm = all(cells[sp][str(d)] >= 3 for sp in cells for d in DAYS)
        candidates.append({"tissue": tissue, "genotype": genotype, "region": region,
                           "accessions_per_cell_NOT_confirmed_biological_donors": cells,
                           "all_six_cells_at_least_three_GSM": has_three_gsm})
    eligible = [c for c in candidates if c["all_six_cells_at_least_three_GSM"]]
    status = "UNVERIFIED_DONOR_AND_ASSAY_QC" if eligible else "NOT_COMPARABLE_ORIGINAL_TIMEPOINTS_AND_STRATA"
    return {"accession": ACCESSION, "source": SOURCE, "input_sha256": sha,
            "sample_count": len(items), "status": status,
            "original_preregistered_days": list(DAYS),
            "total_accessions_by_species": dict(Counter(s["species"] for s in items)),
            "strata": candidates, "possible_eligible_strata": len(eligible),
            "sample_manifest": items,
            "interpretation": ("GSM identifiers are NOT automatically independent donors; no biological PASS or "
                               "original-hypothesis replication may be claimed from this metadata audit.")}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, help="Local GSE159938_family.soft[.gz] (offline/no download)")
    p.add_argument("--out", type=Path, help="Write JSON report")
    a = p.parse_args()
    try:
        if a.input:
            raw = a.input.read_bytes()
        else:
            req = urllib.request.Request(SOURCE, headers={"User-Agent": "BIO-MIMIC-X GEO metadata audit"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read(10_000_001)
            if len(raw) > 10_000_000:
                raise ValueError("GEO metadata exceeds safety size limit")
        report = audit(raw)
    except (OSError, ValueError, EOFError, UnicodeError) as e:
        report = {"accession": ACCESSION, "status": "UNVERIFIED_METADATA_UNAVAILABLE",
                  "error": f"{type(e).__name__}: {e}"}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] in {"NOT_COMPARABLE_ORIGINAL_TIMEPOINTS_AND_STRATA", "UNVERIFIED_DONOR_AND_ASSAY_QC"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
