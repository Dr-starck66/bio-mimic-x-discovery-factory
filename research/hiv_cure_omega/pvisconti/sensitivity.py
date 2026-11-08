#!/usr/bin/env python3
"""Post-hoc Holm sensitivity on PUBLISHED p-values only (no raw xlsx observations)."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def holm_adjust(pvalues: list[float]) -> list[float]:
    if not pvalues or any(not 0 <= x <= 1 for x in pvalues):
        raise ValueError("Invalid p-values")
    ordered = sorted(enumerate(pvalues), key=lambda item: item[1])
    adjusted = [0.0] * len(pvalues)
    previous = 0.0
    for rank, (original_index, p_value) in enumerate(ordered):
        previous = max(previous, min(1.0, p_value * (len(pvalues) - rank)))
        adjusted[original_index] = round(previous, 6)
    return adjusted


def analyse(path: Path | None = None) -> dict:
    path = path or HERE / "published_aggregates.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 16:
        raise ValueError("Unexpected published endpoints; must review source mapping")
    if len({(r["study"], r["endpoint"]) for r in rows}) != len(rows):
        raise ValueError("Duplicate endpoints")
    if {r["cohort_id"] for r in rows} != {"pVISCONTI_SIV_MACAQUES"}:
        raise ValueError("Related papers must not be counted as independent cohorts")
    if any(r["raw_xlsx_verified"].lower() != "false" for r in rows):
        raise ValueError("Raw data verification must be established in a separate audit")
    if not any("negative_control" in r["endpoint"] and float(r["p_published"]) == 0.9 for r in rows):
        raise ValueError("Missing prespecified negative contrast in published summary")
    groups = defaultdict(list)
    for row in rows:
        groups[row["family"]].append(row)
    results = []
    for family, subset in groups.items():
        adjusted = holm_adjust([float(r["p_published"]) for r in subset])
        for row, p_adj in zip(subset, adjusted):
            results.append({
                "family": family,
                "study": row["study"],
                "cohort_id": row["cohort_id"],
                "endpoint": row["endpoint"],
                "rho_published": float(row["rho_published"]) if row["rho_published"] else None,
                "p_published": float(row["p_published"]),
                "p_holm_posthoc": p_adj,
                "source_url": row["source_url"],
                "raw_individual_data_reanalysed": False,
            })
    charre = [r for r in rows if r["study"] == "Charre_2026"]
    charre_adjusted = holm_adjust([float(r["p_published"]) for r in charre])
    return {
        "schema": "astra-pvisconti-posthoc-summary-audit/1",
        "status": "PUBLISHED_SUMMARY_RECALCULATION_ONLY",
        "papers": 3,
        "underlying_siv_cohorts": 1,
        "published_endpoints_checked": len(rows),
        "raw_xlsx_retrieved": False,
        "raw_statistical_reanalysis_completed": False,
        "clinical_eradication_demonstrated": False,
        "holm_warning": "Sensitivity analysis with post-hoc endpoint families, not author-confirmed prespecified correction",
        "results": results,
        "charre_6_endpoint_sensitivity": [
            {"endpoint": row["endpoint"], "p_published": float(row["p_published"]), "p_holm_posthoc": adjusted}
            for row, adjusted in zip(charre, charre_adjusted)
        ],
    }


if __name__ == "__main__":
    output = analyse()
    out = HERE / "published_sensitivity.json"
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": output["status"],
        "endpoints": output["published_endpoints_checked"],
        "independent_cohorts": output["underlying_siv_cohorts"],
        "result_file": str(out),
    }, ensure_ascii=False))
