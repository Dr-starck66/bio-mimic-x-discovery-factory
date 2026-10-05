import copy
import json
import tempfile
import unittest
from pathlib import Path

from factory.tardigrade_omega import (
    GateStatus,
    Mode,
    Signals,
    Thresholds,
    decide,
    evidence_manifest,
    make_checkpoint,
    recovery_gate,
    scenario_report,
    verify_checkpoint,
    write_bundle,
)


class TardigradeOmegaTests(unittest.TestCase):
    def test_healthy_system_is_active(self):
        d = decide(Signals(energy_ratio=0.9, dependencies_ok=True))
        self.assertEqual(d.mode, Mode.ACTIVE)
        self.assertEqual(d.status, GateStatus.PASS)
        self.assertTrue(d.can_execute_nonessential_work)

    def test_low_energy_enters_dormancy(self):
        d = decide(Signals(energy_ratio=0.15, dependencies_ok=True))
        self.assertEqual(d.mode, Mode.DORMANT)
        self.assertEqual(d.status, GateStatus.PARTIAL)
        self.assertFalse(d.can_execute_nonessential_work)

    def test_dependency_failure_enters_shielded_mode(self):
        d = decide(Signals(energy_ratio=0.9, dependencies_ok=False))
        self.assertEqual(d.mode, Mode.SHIELDED)
        self.assertEqual(d.status, GateStatus.PARTIAL)
        self.assertFalse(d.can_execute_nonessential_work)

    def test_integrity_error_fails_closed(self):
        d = decide(Signals(energy_ratio=0.9, dependencies_ok=True, integrity_errors=1))
        self.assertEqual(d.mode, Mode.QUARANTINED)
        self.assertEqual(d.status, GateStatus.FAIL)
        self.assertFalse(d.can_execute_nonessential_work)

    def test_checkpoint_tampering_is_detected(self):
        cp = make_checkpoint({"ledger": [1, 2, 3]}, {"source": "unit-test"})
        self.assertTrue(verify_checkpoint(cp))
        tampered = copy.deepcopy(cp)
        tampered["payload"]["ledger"].append(4)
        self.assertFalse(verify_checkpoint(tampered))

    def test_recovery_requires_resume_energy(self):
        cp = make_checkpoint({"state": "safe"})
        d = recovery_gate(cp, Signals(energy_ratio=0.2, dependencies_ok=True))
        self.assertEqual(d.mode, Mode.RECOVERY)
        self.assertEqual(d.status, GateStatus.PARTIAL)

    def test_recovery_with_valid_checkpoint_and_all_gates_passes(self):
        cp = make_checkpoint({"state": "safe"})
        d = recovery_gate(cp, Signals(energy_ratio=0.8, dependencies_ok=True))
        self.assertEqual(d.mode, Mode.ACTIVE)
        self.assertEqual(d.status, GateStatus.PASS)

    def test_recovery_rejects_corrupt_checkpoint(self):
        cp = make_checkpoint({"state": "safe"})
        cp["sha256"] = "0" * 64
        d = recovery_gate(cp, Signals(energy_ratio=0.8, dependencies_ok=True))
        self.assertEqual(d.mode, Mode.QUARANTINED)
        self.assertEqual(d.status, GateStatus.FAIL)

    def test_threshold_validation_blocks_unsafe_configuration(self):
        with self.assertRaises(ValueError):
            decide(
                Signals(energy_ratio=0.9, dependencies_ok=True),
                Thresholds(low_energy=0.8, resume_energy=0.2),
            )

    def test_network_requirement_is_fail_closed(self):
        d = decide(Signals(
            energy_ratio=0.9,
            dependencies_ok=True,
            network_required=True,
            network_ok=False,
        ))
        self.assertEqual(d.mode, Mode.DORMANT)
        self.assertEqual(d.status, GateStatus.PARTIAL)

    def test_evidence_manifest_marks_analogy_boundary(self):
        m = evidence_manifest()
        self.assertEqual(m["status"], "SUPPORTED_ANALOGY")
        self.assertTrue(m["policy"]["no_biological_equivalence_claims"])
        for row in m["mapping"].values():
            self.assertIn("analogy", row["claim_boundary"].lower())

    def test_report_hash_is_deterministic(self):
        scenarios = [
            {"id": "healthy", "signals": {"energy_ratio": 0.9, "dependencies_ok": True}},
            {"id": "low", "signals": {"energy_ratio": 0.1, "dependencies_ok": True}},
        ]
        a = scenario_report(scenarios)
        b = scenario_report(scenarios)
        self.assertEqual(a["sha256"], b["sha256"])

    def test_bundle_emits_verifiable_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            out = write_bundle(Path(td))
            ep = Path(out["evidence"])
            rp = Path(out["scenario_report"])
            self.assertTrue(ep.exists())
            self.assertTrue(rp.exists())
            evidence = json.loads(ep.read_text(encoding="utf-8"))
            report = json.loads(rp.read_text(encoding="utf-8"))
            self.assertEqual(evidence["sha256"], out["evidence_sha256"])
            self.assertEqual(report["sha256"], out["scenario_sha256"])
            self.assertEqual(len(report["scenarios"]), 4)


if __name__ == "__main__":
    unittest.main()
