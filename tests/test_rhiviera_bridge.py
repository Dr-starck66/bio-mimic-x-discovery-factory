"""Provenance, falsification and direct BIO-MIMIC engine integration tests."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from factory.hypothesis_engine import generate_hypotheses
from factory.debate_engine import debate_hypotheses
from factory.experiment_planner import plan_experiments
from factory.scientific_memory import load_memory, update_scientific_memory
from research.hiv_cure_omega.rhiviera_bridge import (
    SOURCE, run_bridge, validate_evidence, _digest,
)

DATA = json.loads(SOURCE.read_text(encoding="utf-8"))


class RhivieraBridgeTests(unittest.TestCase):
    def test_integration_calls_real_factory_engines(self):
        self.assertEqual(generate_hypotheses.__module__, "factory.hypothesis_engine")
        self.assertEqual(debate_hypotheses.__module__, "factory.debate_engine")
        self.assertEqual(plan_experiments.__module__, "factory.experiment_planner")
        report = run_bridge(DATA)
        self.assertEqual(report["studies_checked"], 6)
        self.assertEqual(report["hypotheses_generated"], 18)
        self.assertEqual(report["conceptual_plans_generated"], 12)
        self.assertFalse(report["clinical_cure_proven"])
        self.assertEqual(len(report["engines_invoked"]), 3)

    def test_every_output_is_hypothesis_not_cure(self):
        report = run_bridge(DATA)
        for d in report["dossiers"]:
            self.assertFalse(d["eradication_demonstrated"])
            for h in d["hypotheses"]:
                self.assertEqual(h["status"], "HYPOTHESIS")
                self.assertFalse(h["clinical_efficacy_claim"])
            for p in d["conceptual_plans"]:
                self.assertEqual(p["status"], "PROPOSED_NOT_EXECUTED")
                self.assertFalse(p["clinical_efficacy_claim"])
            primary = next(h for h in d["hypotheses"] if h["kind"] == "PRIMARY_CAUSAL")
            self.assertEqual(d["adversarial_review"]["status_by_hypothesis"][primary["id"]],
                             "NEEDS_CAUSAL_EVIDENCE")

    def test_deterministic_provenance_hash(self):
        self.assertEqual(run_bridge(DATA)["report_sha256"], run_bridge(DATA)["report_sha256"])

    def test_siv_cannot_be_relabelled_human(self):
        wrong = deepcopy(DATA)
        wrong["records"][2]["species"] = "human"
        self.assertTrue(validate_evidence(wrong))
        with self.assertRaises(ValueError):
            run_bridge(wrong)

    def test_trial_protocol_cannot_become_result(self):
        wrong = deepcopy(DATA)
        wrong["records"][1]["has_results"] = True
        self.assertTrue(validate_evidence(wrong))

    def test_rio_is_not_a_rhiviera_trial(self):
        wrong = deepcopy(DATA)
        wrong["independent_comparator"]["relation"] = "anrs_trial"
        self.assertTrue(validate_evidence(wrong))
        self.assertNotIn("RIO-2026", {r["id"] for r in DATA["records"]})

    def test_fabricated_eradication_is_blocked(self):
        wrong = deepcopy(DATA)
        wrong["records"][3]["eradication_demonstrated"] = True
        self.assertTrue(validate_evidence(wrong))

    def test_missing_negative_control_is_blocked(self):
        wrong = deepcopy(DATA)
        wrong["records"][4]["negative_control"] = ""
        self.assertTrue(validate_evidence(wrong))

    def test_invalid_source_is_blocked(self):
        wrong = deepcopy(DATA)
        wrong["records"][0]["source_url"] = "http://example.invalid/trial"
        self.assertTrue(validate_evidence(wrong))

    def test_memory_engine_accepts_hypotheses_without_promoting_claim(self):
        report = run_bridge(DATA)
        dossiers = [
            {"program_id": "RHIVIERA-PUBLIC-" + d["record_id"],
             "subject": d["observation"],
             "sha256": _digest(d),
             "reasoning_status": "HYPOTHESIS_ONLY_NOT_CLINICALLY_VALIDATED",
             "hypotheses": d["hypotheses"]}
            for d in report["dossiers"]
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rhiviera_memory.json"
            status = update_scientific_memory(path, dossiers)
            self.assertEqual(status["programs"], 6)
            self.assertEqual(status["hypotheses"], 18)
            mem = load_memory(path)
            self.assertEqual(len(mem["programs"]), 6)
            self.assertTrue(all(h["clinical_efficacy_claim"] is False
                                for h in mem["hypotheses"].values()))


if __name__ == "__main__":
    unittest.main()
