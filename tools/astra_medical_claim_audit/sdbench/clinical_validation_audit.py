#!/usr/bin/env python3
"""ASTRA MEDICAL: offline, aggregate-only paired audit of official SDBench MIMIC *test* results.

Not a clinical validator. Scores are SDBench judge decisions, NOT demonstrated
patient safety, diagnostic clinical validity, or prospectively measured outcomes.
No source case text or individual diagnosis is copied into the output.
Requires explicit provenance; surrogate judge/gatekeeper results are rejected.
Stdlib only. Run solely in a licensed, authorized local environment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib


class AuditError(ValueError):
    pass


def wilson95(successes: int, n: int) -> list[float]:
    if n <= 0:
        return [0.0, 1.0]
    z = 1.959963984540054
    p = successes / n
    d = 1 + z*z/n
    mid = (p+z*z/(2*n))/d
    rad = (z/d)*math.sqrt((p*(1-p)+z*z/(4*n))/n)
    return [round(max(0,mid-rad),6),round(min(1,mid+rad),6)]


def exact_mcnemar(baseline_only: int, astra_only: int) -> float:
    """Exact two-sided binomial McNemar p (paired, unadjusted, descriptive)."""
    n = baseline_only + astra_only
    if n == 0:
        return 1.0
    smaller = min(baseline_only, astra_only)
    return min(1.0, 2.0 * sum(math.comb(n,i) for i in range(smaller+1)) / (2**n))


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def validate_provenance(manifest: dict) -> None:
    # The researcher must provide auditable provenance, not a claim of certification.
    required = {
        "dataset_id": "mimic-iv-ext-sdbench/1.0.0",
        "case_set": "test",
        "gatekeeper_mode": "original_model",
        "judge_mode": "original_model",
        "data_use_authorized": True,
        "reference_labels_sealed_before_run": True,
        "patient_level_leakage_screened": True,
    }
    for field, expected in required.items():
        if manifest.get(field) != expected:
            raise AuditError(f"Provenance not established: {field} must be {expected!r}")
    for field in ("model_identifier", "model_sha256", "sdbench_commit", "evaluation_date", "evaluator_record"):
        if not isinstance(manifest.get(field),str) or not manifest[field].strip():
            raise AuditError(f"Missing provenance field {field}")
    if manifest.get("surrogate_roles_used") is not False:
        raise AuditError("Surrogate gatekeeper/judge results cannot qualify")
    # Self-declaration is not independent verification, even if all checks pass.


def load_run(directory: pathlib.Path, expected: int) -> tuple[dict[str,bool],dict]:
    json_dir = directory / "json"
    if not json_dir.is_dir():
        raise AuditError(f"Missing official SDBench results folder: {json_dir}")
    files = sorted(json_dir.glob("case_*.json"))
    if len(files) != expected:
        raise AuditError(f"Incomplete/non-single run in {directory}: {len(files)} files, expected {expected}")
    cases: dict[str,bool] = {}
    digests: dict[str,str] = {}
    abstentions = 0
    rounds = []
    for file in files:
        try:
            row = json.loads(file.read_text(encoding="utf-8"))
        except (ValueError,UnicodeError) as exc:
            raise AuditError(f"Invalid JSON in {file.name}") from exc
        if row.get("dataset") != "mimic" or row.get("case_set") != "test":
            raise AuditError("Wrong dataset or split; STOP (no train/synthetic leakage)")
        if row.get("k") not in (0,None):
            raise AuditError("Use a single repetition k=0 only")
        key = str(row.get("case_id",""))
        if not key or key in cases:
            raise AuditError("Missing or duplicate case ID")
        correct = row.get("correct")
        score = row.get("diagnosis_score")
        if type(correct) is not bool or type(score) is not int or not (1 <= score <= 5):
            raise AuditError("Missing/invalid judgement or errored case: do not silently exclude")
        if correct != (score >= 4):
            raise AuditError("Judge score and correctness disagree")
        diagnosis = row.get("model_diagnosis","")
        if not isinstance(diagnosis,str):
            raise AuditError("Invalid prediction")
        if diagnosis == "Unable to provide diagnosis":
            abstentions += 1
        turns = row.get("num_test_rounds",0)
        if type(turns) is not int or turns < 0:
            raise AuditError("Invalid test rounds")
        cases[key] = correct
        digests[file.name] = sha256_file(file)
        rounds.append(turns)
    return cases, {"abstentions":abstentions,"total_test_rounds":sum(rounds),"file_sha256":digests}


def audit(baseline: pathlib.Path, astra: pathlib.Path, manifest_path: pathlib.Path, expected: int=71) -> dict:
    if expected < 2 or expected > 100000:
        raise AuditError("Invalid expected sample size")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_provenance(manifest)
    a, ma = load_run(astra, expected)
    b, mb = load_run(baseline, expected)
    if set(a) != set(b):
        raise AuditError("Non-paired cases! Must compare identical patient-level test set")
    n = len(a)
    a_s = sum(a.values())
    b_s = sum(b.values())
    a_only = sum(a[i] and not b[i] for i in a)
    b_only = sum(b[i] and not a[i] for i in a)
    both_wrong = sum(not a[i] and not b[i] for i in a)
    both_right = n-a_only-b_only-both_wrong
    return {
        "status":"AUDITED_BENCHMARK_RESULTS_NOT_CLINICAL_VALIDATION",
        "dataset":"MIMIC-IV-Ext-SDBench v1.0.0",
        "split":"held-out clinician-reviewed test",
        "n":n,"provenance_manifest_sha256":sha256_file(manifest_path),
        "metadata_declarations_not_independently_verified": True,
        "metric":"Official SDBench model-judge score >=4/5, not a clinician-independent assessment",
        "astra":{"judge_correct":a_s,"judge_incorrect":n-a_s,"score_fraction":round(a_s/n,6),
                 "wilson95":wilson95(a_s,n),"abstentions":ma["abstentions"],
                 "mean_test_rounds":round(ma["total_test_rounds"]/n,3)},
        "baseline":{"judge_correct":b_s,"judge_incorrect":n-b_s,"score_fraction":round(b_s/n,6),
                    "wilson95":wilson95(b_s,n),"abstentions":mb["abstentions"],
                    "mean_test_rounds":round(mb["total_test_rounds"]/n,3)},
        "paired":{"both_correct":both_right,"both_wrong":both_wrong,
                  "astra_only_correct":a_only,"baseline_only_correct":b_only,
                  "difference_percentage_points":round(100*(a_s-b_s)/n,3),
                  "mcnemar_exact_p":round(exact_mcnemar(b_only,a_only),8)},
        "clinical_validity":"NOT ESTABLISHED: independent physician adjudication and external prospective evidence required",
        "export_policy":"Aggregate counts only; source records and per-case predictions remain inside authorized environment",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",type=pathlib.Path,required=True)
    p.add_argument("--astra",type=pathlib.Path,required=True)
    p.add_argument("--provenance",type=pathlib.Path,required=True)
    p.add_argument("--expected-cases",type=int,default=71)
    p.add_argument("--out",type=pathlib.Path,required=True)
    args=p.parse_args()
    report=audit(args.baseline,args.astra,args.provenance,args.expected_cases)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"n":report["n"],
                      "astra_correct":report["astra"]["judge_correct"],
                      "baseline_correct":report["baseline"]["judge_correct"],
                      "clinical_validity":report["clinical_validity"]},ensure_ascii=False))

if __name__ == "__main__":
    main()