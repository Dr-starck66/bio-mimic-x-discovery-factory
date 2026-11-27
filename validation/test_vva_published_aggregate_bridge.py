#!/usr/bin/env python3
"""Integrity and negative tests for literature-aggregate only workflow."""
import copy
import json
from pathlib import Path
import unittest
from vva_published_aggregate_bridge import audit

DOC = json.loads((Path(__file__).parent / "data/vva_published_trial_aggregates_20261123.json").read_text())

class TestPublishedData(unittest.TestCase):
    def test_real_report_has_correct_study_count(self):
        out = audit(DOC)
        self.assertEqual(out["independent_studies"], 2)

    def test_cytology_superficial_retention(self):
        e = audit(DOC)["study_results"]["chen2018_erzhi"]["endpoints"]["superficial_cells_pct"]
        self.assertAlmostEqual(e["control_adjusted_change_week12"], 5.02)
        self.assertAlmostEqual(e["control_adjusted_change_week16_off"], 4.12)
        self.assertAlmostEqual(e["descriptive_retention_pct"], 100 * 4.12 / 5.02, places=4)

    def test_basal_direction_correct(self):
        e = audit(DOC)["study_results"]["chen2018_erzhi"]["endpoints"]["basal_cells_pct"]
        self.assertAlmostEqual(e["control_adjusted_change_week12"], 23.02)
        self.assertAlmostEqual(e["control_adjusted_change_week16_off"], 17.97)

    def test_decline_after_withdrawal(self):
        for n in ("superficial_cells_pct", "basal_cells_pct", "vaginal_health_score", "moisture_score"):
            e = audit(DOC)["study_results"]["chen2018_erzhi"]["endpoints"][n]
            self.assertLess(e["adjusted_change_after_withdrawal"], 0)

    def test_negative_no_ecm_and_no_proof(self):
        r = audit(DOC)
        self.assertFalse(r["durable_ECM_regeneration_proven"])
        self.assertFalse(r["biological_repair_proven"])
        self.assertFalse(r["study_results"]["chen2018_erzhi"]["complete_core_3domain_gate_available"])

    def test_symptoms_cannot_replace_cytology(self):
        r = audit(DOC)["study_results"]["mitchell2018_estradiol_moisturizer"]
        self.assertAlmostEqual(r["symptom_MBS_change_active_vs_placebo"], -0.1)
        self.assertAlmostEqual(r["VMI_responder_percentage_point_difference_estradiol_vs_placebo"], 46)

    def test_no_pvalue_reconstructed(self):
        r = audit(DOC)
        self.assertIsNone(r["study_results"]["chen2018_erzhi"]["endpoints"]["superficial_cells_pct"]["inferential_p_value"])

    def test_forged_withdrawal_refused(self):
        doc = copy.deepcopy(DOC)
        doc["studies"][0]["timepoints"] = ["pre", "week12_on", "week16_on"]
        with self.assertRaisesRegex(ValueError, "off-intervention"):
            audit(doc)

    def test_missing_values_refused(self):
        doc = copy.deepcopy(DOC)
        doc["studies"][0]["endpoints"][0]["means"]["active"][2] = None
        with self.assertRaisesRegex(ValueError, "finite"):
            audit(doc)

    def test_nonfinite_refused(self):
        doc = copy.deepcopy(DOC)
        doc["studies"][0]["endpoints"][0]["means"]["active"][2] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            audit(doc)

    def test_no_pooled_treatment(self):
        r = audit(DOC)
        self.assertEqual(set(r["study_results"]), {"chen2018_erzhi", "mitchell2018_estradiol_moisturizer"})
        self.assertNotIn("pooled_effect", r)

    def test_missing_comparator_refused(self):
        doc = copy.deepcopy(DOC)
        del doc["studies"][1]["endpoints"][0]["values"]["dual_placebo"]
        with self.assertRaisesRegex(ValueError, "comparator"):
            audit(doc)

if __name__ == "__main__":
    unittest.main(verbosity=2)
