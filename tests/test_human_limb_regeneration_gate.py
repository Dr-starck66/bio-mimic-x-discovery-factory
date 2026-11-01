import copy
import json
import unittest
from pathlib import Path

from factory.human_limb_regeneration_gate import build_report, render_markdown

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = """# Bridge
Supported claims: 12
Strict orthology: 4/12 (33.3%)
Verified human translation: 7/12 (58.3%)
"""
GEO = """| GSE74387 | Microarray | x | y | z | **FAIL** (IC) |
| GSE113081 | RNA-seq | x | y | z | **PASS individuel** |
Le critère n'est PAS satisfait.
"""


class TestHumanLimbRegenerationGate(unittest.TestCase):
    def test_real_repository_sources_fail_closed(self):
        report = build_report(
            (ROOT / "reports/factory/HUMAN-BRIDGE-LATEST.md").read_text(encoding="utf-8"),
            json.loads((ROOT / "factory/external_validation_registry.json").read_text(encoding="utf-8")),
            (ROOT / "validation/NOTE-INTERPRETATION-GEO-2026-10-27.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(report["human_limb_regeneration_status"], "UNVERIFIED")
        self.assertEqual(report["retro_geo"]["global_replication"], "FAIL_PRE_REGISTERED_REPLICATION")
        self.assertEqual(report["human_bridge"]["translated_candidates"], 7)
        self.assertEqual(report["external_review_registry_entries"], 0)
        self.assertIn("UNVERIFIED", render_markdown(report))

    def test_perfect_orthology_is_not_human_regrowth(self):
        perfect = BRIDGE.replace("4/12", "12/12").replace("7/12", "12/12")
        fake_review = {"validations": [{"validator_name": "Claimed reviewer", "verdict": "SUPPORTS_FURTHER_TESTING"}]}
        report = build_report(perfect, fake_review, GEO)
        self.assertEqual(report["human_bridge"]["translated_candidates"], 12)
        self.assertEqual(report["human_limb_regeneration_status"], "UNVERIFIED")
        self.assertEqual(report["prospective_independent_biological_replication"], "UNVERIFIED")

    def test_negative_cohort_is_not_relabelled_as_success(self):
        report = build_report(BRIDGE, {"validations": []}, GEO)
        self.assertEqual(report["retro_geo"]["GSE74387"], "FAIL_ORIGINAL_CI_INCLUDES_ZERO")
        self.assertEqual(report["retro_geo"]["GSE113081"], "PASS_SINGLE_COHORT_ONLY")
        self.assertTrue(report["retro_geo"]["negative_controls_preserved"])

    def test_missing_geo_source_never_promotes(self):
        report = build_report(BRIDGE, {"validations": []}, "No accessible GEO outcome")
        self.assertEqual(report["retro_geo"]["global_replication"], "UNVERIFIED_SOURCE")
        self.assertEqual(report["human_limb_regeneration_status"], "UNVERIFIED")

    def test_incoherent_bridge_counts_rejected(self):
        with self.assertRaises(ValueError):
            build_report(BRIDGE.replace("4/12", "9/12"), {"validations": []}, GEO)

    def test_replay_is_deterministic(self):
        a = build_report(BRIDGE, {"validations": []}, GEO)
        b = build_report(BRIDGE, copy.deepcopy({"validations": []}), GEO)
        self.assertEqual(a["sha256"], b["sha256"])


if __name__ == "__main__":
    unittest.main()
