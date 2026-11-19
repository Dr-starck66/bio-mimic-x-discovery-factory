#!/usr/bin/env python3
"""ASTRA MEDICAL sequential reasoning research harness, synthetic cases only.

Decision-theory reference implementation, not a patient-facing diagnostic system.
No generative model, real clinical inference, network access or treatment advice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

FORBIDDEN_FIELDS = {"patient", "patient_id", "first_name", "last_name", "name", "full_name", "address", "dob", "birth_date", "phone", "email", "ssn", "nhs_number"}


def _walk_no_personal_fields(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_FIELDS:
                raise ValueError("patient-identifying field prohibited, including synthetic")
            _walk_no_personal_fields(item)
    elif isinstance(value, list):
        for item in value:
            _walk_no_personal_fields(item)


def validate_case(case):
    if not isinstance(case, dict) or case.get("synthetic") is not True:
        raise ValueError("explicit synthetic=true required")
    _walk_no_personal_fields(case)
    if not isinstance(case.get("case_id"), str) or not case["case_id"].startswith("synthetic-"):
        raise ValueError("case_id must start synthetic-")
    hypotheses = case.get("hypotheses")
    if not isinstance(hypotheses, list) or not 2 <= len(hypotheses) <= 20:
        raise ValueError("2..20 hypotheses required")
    priors = {}
    for h in hypotheses:
        if not isinstance(h, dict) or not isinstance(h.get("id"), str) or not h["id"] or h["id"] in priors:
            raise ValueError("invalid or duplicate hypothesis")
        p = h.get("prior")
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or p <= 0 or p >= 1:
            raise ValueError("invalid prior")
        priors[h["id"]] = float(p)
    if abs(sum(priors.values()) - 1) > 1e-9:
        raise ValueError("priors must sum to 1")
    tests = case.get("tests")
    if not isinstance(tests, list) or len(tests) > 100:
        raise ValueError("tests must be a list with <=100 entries")
    seen = set()
    for t in tests:
        if not isinstance(t, dict) or not isinstance(t.get("id"), str) or not t["id"] or t["id"] in seen:
            raise ValueError("duplicate or invalid test id")
        seen.add(t["id"])
        cost = t.get("cost")
        if isinstance(cost, bool) or not isinstance(cost, (float, int)) or not math.isfinite(cost) or cost < 0:
            raise ValueError("invalid synthetic test cost")
        outcomes = t.get("outcomes")
        if not isinstance(outcomes, dict) or set(outcomes) != set(priors):
            raise ValueError("test requires likelihood distribution for every hypothesis")
        categories = None
        for h, distribution in outcomes.items():
            if not isinstance(distribution, dict) or len(distribution) < 2 or len(distribution) > 8:
                raise ValueError("test requires 2..8 possible outcomes")
            if not all(isinstance(k, str) and k for k in distribution):
                raise ValueError("outcome keys must be nonempty strings")
            if categories is None:
                categories = set(distribution)
            if set(distribution) != categories:
                raise ValueError("all hypotheses must share outcome categories")
            if any(isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or p < 0 or p > 1 for p in distribution.values()):
                raise ValueError("invalid conditional probability")
            if abs(sum(distribution.values()) - 1) > 1e-9:
                raise ValueError("outcome likelihoods must sum to 1")
    observations = case.get("observations")
    if not isinstance(observations, dict) or set(observations) != seen:
        raise ValueError("harness requires one synthetic observation per test")
    for t in tests:
        if observations[t["id"]] not in t["outcomes"][next(iter(priors))]:
            raise ValueError("observation not in test outcomes")
    truth = case.get("ground_truth")
    if truth not in priors:
        raise ValueError("synthetic ground truth must match one hypothesis")
    return priors


def entropy(dist):
    return -sum(p * math.log2(p) for p in dist.values() if p > 0)


def posterior(prior, test, outcome):
    weights = {h: prior[h] * float(test["outcomes"][h][outcome]) for h in prior}
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("impossible observation under all hypotheses")
    return {h: weights[h] / total for h in prior}


def information_gain(prior, test):
    first_h = next(iter(prior))
    expected_entropy = 0.0
    for outcome in test["outcomes"][first_h]:
        prob = sum(prior[h] * test["outcomes"][h][outcome] for h in prior)
        if prob > 0:
            expected_entropy += prob * entropy(posterior(prior, test, outcome))
    return max(0.0, entropy(prior) - expected_entropy)


def select_next(prior, available):
    """No harness answers/ground_truth accessible here: selection depends on priors and test distributions only."""
    candidates = []
    for t in available:
        gain = information_gain(prior, t)
        if gain > 1e-10:
            candidates.append((gain / (1.0 + float(t["cost"])), gain, t["id"], t))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (-x[0], -x[1], x[2]))
    utility, gain, _, test = candidates[0]
    return test, gain, utility


def run_case(case, *, threshold=0.85, max_steps=5):
    if not 0.5 < threshold <= 1 or not isinstance(max_steps, int) or not 1 <= max_steps <= 100:
        raise ValueError("invalid stop configuration")
    prior = validate_case(case)
    current = prior.copy()
    remaining = {t["id"]: t for t in case["tests"]}
    trace = []
    for _ in range(min(max_steps, len(remaining))):
        if max(current.values()) >= threshold:
            break
        next_choice = select_next(current, list(remaining.values()))
        if next_choice is None:
            break
        test, info_gain, utility = next_choice
        del remaining[test["id"]]
        observation = case["observations"][test["id"]]   # synthetic harness response after order only
        before = current.copy()
        try:
            current = posterior(current, test, observation)
        except ValueError:
            trace.append({"test_id": test["id"], "observed": observation, "status": "IMPOSSIBLE_OBSERVATION"})
            break
        trace.append({"test_id": test["id"], "observed": observation,
                      "expected_gain_bits": round(info_gain, 8), "utility": round(utility, 8),
                      "cost_synthetic_units": test["cost"], "posterior": {k: round(v, 8) for k, v in current.items()},
                      "entropy_before_bits": round(entropy(before), 8), "entropy_after_bits": round(entropy(current), 8),
                      "status": "SIMULATED_STEP"})
    best = sorted(current, key=lambda h: (-current[h], h))[0]
    decision = best if trace and current[best] >= threshold and all(x["status"] == "SIMULATED_STEP" for x in trace) else None
    return {"case_id": case["case_id"], "predicted_label": decision, "synthetic_ground_truth": case["ground_truth"],
            "correct_on_synthetic": (decision == case["ground_truth"]) if decision else None,
            "outcome": "SIMULATED_CLASSIFICATION" if decision else "ABSTAIN",
            "posterior": {k: round(v, 8) for k, v in current.items()}, "steps": trace,
            "tests_used": len(trace), "synthetic_cost_units": sum(x.get("cost_synthetic_units",0) for x in trace),
            "evidence_status": "PASS_SIMULATION_ONLY", "clinical_validity": "UNVERIFIED",
            "note": "No patients, no therapy advice. Synthetic likelihoods supplied by experiment designer, not clinically calibrated."}


def run_suite(cases, threshold=0.85, max_steps=5):
    if not isinstance(cases, list) or not cases:
        raise ValueError("nonempty cases array required")
    results = [run_case(case, threshold=threshold, max_steps=max_steps) for case in cases]
    decided = [r for r in results if r["predicted_label"] is not None]
    correct = sum(r["correct_on_synthetic"] is True for r in decided)
    serialized = json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {"benchmark": "ASTRA sequential synthetic only", "input_sha256": hashlib.sha256(serialized).hexdigest(),
            "number_cases": len(results), "decided": len(decided), "abstained": len(results)-len(decided),
            "correct_decisions": correct, "accuracy_among_decided": correct/len(decided) if decided else None,
            "coverage": len(decided)/len(results), "patient_data": "PROHIBITED", "clinical_validation": "UNVERIFIED", "cases": results}


def main():
    p = argparse.ArgumentParser(description="ASTRA sequential diagnostic hypothesis simulator (synthetic only)")
    p.add_argument("input", type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--threshold", type=float, default=0.85)
    p.add_argument("--max-steps", type=int, default=5)
    args = p.parse_args()
    report = run_suite(json.loads(args.input.read_text(encoding="utf-8")), threshold=args.threshold, max_steps=args.max_steps)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("Synthetic cases", report["number_cases"], "decided", report["decided"], "correct", report["correct_decisions"], "abstained", report["abstained"])


if __name__ == "__main__":
    main()