#!/usr/bin/env python3
"""SciFact third-party prediction benchmark and ASTRA no-evidence negative control.

Evaluation only. This does NOT perform scientific evidence retrieval or validation.
SciFact is CC BY-NC 2.0: do not use dataset for commercial deployment absent permission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

LABELS = ("SUPPORT", "CONTRADICT", "NEI")
NEGATIVE_CONTROL = re.compile(r"\b(?:not|no|never|without|less|fewer|only|exclusively|solely|decrease|reduce|reduction|absent|lack|unable)\b", re.I)

def control_predict(claim: str) -> str:
    """Deliberately weak claim-only control, not a scientific verifier."""
    return "CONTRADICT" if NEGATIVE_CONTROL.search(claim) else "SUPPORT"

def evaluate(records: list[dict], pred_key: str) -> dict:
    matrix = {g: {p: 0 for p in LABELS} for g in LABELS}
    seen = set()
    for item in records:
        if set(["id", "claim", "ground_truth"]) - item.keys():
            raise ValueError("missing mandatory row data")
        if item["id"] in seen or not isinstance(item["id"], int) or not isinstance(item["claim"], str):
            raise ValueError("duplicate or invalid claim")
        seen.add(item["id"])
        g = item["ground_truth"]
        p = control_predict(item["claim"]) if pred_key == "ASTRA_NEGATIVE_CONTROL" else item.get(pred_key)
        if g not in LABELS or p not in LABELS:
            raise ValueError("invalid label")
        matrix[g][p] += 1
    tp = matrix["CONTRADICT"]["CONTRADICT"]
    fn = sum(matrix["CONTRADICT"].values()) - tp
    fp = sum(matrix[g]["CONTRADICT"] for g in LABELS if g != "CONTRADICT")
    tn = len(records) - tp - fn - fp
    return {"number_rows": len(records), "multiclass_confusion_gold_rows_prediction_cols": matrix,
            "contradiction_positive_binary": {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
                "precision": round(tp / (tp + fp), 8) if (tp + fp) else None,
                "recall": round(tp / (tp + fn), 8) if (tp + fn) else None,
                "specificity": round(tn / (tn + fp), 8) if (tn + fp) else None}}

def benchmark(raw: bytes, prediction_key: str = "RoBERTa (fine-tuned)") -> dict:
    records = json.loads(raw)
    if not isinstance(records, list) or not records:
        raise ValueError("nonempty list expected")
    return {"source_sha256": hashlib.sha256(raw).hexdigest(), "n": len(records),
            "gold_label_positive": "CONTRADICT", "external_model_name": prediction_key,
            "external_third_party_model": evaluate(records, prediction_key),
            "astra_claim_only_negative_control": evaluate(records, "ASTRA_NEGATIVE_CONTROL"),
            "scientific_evidence_verification": "UNVERIFIED",
            "clinical_validation": "UNVERIFIED",
            "metric_warning": "External model is not an ASTRA inference. Claim-only control never reads abstracts and cannot verify science. Counts are NOT clinical safety FP/FN.",
            "license": "SciFact CC BY-NC 2.0; research only; obtain permission for commercial use"}

def main() -> int:
    p = argparse.ArgumentParser(description="Strict independent benchmark confusion matrix")
    p.add_argument("input", type=Path, help="third party benchmark_results.json downloaded separately")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    report = benchmark(args.input.read_bytes())
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    for k in ("external_third_party_model", "astra_claim_only_negative_control"):
        print(k, report[k]["contradiction_positive_binary"])
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
