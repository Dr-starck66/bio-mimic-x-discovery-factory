import math
import unittest
from validation.adaptamer_control import Parameters, switch_output, simulate, evaluate_measurements, run_report


class AdaptamerModelTests(unittest.TestCase):
    def test_zero_drug_equals_leak(self):
        p = Parameters()
        self.assertAlmostEqual(switch_output(0, p), p.basal_fraction)

    def test_dose_response_monotonic_and_saturating(self):
        values = [switch_output(d) for d in (0, 0.1, 0.5, 1, 2, 10, 100)]
        self.assertEqual(values, sorted(values))
        self.assertLess(values[-1], 1)

    def test_adar_negative_control(self):
        self.assertAlmostEqual(switch_output(100, adar_fraction=0), Parameters().basal_fraction)

    def test_protein_decays_after_withdrawal(self):
        rows = simulate()
        def protein(t):
            return next(r["protein_normalized"] for r in rows if r["time_h"] == t)
        self.assertGreater(protein(24), protein(0))
        self.assertGreater(protein(24), protein(72))
        self.assertGreater(protein(72), protein(0))

    def test_reject_bad_numbers_and_schedules(self):
        for d in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                switch_output(d)
        with self.assertRaises(ValueError):
            Parameters(protein_half_life_h=0)
        with self.assertRaises(ValueError):
            simulate(step_h=0.0)

    def test_no_external_data_is_not_certified(self):
        self.assertEqual(run_report()["external_validation"]["status"], "UNVERIFIED")

    @staticmethod
    def measurements(on=3.0, withdrawal=1.1, off_target=0.002):
        records=[]
        for laboratory, doi in (("lab_1", "10.1000/one"), ("lab_2", "10.1000/two")):
            for arm, protein in (("off", 1.0), ("on", on), ("withdrawal", withdrawal), ("switch_negative", 1.02)):
                for replicate in ("a", "b", "c"):
                    records.append({"laboratory":laboratory, "study_doi":doi,
                                    "arm":arm, "replicate":replicate,
                                    "protein":protein, "viability_pct":96,
                                    "offtarget_fraction":off_target})
        return records

    def test_synthetic_fixture_passes_numeric_gate_not_biology(self):
        result = evaluate_measurements(self.measurements())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["biological_validation"], "UNVERIFIED")
        self.assertEqual(result["external_provenance"], "REVIEW_REQUIRED")

    def test_falsification_with_persistent_expression(self):
        result = evaluate_measurements(self.measurements(withdrawal=2.9))
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["criteria"]["withdrawal_80pct_reversal"])

    def test_falsification_with_adverse_signal(self):
        result = evaluate_measurements(self.measurements(off_target=0.06))
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["criteria"]["offtarget_at_most_1pct"])

    def test_insufficient_external_coverage(self):
        rows = self.measurements()
        result = evaluate_measurements([r for r in rows if r["laboratory"] == "lab_1"])
        self.assertEqual(result["status"], "UNVERIFIED")

    def test_malformed_observation_rejected(self):
        rows = self.measurements()
        rows[0]["viability_pct"] = math.nan
        self.assertEqual(evaluate_measurements(rows)["status"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()