"""Exact count check; original individual data are not available."""
import unittest
from research.hiv_cure_omega.pvisconti.published_counts import calculate, compare, fisher_exact_2sided

class PublishedCountTests(unittest.TestCase):
    def test_reference_cohort(self):
        r=compare(9,11,2,11)
        self.assertAlmostEqual(r["odds_ratio"],20.25)
        self.assertAlmostEqual(r["fisher_exact_p_two_sided"],0.008922192358724868,places=12)
    def test_hua_subset_not_confirmatory(self):
        r=compare(8,9,2,4)
        self.assertAlmostEqual(r["fisher_exact_p_two_sided"],0.2027972027972028,places=12)
        self.assertLess(r["risk_difference_newcombe_95_ci"][0],0)
    def test_non_independence_and_no_cure(self):
        r=calculate()
        self.assertEqual(r["underlying_siv_cohort_count"],1)
        self.assertFalse(r["raw_source_xlsx_verified"])
        self.assertTrue(r["do_not_meta_analyze"])
        self.assertFalse(r["clinical_hiv_cure_demonstrated"])
    def test_known_exact_null(self):
        self.assertAlmostEqual(fisher_exact_2sided(1,1,1,1),1.0)
