import copy
import json
import unittest
from pathlib import Path
from vva_independent_histology_gate import audit, fisher_two_sided

FIXTURE=json.loads((Path(__file__).parent/'data/vva_independent_histology_20261123.json').read_text())

class TestStructuralAudit(unittest.TestCase):
    def test_primary_exact_effect(self):
        r=audit(FIXTURE)
        self.assertAlmostEqual(r['histology']['risk_difference_percentage_points'],-3.4091,places=3)
        self.assertEqual(r['histology']['fisher_exact_two_sided_p'],1.0)
    def test_negative_sham_superior_to_active(self):
        self.assertLess(audit(FIXTURE)['histology']['risk_difference_percentage_points'],0)
    def test_offtreatment_unverified(self):
        r=audit(FIXTURE)
        self.assertIsNone(r['histology']['verified_months_after_last_treatment'])
        self.assertFalse(r['gates']['off_treatment_at_least_3_months_verified'])
    def test_structure_not_clinically_claimed(self):
        self.assertFalse(audit(FIXTURE)['durable_structural_regeneration_proven'])
    def test_human_GSE_not_washout(self):
        self.assertFalse(audit(FIXTURE)['GSE11622']['post_cessation_data'])
    def test_no_TEER(self):
        self.assertFalse(audit(FIXTURE)['gates']['functional_barrier_TEER'])
    def test_no_quantitative_ECM(self):
        self.assertFalse(audit(FIXTURE)['gates']['quantitative_collagen_elastin_architecture'])
    def test_no_paired_raw_data(self):
        self.assertFalse(audit(FIXTURE)['gates']['paired_source_raw_data_downloaded'])
    def test_misdated_histology_refused(self):
        d=copy.deepcopy(FIXTURE);d['histology_sham_rct']['histology_time_months_after_first_treatment']=12
        with self.assertRaisesRegex(ValueError,'histology time'): audit(d)
    def test_false_last_dose_date_refused(self):
        d=copy.deepcopy(FIXTURE);d['histology_sham_rct']['last_treatment_date_known']=True
        with self.assertRaisesRegex(ValueError,'last treatment date'): audit(d)
    def test_false_GSE_withdrawal_refused(self):
        d=copy.deepcopy(FIXTURE);d['transcriptomics_GSE11622']['documented_off_treatment_followup']=True
        with self.assertRaisesRegex(ValueError,'do not invent'): audit(d)
    def test_bad_counts_refused(self):
        d=copy.deepcopy(FIXTURE);d['histology_sham_rct']['treated']['improved']=23
        with self.assertRaises(ValueError):audit(d)
    def test_fisher_symmetry(self):
        self.assertEqual(fisher_two_sided(2,22,3,24),fisher_two_sided(3,24,2,22))
    def test_fisher_extreme(self):
        self.assertLess(fisher_two_sided(10,10,0,10),0.001)
    def test_fisher_null(self):
        self.assertEqual(fisher_two_sided(0,10,0,10),1.0)

if __name__=='__main__':unittest.main(verbosity=2)
