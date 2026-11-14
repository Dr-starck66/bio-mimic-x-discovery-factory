"""ASTRA OCTOPUS CONTROL Ω — explicitly non-physical decision proxy.

This deliberately simple model is NOT a soft-body simulation and does not
claim to reproduce the findings of DOI 10.1242/jeb.252825 quantitatively.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from itertools import product
import hashlib
import json

@dataclass(frozen=True)
class Scenario:
    aperture_cm: float
    resistance: float
    anchor_quality: float
    offset: int = 0

@dataclass(frozen=True)
class Outcome:
    success: bool
    steps: int
    time_units: float | None
    effort_units: float | None
    required_force: float
    available_force: float
    reason: str

MIN_ENVELOPE = 4.5
NOMINAL_ENVELOPE = 11.0
DRIVE = 8.0

def required_force(s: Scenario) -> float:
    """Dimensionless decision proxy: no physical calibration."""
    strain = max(0.0, (NOMINAL_ENVELOPE - s.aperture_cm) / (NOMINAL_ENVELOPE - MIN_ENVELOPE))
    return round(3.0 + 9.0 * strain * strain + 4.0 * s.resistance + 1.5 * s.offset, 6)

def decide(s: Scenario, mode: str) -> Outcome:
    if mode not in {"direct", "staged"}:
        raise ValueError("mode must be direct or staged")
    if not (0 <= s.resistance <= 1.5 and 0 <= s.anchor_quality <= 1.5
            and s.aperture_cm > 0 and s.offset in (0, 1)):
        raise ValueError("scenario outside predeclared parameter domain")
    narrow = s.aperture_cm < 8.0
    steps = 1 if mode == "direct" else (4 if narrow else 3)
    arms = 0 if mode == "direct" else (5 if narrow else 3)
    available = round(DRIVE + 1.8 * arms * s.anchor_quality, 6)
    required = required_force(s)
    if s.aperture_cm < MIN_ENVELOPE:
        return Outcome(False, steps, None, None, required, available, "geometric_exclusion")
    if available + 1e-10 < required:
        return Outcome(False, steps, None, None, required, available, "force_proxy_limit")
    time = round((1.0 if mode == "direct" else 2.3 + 0.4 * (steps - 3))
                 + required / available, 6)
    effort = round(required * time + (0 if mode == "direct" else 0.8 * arms), 6)
    return Outcome(True, steps, time, effort, required, available, "pass_proxy")

def scenarios():
    # Full deterministic grid (400 configurations), including no-grip and impossible openings.
    return [Scenario(*v) for v in product(
        (3.5, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0),
        (0.0, 0.5, 1.0, 1.5),
        (0.0, 0.25, 0.5, 1.0, 1.5),
        (0, 1)
    )]

def run():
    observations = []
    for s in scenarios():
        direct, staged = decide(s, "direct"), decide(s, "staged")
        observations.append({"scenario": asdict(s), "direct": asdict(direct), "staged": asdict(staged)})
    both = [r for r in observations if r["direct"]["success"] and r["staged"]["success"]]
    outcomes = {
        "design": "deterministic, uncalibrated force/traction decision proxy, NOT physics",
        "units": "abstract effort/time; input aperture centimeters are assumed examples",
        "scenario_count": len(observations),
        "direct_success": sum(r["direct"]["success"] for r in observations),
        "staged_success": sum(r["staged"]["success"] for r in observations),
        "staged_only_success": sum(r["staged"]["success"] and not r["direct"]["success"] for r in observations),
        "direct_only_success": sum(r["direct"]["success"] and not r["staged"]["success"] for r in observations),
        "both_fail": sum(not r["direct"]["success"] and not r["staged"]["success"] for r in observations),
        "both_success": len(both),
        "staged_faster_when_both_success": sum(r["staged"]["time_units"] < r["direct"]["time_units"] for r in both),
        "direct_faster_when_both_success": sum(r["direct"]["time_units"] < r["staged"]["time_units"] for r in both),
        "no_anchor_cases": sum(r["scenario"]["anchor_quality"] == 0 for r in observations),
        "geometry_block_cases": sum(r["scenario"]["aperture_cm"] < MIN_ENVELOPE for r in observations),
        "notes": [
            "Higher staged traction is a MODEL ASSUMPTION, not an observed robot benefit.",
            "All entries are synthetic; no FEM, ROS, sensors, pneumatic hardware or deployments.",
            "When anchor_quality=0, staged cannot improve success; extra stages have a time cost.",
            "No training/test split because this is a parameter grid, not machine learning.",
        ]
    }
    canonical = json.dumps(observations, sort_keys=True, separators=(",", ":")).encode()
    outcomes["sha256_observations"] = hashlib.sha256(canonical).hexdigest()
    return outcomes, observations

if __name__ == "__main__":
    summary, data = run()
    import pathlib
    base = pathlib.Path(__file__).parent
    (base / "observations.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    (base / "report.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
