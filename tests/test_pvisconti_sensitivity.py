"""No external data needed: test the statistical summary safety gates."""
import csv
import tempfile
import unittest
from pathlib import Path

from research.hiv_cure_omega.pvisconti.sensitivity import analyse, holm_adjust


class TestPVISCONTISensitivity(unittest.TestCase):
    def test_holm_core(self):
        self.assertEqual(holm_adjust([0.003, 0.006, 0.047]), [0.009, 0.012, 0.047])

    def test_holm_order_invariant(self):
        self.assertEqual(holm_adjust([0.047, 0.006, 0.003]), [0.047, 0.012, 0.009])

    def test_reject_invalid_p(self):
        with self.assertRaises(ValueError):
            holm_adjust([1.1])

    def test_reject_empty_p(self):
        with self.assertRaises(ValueError):
            holm_adjust([])

    def test_no_independence_inflation(self):
        output = analyse()
        self.assertEqual(output["underlying_siv_cohorts"], 1)
        self.assertEqual(output["papers"], 3)

    def test_do_not_claim_raw_analysis(self):
        output = analyse()
        self.assertFalse(output["raw_xlsx_retrieved"])
        self.assertFalse(output["raw_statistical_reanalysis_completed"])

    def test_no_cure_claim(self):
        self.assertFalse(analyse()["clinical_eradication_demonstrated"])

    def test_endpoint_count(self):
        self.assertEqual(analyse()["published_endpoints_checked"], 16)

    def test_negative_cd8_extended_family(self):
        d = {r["endpoint"]: r for r in analyse()["charre_6_endpoint_sensitivity"]}
        self.assertEqual(d["CD8_suppression_vs_intact_PNL_preATI"]["p_holm_posthoc"], 0.141)

    def test_preserve_negative_control(self):
        rows = analyse()["results"]
        self.assertEqual([r for r in rows if "negative_control" in r["endpoint"]][0]["p_published"], 0.9)


if __name__ == "__main__":
    unittest.main()
