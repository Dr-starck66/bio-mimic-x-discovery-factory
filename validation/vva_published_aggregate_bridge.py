#!/usr/bin/env python3
"""Research-only published trial aggregate audit; deliberately NOT patient-level VVA gate.

Only descriptive arithmetic on author-reported group means. No inferred p-values,
uncertainty, causality, subject-level reconstruction, ECM/barrier claims or drug endorsement.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

SCHEMA = "ASTRA-BIOMIMICX/VVA-AGGREGATE-CHECK/1"

def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)

def check_study(study):
    if study.get("id") != "chen2018_erzhi":
        raise ValueError("longitudinal aggregate requires explicit pre/on/off study")
    if study.get("timepoints") != ["pre", "week12_on", "week16_off"]:
        raise ValueError("true off-intervention follow-up missing or wrongly labeled")
    if min(study["completer_n"].values()) < 1:
        raise ValueError("invalid biological sample size")
    for endpoint in study["endpoints"]:
        if endpoint["direction"] not in (1, -1):
            raise ValueError("endpoint direction must be registered")
        for arm in ("active", "vehicle"):
            for key in ("means", "sd"):
                arr = endpoint[key][arm]
                if len(arr) != 3 or not all(finite(x) for x in arr):
                    raise ValueError("requires 3 real finite group aggregates per arm")
            if any(x < 0 for x in endpoint["sd"][arm]):
                raise ValueError("negative SD")
    return True

def _round(v):
    return round(v, 6) if v is not None else None

def audit(doc):
    studies = doc.get("studies", [])
    if len(studies) != 2 or {s.get("id") for s in studies} != {
        "chen2018_erzhi", "mitchell2018_estradiol_moisturizer"
    }:
        raise ValueError("requires exactly the two independent, explicitly identified sources")
    chen = next(s for s in studies if s["id"] == "chen2018_erzhi")
    mit = next(s for s in studies if s["id"] == "mitchell2018_estradiol_moisturizer")
    check_study(chen)
    out = {
        "schema": SCHEMA,
        "status": "PARTIAL_REAL_PUBLISHED_AGGREGATES",
        "independent_studies": 2,
        "biological_repair_proven": False,
        "durable_ECM_regeneration_proven": False,
        "clinical_efficacy_reanalyzed": False,
        "raw_patient_data_reanalyzed": False,
        "study_results": {},
        "restrictions": [
            "Descriptive arithmetic of real published aggregate means, not a reproduction of original analysis",
            "No paired raw data or within-patient covariance; no reconstructed p values or confidence intervals",
            "Four weeks after withdrawal is not permanent and long-term persistence is unknown",
            "VMI is cytology, not tissue thickness; clinical elasticity is not ECM histology",
            "Different interventions and endpoints: the two studies MUST NOT be statistically pooled",
            "Independent two-reviewer transcription audit required before scientific publication",
        ],
    }
    chen_rows = {}
    for e in chen["endpoints"]:
        active = e["means"]["active"]
        control = e["means"]["vehicle"]
        direction = e["direction"]
        def did(i):
            return direction * ((active[i]-active[0]) - (control[i]-control[0]))
        on, off = did(1), did(2)
        retention = (off/on*100) if abs(on) > 1e-12 else None
        chen_rows[e["name"]] = {
            "domain": e["domain"],
            "unit": "percentage points" if e["name"].endswith("_pct") else "source score units",
            "source_table": e["source_table"],
            "control_adjusted_change_week12": _round(on),
            "control_adjusted_change_week16_off": _round(off),
            "adjusted_change_after_withdrawal": _round(off-on),
            "descriptive_retention_pct": _round(retention),
            "source_means": {"active": active, "vehicle": control},
            "inferential_p_value": None,
        }
    out["study_results"]["chen2018_erzhi"] = {
        "endpoints": chen_rows,
        "withdrawal_observed": True,
        "followup_duration_weeks": 4,
        "complete_core_3domain_gate_available": False,
        "missing": [
            "paired individual-level data", "histological epithelial thickness",
            "barrier TEER", "blinded ECM architecture", "longer-term withdrawal follow-up"
        ],
        "verdict": "PARTIAL_SHORT_TERM_EPITHELIAL_CYTOLOGY_SIGNAL; NOT FULL STRUCTURAL OR DURABLE REPAIR",
    }
    mi = {e["name"]: e["values"] for e in mit["endpoints"]}
    expected = {"estradiol", "moisturizer", "dual_placebo"}
    if not all(set(e) == expected and all(finite(v) for v in e.values()) for e in mi.values()):
        raise ValueError("missing comparator arms or non-finite summary")
    mbs = mi["MBS_mean_change_baseline_to_week12"]
    vmi = mi["crossed_5pct_superficial_VMI_at_week12_pct"]
    out["study_results"]["mitchell2018_estradiol_moisturizer"] = {
        "symptom_MBS_change_active_vs_placebo": _round(mbs["estradiol"]-mbs["dual_placebo"]),
        "symptom_MBS_change_moisturizer_vs_placebo": _round(mbs["moisturizer"]-mbs["dual_placebo"]),
        "VMI_responder_percentage_point_difference_estradiol_vs_placebo": _round(vmi["estradiol"]-vmi["dual_placebo"]),
        "VMI_responder_percentage_point_difference_moisturizer_vs_placebo": _round(vmi["moisturizer"]-vmi["dual_placebo"]),
        "withdrawal_observed": False,
        "complete_core_3domain_gate_available": False,
        "missing": ["histological epithelium", "barrier TEER", "ECM architecture", "off-treatment follow-up"],
        "verdict": "SYMPTOM_ENDPOINT_IS_NOT_SUBSTITUTE_FOR_EPITHELIAL_CYTOLOGY; NO ECM OR DURABILITY CONCLUSION",
    }
    return out

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("published_aggregates_json")
    p.add_argument("--output")
    args = p.parse_args()
    raw = Path(args.published_aggregates_json).read_bytes()
    result = audit(json.loads(raw))
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    msg = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(msg, encoding="utf-8")
    print(msg, end="")

if __name__ == "__main__":
    main()
