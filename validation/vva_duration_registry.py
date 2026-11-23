#!/usr/bin/env python3
"""ASTRA BIO-MIMIC X: conservative eligibility audit of published vaginal tissue cohorts.

This program reads curated literature metadata, NOT participant records. It prevents
false durable-repair conclusions by requiring paired quantitative histology in a
placebo/sham-controlled group with independently verified 3/6/12-month cessation
measurements, no re-treatment, and audited participant-level observations.
"""
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED = {3, 6, 12}
SCHEMA = "astra.biomicx.vva_duration_registry.v1"
FAMILY_FIELDS = (
    "id", "cohort_family", "name", "source_urls", "comparison", "sham_or_placebo",
    "histology_paired", "quantitative_epithelium", "quantitative_ecm",
    "observations_after_last_treatment_months", "time_reference",
    "post_treatment_biopsy_per_timepoint", "any_booster_before_followup",
    "participant_level_data_available_to_pipeline", "participant_level_pairing_verified",
    "limitations", "data_access"
)


def evaluate(study):
    missing = [x for x in FAMILY_FIELDS if x not in study]
    if missing:
        raise ValueError(f"missing required study fields: {missing}")
    times = study["observations_after_last_treatment_months"]
    if not isinstance(times, list) or any(type(x) not in (int, float) or x < 0 for x in times):
        raise ValueError("invalid cessation-relative timepoints")
    if len(times) != len(set(times)):
        raise ValueError("duplicate timepoints")
    if study["time_reference"] not in ("last_treatment", "first_treatment", "end_of_protocol_unspecified", "unknown"):
        raise ValueError("invalid time origin")
    if not isinstance(study["limitations"], list) or not study["source_urls"]:
        raise ValueError("source and limitations must be documented")
    reasons = []
    if study["comparison"] not in ("sham", "placebo") or not study["sham_or_placebo"]:
        reasons.append("SHAM_OR_PLACEBO_CONTROL_ABSENT")
    if not study["histology_paired"]:
        reasons.append("REPORTED_PAIRED_HISTOLOGY_ABSENT")
    if not study["participant_level_pairing_verified"]:
        reasons.append("INDIVIDUAL_PAIR_MAPPING_NOT_REANALYZABLE")
    if not study["quantitative_epithelium"]:
        reasons.append("QUANTITATIVE_EPITHELIAL_HISTOLOGY_MISSING")
    if not study["quantitative_ecm"]:
        reasons.append("QUANTITATIVE_COLLAGEN_ELASTIN_MISSING")
    if study["time_reference"] != "last_treatment":
        reasons.append("LAST_TREATMENT_TIME_ORIGIN_UNVERIFIED")
    if not REQUIRED.issubset(set(times)):
        reasons.append("MISSING_3_6_12_MONTH_HISTOLOGY_AFTER_CESSATION")
    if not study["post_treatment_biopsy_per_timepoint"]:
        reasons.append("HISTOLOGY_NOT_DOCUMENTED_AT_ALL_3_6_12_MONTH_POINTS")
    if study["any_booster_before_followup"] is not False:
        reasons.append("RE_TREATMENT_NOT_EXCLUDED")
    if not study["participant_level_data_available_to_pipeline"]:
        reasons.append("PARTICIPANT_LEVEL_DATA_NOT_AVAILABLE_FOR_REANALYSIS")
    return {
        "id": study["id"], "family": study["cohort_family"],
        "independent_durability_dataset_eligible": not reasons,
        "reasons": reasons, "observed_cessation_months": sorted(times),
        "raw_data_access": study["data_access"],
    }


def audit(dataset):
    if dataset.get("schema") != SCHEMA:
        raise ValueError("unknown registry schema")
    records = dataset.get("studies")
    if not isinstance(records, list) or not records:
        raise ValueError("nonempty study registry required")
    ids, families = set(), set()
    results = []
    for s in records:
        if s["id"] in ids:
            raise ValueError("duplicated study id")
        ids.add(s["id"])
        if s["cohort_family"] in families:
            raise ValueError("double-counting published follow-ups of the same cohort")
        families.add(s["cohort_family"])
        results.append(evaluate(s))
    count = sum(int(r["independent_durability_dataset_eligible"]) for r in results)
    return {
        "schema": "astra.biomicx.vva_duration_audit.v1",
        "literature_study_families": len(families),
        "strictly_eligible_dataset_count": count,
        "durable_structural_repair_proven": False,  # Eligibility alone does not prove efficacy.
        "claim": "UNVERIFIED: causal, durable structural regeneration of human vulvovaginal tissue",
        "status": "PARTIAL_LITERATURE_EVIDENCE" if count == 0 else "ELIGIBILITY_ONLY_REQUIRES_DATA_REANALYSIS",
        "studies": results,
        "caution": [
            "No literature abstract, group aggregate or illustrative image is patient-level paired biopsy data.",
            "Eligibility is not an efficacy result, even if all criteria pass.",
            "No JAMA 2023 and JAMA 2026 LIGHT double counting, or protocol and analysis as separate cohorts.",
            "No clinical laser efficacy recommendation or untreated control inference from nonrandomized studies.",
            "Source observations and digital histological slides must be separately verified before any structural claim."
        ]
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("registry_json")
    p.add_argument("--out")
    ns=p.parse_args()
    raw=Path(ns.registry_json).read_bytes()
    result=audit(json.loads(raw))
    result["registry_sha256"] = hashlib.sha256(raw).hexdigest()
    text=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if ns.out:Path(ns.out).write_text(text,encoding="utf8")
    print(text,end="")

if __name__=="__main__":main()
