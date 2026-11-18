"""BIO-MIMIC X: non-clinical, sequence-free Adaptamer/ADAR control model.

No construct design, dosing guidance, or claims of biological validation.
The model is deliberately phenomenological; parameters are NOT calibrated.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path

SOURCE_DOI = "10.1016/j.molcel.2026.09.037"


@dataclass(frozen=True)
class Parameters:
    ec50_arbitrary: float = 1.0
    hill: float = 2.0
    basal_fraction: float = 0.03
    protein_half_life_h: float = 8.0
    drug_half_life_h: float = 2.0

    def __post_init__(self):
        if min(self.ec50_arbitrary, self.hill, self.protein_half_life_h, self.drug_half_life_h) <= 0:
            raise ValueError("positive kinetic parameters required")
        if not 0 <= self.basal_fraction < 1:
            raise ValueError("basal_fraction must be in [0,1)")


def switch_output(dose: float, p: Parameters = Parameters(), adar_fraction: float = 1.0) -> float:
    """Normalized steady-state expression, not a biological measurement."""
    if not math.isfinite(dose) or dose < 0 or not 0 <= adar_fraction <= 1:
        raise ValueError("dose must be nonnegative and finite; ADAR fraction in [0,1]")
    x = (dose / p.ec50_arbitrary) ** p.hill
    return p.basal_fraction + (1 - p.basal_fraction) * adar_fraction * (x / (1 + x))


def simulate(p: Parameters = Parameters(), *, exposure: float = 5.0,
             on_until_h: float = 24.0, horizon_h: float = 72.0,
             step_h: float = 0.25, adar_fraction: float = 1.0) -> list[dict]:
    """Illustrative ON then withdrawal: drug and protein decay with separate timescales."""
    if not all(math.isfinite(v) for v in (exposure, on_until_h, horizon_h, step_h)):
        raise ValueError("all numerical inputs must be finite")
    if min(on_until_h, step_h) <= 0 or horizon_h <= on_until_h or exposure < 0:
        raise ValueError("invalid schedule")
    steps = round(horizon_h / step_h)
    if steps > 1_000_000 or abs(steps * step_h - horizon_h) > 1e-9:
        raise ValueError("step must divide horizon and stay computationally bounded")
    protein = switch_output(0, p, adar_fraction)
    drug = exposure
    drug_rate = math.log(2) / p.drug_half_life_h
    protein_rate = math.log(2) / p.protein_half_life_h
    rows = []
    for i in range(steps + 1):
        t = i * step_h
        if t >= on_until_h:
            drug = exposure * math.exp(-drug_rate * (t - on_until_h))
        elif t > 0:
            drug = exposure
        expression = switch_output(drug, p, adar_fraction)
        rows.append({"time_h": round(t, 6), "drug_arbitrary": round(drug, 8),
                     "expression_normalized": round(expression, 8),
                     "protein_normalized": round(protein, 8)})
        if i < steps:
            decay = math.exp(-protein_rate * step_h)
            protein = protein * decay + expression * (1 - decay)
    return rows


REQUIRED = {"laboratory", "study_doi", "arm", "replicate", "protein", "viability_pct", "offtarget_fraction"}
ARMS = ("off", "on", "withdrawal", "switch_negative")


def evaluate_measurements(rows: list[dict]) -> dict:
    """Predeclared *illustrative* acceptance gate for independent datasets.

    Never certifies independence, clinical safety, or tissue regeneration.
    Accepts raw measurements only; abstains if required arms/replicates absent.
    """
    if not rows:
        return {"status": "UNVERIFIED", "reason": "NO_EXTERNAL_MEASUREMENTS"}
    if any(not REQUIRED.issubset(row) for row in rows):
        return {"status": "UNVERIFIED", "reason": "REQUIRED_COLUMNS_MISSING"}
    groups = {arm: [] for arm in ARMS}
    sources = set()
    labs = set()
    try:
        for row in rows:
            if row["arm"] not in groups or not row["laboratory"] or not row["study_doi"]:
                raise ValueError("invalid provenance or arm")
            values = [float(row[k]) for k in ("protein", "viability_pct", "offtarget_fraction")]
            if not all(math.isfinite(v) for v in values):
                raise ValueError("nonfinite measurement")
            protein, viability, off_target = values
            if protein < 0 or not 0 <= viability <= 100 or not 0 <= off_target <= 1:
                raise ValueError("measurement outside valid range")
            groups[row["arm"]].append((row["laboratory"], row["replicate"], protein, viability, off_target))
            labs.add(row["laboratory"])
            sources.add(row["study_doi"])
    except (TypeError, ValueError, KeyError) as exc:
        return {"status": "UNVERIFIED", "reason": "BAD_MEASUREMENTS", "detail": str(exc)}
    # No cross-laboratory pooling: every arm must have >=3 distinct replicates
    # in EACH laboratory. Reject missing arms to prevent batch confounding.
    coverage = {lab: {arm: len({r[1] for r in groups[arm] if r[0] == lab})
                      for arm in ARMS} for lab in sorted(labs)}
    if len(labs) < 2 or len(sources) < 2 or any(
        n < 3 for arms in coverage.values() for n in arms.values()
    ):
        return {"status": "UNVERIFIED", "reason": "INSUFFICIENT_INDEPENDENT_COVERAGE",
                "labs": len(labs), "studies": len(sources), "counts_by_lab": coverage}
    lab_results = {}
    for lab in sorted(labs):
        lab_data = {arm: [r for r in groups[arm] if r[0] == lab] for arm in ARMS}
        med = {arm: statistics.median(r[2] for r in lab_data[arm]) for arm in ARMS}
        baseline = med["off"]
        dynamic = med["on"] - baseline
        criteria = {
            "induction_2fold": baseline > 0 and med["on"] >= 2 * baseline,
            "withdrawal_80pct_reversal": dynamic > 0 and med["withdrawal"] <= baseline + 0.2 * dynamic,
            "negative_switch_near_baseline": med["switch_negative"] <= baseline * 1.25,
            "viability_at_least_90pct": min(r[3] for arm in ARMS for r in lab_data[arm]) >= 90,
            "offtarget_at_most_1pct": max(r[4] for arm in ARMS for r in lab_data[arm]) <= 0.01,
        }
        lab_results[lab] = {"criteria": criteria, "median_protein": med}
    all_criteria = {criterion: all(r["criteria"][criterion] for r in lab_results.values())
                    for criterion in next(iter(lab_results.values()))["criteria"]}
    return {"status": "PASS" if all(all_criteria.values()) else "FAIL",
            "status_scope": "ILLUSTRATIVE_NUMERIC_GATE_ONLY",
            "biological_validation": "UNVERIFIED", "external_provenance": "REVIEW_REQUIRED",
            "criteria": all_criteria, "by_lab": lab_results,
            "labs": len(labs), "studies": len(sources)}


def run_report(data_csv: str | None = None) -> dict:
    p = Parameters()
    traces = simulate(p)
    def at(t):
        return next(r for r in traces if r["time_h"] == t)
    evidence = {"source_doi": SOURCE_DOI, "source_kind": "peer_reviewed_mechanism",
                "not_regenerative_therapy_validation": True}
    if data_csv:
        with open(data_csv, newline="", encoding="utf-8") as f:
            validation = evaluate_measurements(list(csv.DictReader(f)))
    else:
        validation = evaluate_measurements([])
    return {"model_status": "SIMULATION_ONLY", "kinetics": "UNCALIBRATED_PLACEHOLDERS",
            "tissue": "NO_SPECIFIC_REGENERATIVE_TISSUE", "source": evidence,
            "observations": {"baseline": at(0), "end_of_exposure": at(24),
                             "end_of_simulation": at(72)},
            "external_validation": validation,
            "safety_note": "Simulated expression is not evidence of regeneration or absence of adverse effects."}


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--external-csv", default=None)
    cli.add_argument("--output", default=None)
    args = cli.parse_args()
    out = json.dumps(run_report(args.external_csv), indent=2, ensure_ascii=False, sort_keys=True)
    if args.output:
        Path(args.output).write_text(out + "\n", encoding="utf-8")
    else:
        print(out)