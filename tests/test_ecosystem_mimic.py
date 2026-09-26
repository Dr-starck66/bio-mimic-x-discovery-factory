import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "factory"))

import ecosystem_mimic


DEMO = {
    "ecosystem_id": "pond-demo",
    "observations": [
        {"time": "2026-01-01", "taxa": {"frog": 10, "beetle": 5}},
        {"time": "2026-02-01", "taxa": {"frog": 11, "beetle": 4, "dragonfly": 2}},
        {"time": "2026-03-01", "taxa": {"frog": 5, "beetle": 2, "dragonfly": 1}, "perturbation": "dry spell"},
        {"time": "2026-04-01", "taxa": {"frog": 10, "beetle": 5, "dragonfly": 2, "bird": 1}},
        {"time": "2026-05-01", "taxa": {"frog": 12, "beetle": 6, "dragonfly": 3, "bird": 2}},
    ],
}


class TestEcosystemMimic(unittest.TestCase):
    def test_diversity_metrics(self):
        self.assertAlmostEqual(ecosystem_mimic.shannon_diversity({"a": 1, "b": 1}), math.log(2))
        self.assertAlmostEqual(ecosystem_mimic.pielou_evenness({"a": 1, "b": 1}), 1.0)
        self.assertAlmostEqual(ecosystem_mimic.bray_curtis({"a": 1}, {"b": 1}), 1.0)

    def test_analysis_detects_succession_and_recovery_without_claiming_causality(self):
        result = ecosystem_mimic.analyze_ecosystem(DEMO)
        self.assertEqual(result["status"], "ANALYZED")
        self.assertEqual(result["observation_count"], 5)
        self.assertEqual(result["metrics"]["latest_richness"], 4)
        self.assertGreater(result["metrics"]["mean_bray_curtis_turnover"], 0)
        self.assertFalse(result["causal_inference"])
        self.assertFalse(result["interaction_inference"])
        self.assertFalse(result["claims_established_truth"])
        self.assertEqual(len(result["sha256"]), 64)
        self.assertIn("RECOVERED_WITHIN_TOLERANCE", {x["status"] for x in result["perturbation_responses"]})
        self.assertTrue(all(h["status"] == "HYPOTHESIS" for h in result["hypotheses"]))

    def test_cofluctuation_is_never_labeled_interaction(self):
        result = ecosystem_mimic.analyze_ecosystem(DEMO)
        self.assertTrue(result["cofluctuation_network"]["edges"])
        for edge in result["cofluctuation_network"]["edges"]:
            self.assertIn("INTERACTION_NOT_INFERRED", edge["semantics"])

    def test_deterministic_fingerprint(self):
        a = ecosystem_mimic.analyze_ecosystem(DEMO)
        b = ecosystem_mimic.analyze_ecosystem(DEMO)
        self.assertEqual(a["sha256"], b["sha256"])

    def test_insufficient_data_fails_closed(self):
        result = ecosystem_mimic.analyze_ecosystem(
            {"ecosystem_id": "empty", "observations": [{"time": "2026-01-01", "taxa": {}}]}
        )
        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertEqual(result["observation_count"], 0)
        self.assertTrue(result["rejected_observations"])
        self.assertEqual(result["hypotheses"], [])


if __name__ == "__main__":
    unittest.main()
