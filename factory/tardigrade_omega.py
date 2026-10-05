#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


class Mode(str, Enum):
    ACTIVE = "ACTIVE"
    SHIELDED = "SHIELDED"
    DORMANT = "DORMANT"
    RECOVERY = "RECOVERY"
    QUARANTINED = "QUARANTINED"


class GateStatus(str, Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class Thresholds:
    low_energy: float = 0.15
    resume_energy: float = 0.35
    max_recent_failures: int = 3
    max_integrity_errors: int = 0

    def validate(self) -> None:
        if not (0.0 <= self.low_energy < self.resume_energy <= 1.0):
            raise ValueError("energy thresholds must satisfy 0 <= low < resume <= 1")
        if self.max_recent_failures < 0:
            raise ValueError("max_recent_failures must be >= 0")
        if self.max_integrity_errors < 0:
            raise ValueError("max_integrity_errors must be >= 0")


@dataclass(frozen=True)
class Signals:
    energy_ratio: float
    dependencies_ok: bool
    integrity_errors: int = 0
    recent_failures: int = 0
    thermal_ok: bool = True
    network_required: bool = False
    network_ok: bool = True

    def validate(self) -> None:
        if not (0.0 <= self.energy_ratio <= 1.0):
            raise ValueError("energy_ratio must be between 0 and 1")
        if self.integrity_errors < 0 or self.recent_failures < 0:
            raise ValueError("error/failure counts must be >= 0")


@dataclass(frozen=True)
class Decision:
    mode: Mode
    status: GateStatus
    reasons: List[str]
    actions: List[str]
    can_execute_nonessential_work: bool

    def as_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        out["mode"] = self.mode.value
        out["status"] = self.status.value
        return out


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def make_checkpoint(payload: Mapping[str, Any], metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    body = {
        "schema": "ASTRA-TARDIGRADE-OMEGA/CHECKPOINT-1",
        "payload": dict(payload),
        "metadata": dict(metadata or {}),
    }
    return {
        **body,
        "sha256": sha256_json(body),
    }


def verify_checkpoint(checkpoint: Mapping[str, Any]) -> bool:
    required = {"schema", "payload", "metadata", "sha256"}
    if set(checkpoint.keys()) != required:
        return False
    if checkpoint.get("schema") != "ASTRA-TARDIGRADE-OMEGA/CHECKPOINT-1":
        return False
    expected = sha256_json({
        "schema": checkpoint["schema"],
        "payload": checkpoint["payload"],
        "metadata": checkpoint["metadata"],
    })
    return expected == checkpoint["sha256"]


def decide(signals: Signals, thresholds: Thresholds = Thresholds()) -> Decision:
    signals.validate()
    thresholds.validate()

    if signals.integrity_errors > thresholds.max_integrity_errors:
        return Decision(
            mode=Mode.QUARANTINED,
            status=GateStatus.FAIL,
            reasons=["integrity errors exceed allowed threshold"],
            actions=[
                "stop nonessential execution",
                "isolate mutable state",
                "verify last trusted checkpoint before any recovery",
            ],
            can_execute_nonessential_work=False,
        )

    if not signals.thermal_ok:
        return Decision(
            mode=Mode.DORMANT,
            status=GateStatus.PARTIAL,
            reasons=["thermal safety signal is not healthy"],
            actions=[
                "freeze nonessential workload",
                "persist integrity checkpoint",
                "resume only after thermal signal and checkpoint verification pass",
            ],
            can_execute_nonessential_work=False,
        )

    if signals.energy_ratio <= thresholds.low_energy:
        return Decision(
            mode=Mode.DORMANT,
            status=GateStatus.PARTIAL,
            reasons=["available energy is below dormancy threshold"],
            actions=[
                "persist integrity checkpoint",
                "suspend nonessential workload",
                "keep only watchdog and recovery probes alive",
            ],
            can_execute_nonessential_work=False,
        )

    if signals.network_required and not signals.network_ok:
        return Decision(
            mode=Mode.DORMANT,
            status=GateStatus.PARTIAL,
            reasons=["required network path is unavailable"],
            actions=[
                "checkpoint local state",
                "defer network-dependent actions",
                "retry with bounded backoff",
            ],
            can_execute_nonessential_work=False,
        )

    if not signals.dependencies_ok or signals.recent_failures > thresholds.max_recent_failures:
        return Decision(
            mode=Mode.SHIELDED,
            status=GateStatus.PARTIAL,
            reasons=["dependency health or recent failure budget is outside the normal envelope"],
            actions=[
                "route reads to last verified state where safe",
                "block destructive writes",
                "increase integrity verification frequency",
            ],
            can_execute_nonessential_work=False,
        )

    return Decision(
        mode=Mode.ACTIVE,
        status=GateStatus.PASS,
        reasons=["all configured resilience gates pass"],
        actions=["continue normal execution", "refresh checkpoint on normal cadence"],
        can_execute_nonessential_work=True,
    )


def recovery_gate(
    checkpoint: Mapping[str, Any],
    signals: Signals,
    thresholds: Thresholds = Thresholds(),
) -> Decision:
    signals.validate()
    thresholds.validate()

    if not verify_checkpoint(checkpoint):
        return Decision(
            mode=Mode.QUARANTINED,
            status=GateStatus.FAIL,
            reasons=["checkpoint integrity verification failed"],
            actions=["do not restore checkpoint", "retain forensic copy", "find earlier trusted checkpoint"],
            can_execute_nonessential_work=False,
        )

    if signals.integrity_errors > thresholds.max_integrity_errors:
        return Decision(
            mode=Mode.QUARANTINED,
            status=GateStatus.FAIL,
            reasons=["live integrity errors remain during recovery"],
            actions=["hold recovery", "repair or replace corrupted state"],
            can_execute_nonessential_work=False,
        )

    if signals.energy_ratio < thresholds.resume_energy:
        return Decision(
            mode=Mode.RECOVERY,
            status=GateStatus.PARTIAL,
            reasons=["checkpoint is valid but energy reserve is below resume threshold"],
            actions=["keep minimal watchdog active", "wait for resume energy gate"],
            can_execute_nonessential_work=False,
        )

    if not signals.thermal_ok:
        return Decision(
            mode=Mode.RECOVERY,
            status=GateStatus.PARTIAL,
            reasons=["checkpoint is valid but thermal gate is not healthy"],
            actions=["hold recovery until thermal gate passes"],
            can_execute_nonessential_work=False,
        )

    if signals.network_required and not signals.network_ok:
        return Decision(
            mode=Mode.RECOVERY,
            status=GateStatus.PARTIAL,
            reasons=["checkpoint is valid but required network path is unavailable"],
            actions=["restore local state only", "hold network-dependent execution"],
            can_execute_nonessential_work=False,
        )

    if not signals.dependencies_ok:
        return Decision(
            mode=Mode.RECOVERY,
            status=GateStatus.PARTIAL,
            reasons=["checkpoint is valid but required dependencies are not healthy"],
            actions=["hold writes", "probe dependencies", "re-run recovery gate"],
            can_execute_nonessential_work=False,
        )

    return Decision(
        mode=Mode.ACTIVE,
        status=GateStatus.PASS,
        reasons=["checkpoint, energy, integrity, thermal, network and dependencies all pass"],
        actions=["restore checkpoint", "run post-restore verification", "resume normal workload"],
        can_execute_nonessential_work=True,
    )


BIOLOGY_TO_ENGINEERING = {
    "Dsup": {
        "evidence_role": "radiation-associated DNA protection in biological systems",
        "engineering_analogy": "integrity shielding: hashes, immutable checkpoints, redundant validation",
        "claim_boundary": "analogy only; software behavior does not reproduce Dsup biochemistry",
    },
    "SAHS_CAHS": {
        "evidence_role": "desiccation-associated stabilization/preservation mechanisms",
        "engineering_analogy": "dormancy: freeze mutable state and reduce operation to a minimal survival set",
        "claim_boundary": "analogy only; resource dormancy is not biological anhydrobiosis",
    },
    "recovery": {
        "evidence_role": "return from extreme-stress survival states requires restored conditions",
        "engineering_analogy": "fail-closed recovery gates before resuming full execution",
        "claim_boundary": "engineering analogy/design principle, not a biological equivalence claim",
    },
}


def evidence_manifest() -> Dict[str, Any]:
    manifest = {
        "brick": "ASTRA TARDIGRADE Ω",
        "version": "1.0.0",
        "status": "SUPPORTED_ANALOGY",
        "sources": [
            {
                "id": "HASHIMOTO_2016_DSUP",
                "doi": "10.1038/ncomms12808",
                "role": "primary",
                "supports": ["Dsup radiation-associated DNA protection"],
            },
            {
                "id": "LIM_2024_SAHS",
                "doi": "10.1038/s42003-024-06336-w",
                "role": "primary",
                "supports": ["SAHS protection of biological structures during desiccation"],
            },
            {
                "id": "KIRTANE_2025_DSUP_MRNA",
                "doi": "10.1038/s41551-025-01360-5",
                "role": "primary",
                "supports": ["local transient Dsup expression reduced radiation damage in mouse tissues"],
            },
        ],
        "mapping": BIOLOGY_TO_ENGINEERING,
        "policy": {
            "no_biological_equivalence_claims": True,
            "fail_closed_recovery": True,
            "checkpoint_integrity_required": True,
            "pass_requires_all_configured_resume_gates": True,
        },
    }
    manifest["sha256"] = sha256_json(manifest)
    return manifest


def scenario_report(scenarios: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    rows = []
    for item in scenarios:
        sig = Signals(**item["signals"])
        decision = decide(sig)
        rows.append({
            "id": item["id"],
            "signals": asdict(sig),
            "decision": decision.as_dict(),
        })
    out = {
        "brick": "ASTRA TARDIGRADE Ω",
        "schema": "ASTRA-TARDIGRADE-OMEGA/REPORT-1",
        "scenarios": rows,
    }
    out["sha256"] = sha256_json(out)
    return out


def default_scenarios() -> List[Dict[str, Any]]:
    return [
        {"id": "healthy", "signals": {"energy_ratio": 0.90, "dependencies_ok": True}},
        {"id": "low-energy", "signals": {"energy_ratio": 0.10, "dependencies_ok": True}},
        {"id": "dependency-failure", "signals": {"energy_ratio": 0.90, "dependencies_ok": False}},
        {"id": "integrity-failure", "signals": {"energy_ratio": 0.90, "dependencies_ok": True, "integrity_errors": 1}},
    ]


def write_bundle(output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence = evidence_manifest()
    report = scenario_report(default_scenarios())
    evidence_path = output_dir / "evidence.json"
    report_path = output_dir / "scenario-report.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "evidence": str(evidence_path),
        "scenario_report": str(report_path),
        "evidence_sha256": evidence["sha256"],
        "scenario_sha256": report["sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ASTRA TARDIGRADE Ω resilience state machine")
    parser.add_argument("--scenario", choices=["healthy", "low-energy", "dependency-failure", "integrity-failure"], default="healthy")
    parser.add_argument("--evidence", action="store_true", help="print the biology-to-engineering evidence manifest")
    parser.add_argument("--emit", type=Path, help="write evidence.json and scenario-report.json to a directory")
    args = parser.parse_args()

    if args.emit:
        print(json.dumps(write_bundle(args.emit), ensure_ascii=False, sort_keys=True))
        return 0

    if args.evidence:
        print(json.dumps(evidence_manifest(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    scenarios = {
        "healthy": Signals(energy_ratio=0.90, dependencies_ok=True),
        "low-energy": Signals(energy_ratio=0.10, dependencies_ok=True),
        "dependency-failure": Signals(energy_ratio=0.90, dependencies_ok=False),
        "integrity-failure": Signals(energy_ratio=0.90, dependencies_ok=True, integrity_errors=1),
    }
    decision = decide(scenarios[args.scenario])
    print(json.dumps(decision.as_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if decision.status != GateStatus.FAIL else 2


if __name__ == "__main__":
    raise SystemExit(main())
