"""Independent archival checks of six genuine public methylation-clock/RNA scores.

These tests do NOT certify causal cell rejuvenation. They fail closed if
the original unfavorable GrimAge result disappears or the age-model slopes
are re-labelled as a cell-reprogramming intervention.
"""
import json
import unittest
from pathlib import Path

REPORT=Path(__file__).resolve().parents[1]/"reports/factory/GSE179849-INDEPENDENT-6-CLOCK-RNA-IDENTITY-SENSITIVITY-2026-11-04.json"
class SixClockRNAFateSensitivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(REPORT.read_text(encoding="utf-8"))
    def test_six_clocks_are_reported_without_favorable_selection(self):
        xs=self.d["results"]
        self.assertEqual(len(xs),6)
        self.assertEqual({x["clock"] for x in xs},
          {"Horvath1","Horvath2","PhenoAge","PCHorvath2","PCPhenoAge","GrimAge"})
        self.assertTrue(all(x["signal_sign_persists"] for x in xs))
        self.assertEqual(sum(x["years_per_passage_after_RNA_adjustment"]>0 for x in xs),5)
    def test_real_previous_RNA_source_hash_and_102_numeric_pairs(self):
        r=self.d["source"]
        self.assertEqual(r["RNA_original_gzip_bytes"],60622846)
        self.assertEqual(r["RNA_original_GZIP_SHA256"],"b5731fa1253a2bd32f0b64c3bd58770e833a3da59dc90c4f8c8d858944b30109")
        self.assertEqual(r["archived_102_numeric_records_SHA256"],"c2ec0711a61cac04d03c85a108fe7a2245ebe418d55cd0cd75b18c9a01ec7bd2")
        self.assertEqual(self.d["population"]["matching_RNA_DNAm_condition_records"],102)
        self.assertEqual(self.d["population"]["analyzed_untreated_healthy_control_samples"],42)
    def test_age_clock_sign_and_discordant_negative_grimage(self):
        x={o["clock"]:o for o in self.d["results"]}
        self.assertAlmostEqual(x["Horvath1"]["years_per_passage_before"],2.062966,places=6)
        self.assertAlmostEqual(x["Horvath1"]["years_per_passage_after_RNA_adjustment"],1.930454,places=6)
        self.assertAlmostEqual(x["GrimAge"]["years_per_passage_before"],-1.16736,places=5)
        self.assertAlmostEqual(x["GrimAge"]["years_per_passage_after_RNA_adjustment"],-1.238104,places=6)
        self.assertLess(x["GrimAge"]["years_per_passage_after_RNA_adjustment"],0)
    def test_leave_one_healthy_donor_out(self):
        x=self.d["leave_one_donor_out"]
        self.assertEqual(set(x),{"HC1","HC2","HC4"})
        self.assertTrue(all(v["Horvath1_RNA_adjusted"]>0 for v in x.values()))
        self.assertTrue(all(v["GrimAge_RNA_adjusted"]<0 for v in x.values()))
        self.assertTrue(all(v["healthy_donors"]==2 for v in x.values()))
    def test_no_fictitious_CI_or_rejuvenation(self):
        d=self.d
        self.assertEqual(d["population"]["independent_healthy_donor_lines"],3)
        self.assertFalse(d["population"]["marker_panel_validated_as_cell_fate_in_this_dataset"])
        self.assertIn("NO VALID INFERENCE",d["models"]["formal_inference"])
        self.assertEqual(d["status_at_claim_levels"]["cell_rejuvenation_independent_of_fate"],"UNVERIFIED")
        self.assertEqual(d["status_at_claim_levels"]["clinical_rejuvenation"],"UNVERIFIED")
        self.assertEqual(d["audit_reexecution"]["cost_new_eur"],0)

if __name__=="__main__":unittest.main()
