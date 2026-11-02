"""No false biomed inference from public RNA+DNAm lifespan study."""
import unittest
from math import sin
from validation.gse179849_rna_gene_age_adjustment import slopes,EXPECTED,SRC,FIBRO

class RealAgingRNAAdjustmentLogicTests(unittest.TestCase):
    def setUp(self):
        self.obs=[]
        for group in range(5):
            donor=f"HC{group+1}"
            for passage in range(5,11):
                z=sin(passage*1.31+group*2.0)
                self.obs.append({
                    "sample_key":f"{donor}_sp1_Normal_Control_ox21_p{passage}",
                    "passage":passage,"cell_line":donor,
                    "RNA_fibroblast_score":z,
                    "clocks":{"Horvath1":9+group*3+passage*2.0+z*1.2,
                              "GrimAge":30-group-passage*0.4-z*0.5}})
    def test_adjustment_recovers_true_synthetic_relationship(self):
        r=slopes(self.obs)
        self.assertEqual(r["n_control_samples"],30)
        self.assertEqual(r["n_control_series"],5)
        self.assertAlmostEqual(r["RNA_adjusted_slope_years_per_passage"],2.0,places=4)
        self.assertEqual(r["causal_rejuvenation"],"UNVERIFIED")
        self.assertEqual(r["same_physical_aliquot"],"UNVERIFIED")
    def test_unfavorable_grimage_negative_control_preserved(self):
        r=slopes(self.obs,clock="GrimAge")
        self.assertAlmostEqual(r["RNA_adjusted_slope_years_per_passage"],-0.4,places=4)
        self.assertLess(r["unadjusted_slope_years_per_passage"],0)
    def test_fake_sample_size_fails(self):
        with self.assertRaisesRegex(ValueError,"unverifiable"):
            slopes(self.obs[:10])
    def test_actual_public_source_is_bounded_and_fibro_panel_declared(self):
        self.assertEqual(EXPECTED,60622846)
        self.assertIn("GSE179848_processed_cell_lifespan_RNAseq_data.csv.gz",SRC)
        self.assertEqual(FIBRO,("COL1A1","COL1A2","DCN","LUM","FN1","THY1"))

if __name__=="__main__":unittest.main()
