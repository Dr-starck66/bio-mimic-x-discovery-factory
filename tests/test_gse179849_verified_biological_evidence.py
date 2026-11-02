"""Audit signed aging-clock results and never upgrade observational evidence to causal rejuvenation."""
import json
import unittest
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"reports/factory/GSE179849-REAL-ORTHOGONAL-RNA-ADJUSTED-AGING-2026-11-02.json"
class PublishedOrthogonalBiologicalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=json.loads(DATA.read_text(encoding="utf8"))
    def test_raw_RNA_provenance_has_60MB_gzip_and_real_marker_panel(self):
        p=self.r["provenance"]
        self.assertEqual(p["public_processed_RNA_compressed_bytes"],60622846)
        self.assertEqual(p["RNA_gene_rows_examined"],28633)
        self.assertTrue(p["RNA_gzip_crc_verified"])
        self.assertEqual(len(p["RNA_file_SHA256"]),64)
        self.assertEqual(len(self.r["predeclared_fibroblast_identity_genes"]),6)
    def test_same_condition_pairing_and_no_aliquot_claim(self):
        c=self.r["cohort"]
        self.assertEqual(c["exact_donor_experiment_treatment_passage_matches"],109)
        self.assertEqual(c["real_RNA_measurements_fully_extracted_for_matched_samples"],102)
        self.assertEqual(c["independent_healthy_donor_lines"],3)
        self.assertFalse(self.r["analysis"]["same_physical_aliquot_verified"])
        self.assertEqual(self.r["scientific_boundaries"]["same_physical_aliquot"],"UNVERIFIED")
    def test_scientific_result_and_unfavorable_grimage(self):
        a=self.r["analysis"]
        self.assertAlmostEqual(a["unadjusted_Horvath1_years_per_passage"],2.062966)
        self.assertAlmostEqual(a["adjusted_Horvath1_years_per_passage"],1.930454)
        self.assertLess(self.r["negative_control"]["after_years_per_passage"],0)
        self.assertEqual(self.r["scientific_boundaries"]["rejuvenation_under_reprogramming"],"UNVERIFIED")
        self.assertIn("3 independent donors",a["formal_inference"])
    def test_negative_holdout_not_hidden_and_zero_spend(self):
        p=self.r["leave_one_donor_out"]
        self.assertEqual(len(p),3)
        self.assertEqual({x["excluded"] for x in p},{"HC1","HC2","HC4"})
        self.assertTrue(all(x["Horvath1_after"]>0 and x["GrimAge_after"]<0 for x in p))
        self.assertEqual(self.r["audit"]["new_infrastructure_cost_eur"],0)

if __name__=="__main__":unittest.main()
