#!/usr/bin/env python3
"""BIO-MIMIC X: fail-closed audit of paired epithelial function experiments.

Expected JSON:
{"metadata": {"randomized": true, "blinded_readout": true,
              "protocol_locked": true, "flow_matched": true},
 "records": [{"donor_id":"D1", "arm":"static|feedback|predictive",
              "teer_ohm_cm2":400, "permeability_cm_s":0.000001,
              "viable_cell_count":100000, "confluence_pct":98}, ...]}

A statistical signal is never independent biological validation. No invented data.
"""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import median

ARMS = ("static", "feedback", "predictive")
MIN_INDEPENDENT_DONORS = 6
TEER_GAIN_FLOOR = 1.10
PERMEABILITY_RATIO_CEILING = 0.90
CELL_COUNT_RATIO_TOLERANCE = 0.10
MAX_CONFLUENCE_DIFFERENCE = 5.0


def exact_sign_p(positive, nonzero):
    """One-sided exact sign test, no independence claim about repeated wells."""
    return sum(math.comb(nonzero, k) for k in range(positive, nonzero + 1)) / (2 ** nonzero)


def analyze(document):
    records = document.get("records", [])
    if not records:
        return {"status": "UNVERIFIED", "reason": "NO_RAW_FUNCTIONAL_MEASUREMENTS"}
    meta = document.get("metadata", {})
    requirements = ("randomized", "blinded_readout", "protocol_locked", "flow_matched")
    missing = [name for name in requirements if meta.get(name) is not True]
    if missing:
        return {"status": "UNVERIFIED", "reason": "EXPERIMENTAL_DESIGN_NOT_VERIFIED",
                "missing_design_assertions": missing}
    samples = defaultdict(lambda: defaultdict(list))
    for item in records:
        donor, arm = str(item.get("donor_id", "")).strip(), item.get("arm")
        if not donor or arm not in ARMS:
            raise ValueError("Missing donor_id or unknown arm")
        values = {}
        for field in ("teer_ohm_cm2", "permeability_cm_s", "viable_cell_count", "confluence_pct"):
            try:
                value = float(item[field])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Missing or nonnumeric {field}") from exc
            if not math.isfinite(value) or (value <= 0 if field != "confluence_pct" else not 0 <= value <= 100):
                raise ValueError(f"Invalid {field}")
            values[field] = value
        samples[donor][arm].append(values)

    complete = {donor: arms for donor, arms in samples.items() if all(arms.get(a) for a in ARMS)}
    if len(complete) < MIN_INDEPENDENT_DONORS:
        return {"status": "UNVERIFIED", "reason": "INSUFFICIENT_INDEPENDENT_MATCHED_DONORS",
                "matched_donors": len(complete), "required": MIN_INDEPENDENT_DONORS}
    observations = []
    for donor, arms in sorted(complete.items()):
        agg = {arm: {field: median(x[field] for x in arms[arm])
                     for field in ("teer_ohm_cm2", "permeability_cm_s",
                                   "viable_cell_count", "confluence_pct")}
               for arm in ARMS}
        f, predictive = agg["feedback"], agg["predictive"]
        observations.append({
            "donor_id": donor,
            "teer_ratio_predictive_to_feedback": predictive["teer_ohm_cm2"] / f["teer_ohm_cm2"],
            "permeability_ratio_predictive_to_feedback":
                predictive["permeability_cm_s"] / f["permeability_cm_s"],
            "cell_count_ratio_predictive_to_feedback":
                predictive["viable_cell_count"] / f["viable_cell_count"],
            "confluence_delta_percentage_points":
                predictive["confluence_pct"] - f["confluence_pct"]
        })
    n = len(observations)
    positives_teer = sum(o["teer_ratio_predictive_to_feedback"] > 1 for o in observations)
    positives_perm = sum(o["permeability_ratio_predictive_to_feedback"] < 1 for o in observations)
    nonzero_teer = sum(o["teer_ratio_predictive_to_feedback"] != 1 for o in observations)
    nonzero_perm = sum(o["permeability_ratio_predictive_to_feedback"] != 1 for o in observations)
    teer_p = exact_sign_p(positives_teer, nonzero_teer) if nonzero_teer else 1.0
    perm_p = exact_sign_p(positives_perm, nonzero_perm) if nonzero_perm else 1.0
    teer_ratio = median(o["teer_ratio_predictive_to_feedback"] for o in observations)
    perm_ratio = median(o["permeability_ratio_predictive_to_feedback"] for o in observations)
    comparable = all(
        abs(o["cell_count_ratio_predictive_to_feedback"] - 1) <= CELL_COUNT_RATIO_TOLERANCE
        and abs(o["confluence_delta_percentage_points"]) <= MAX_CONFLUENCE_DIFFERENCE
        for o in observations
    )
    statistical_support = (
        teer_p <= .05 and perm_p <= .05 and
        teer_ratio >= TEER_GAIN_FLOOR and perm_ratio <= PERMEABILITY_RATIO_CEILING
        and comparable
    )
    return {
        "status": "PARTIAL" if statistical_support else "FAIL",
        "reason": ("FUNCTIONAL_SIGNAL_ONLY_REQUIRES_INDEPENDENT_REPLICATION"
                   if statistical_support else "FUNCTIONAL_SUPERIORITY_GATE_NOT_MET"),
        "comparison": "predictive vs feedback, paired by independent donor",
        "matched_donors": n,
        "technical_wells_collapsed_to_donor_medians": len(records) > n * 3,
        "teer_median_ratio": round(teer_ratio, 6),
        "permeability_median_ratio": round(perm_ratio, 6),
        "teer_one_sided_exact_sign_p": round(teer_p, 8),
        "permeability_one_sided_exact_sign_p": round(perm_p, 8),
        "cell_growth_and_confluence_comparable": comparable,
        "notes": [
            "Requires protocol-level proof of identical flow, sensors, seeding, randomization.",
            "Self-declared metadata is NOT independently validated.",
            "No clinical or in-vivo regeneration claim follows from this gate."
        ]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    result = analyze(json.loads(raw))
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    out = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(out, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
