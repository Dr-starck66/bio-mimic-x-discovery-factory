import unittest
from validation.pat_tissue_function_gate import analyze, exact_sign_p


def record(donor, arm, teer, permeability, cells=100000, confluence=98):
    return {"donor_id": str(donor), "arm": arm, "teer_ohm_cm2": teer,
            "permeability_cm_s": permeability, "viable_cell_count": cells,
            "confluence_pct": confluence}


def fixture(growth_only=False, missing_feedback=False, donors=8, replicated=False):
    records = []
    for donor in range(donors):
        rows = [record(donor, "static", 350, 2.0e-6),
                record(donor, "feedback", 400, 1.5e-6)]
        if growth_only:
            rows.append(record(donor, "predictive", 400, 1.5e-6, cells=180000))
        else:
            rows.append(record(donor, "predictive", 500, 1.0e-6))
        for row in rows:
            if row["arm"] == "feedback" and missing_feedback:
                continue
            records.append(row)
            if replicated:
                records.append(dict(row))
    return {"metadata": {"randomized": True, "blinded_readout": True,
                         "protocol_locked": True, "flow_matched": True},
            "records": records}


class TestTissueFunctionGate(unittest.TestCase):
    def test_no_records_is_unverified(self):
        self.assertEqual(analyze({"records": []})["status"], "UNVERIFIED")

    def test_synthetic_benefit_not_reported_as_biological_pass(self):
        result = analyze(fixture())
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["matched_donors"], 8)
        self.assertGreater(result["teer_median_ratio"], 1.1)
        self.assertLess(result["permeability_median_ratio"], .9)

    def test_growth_only_negative_control_fails(self):
        result = analyze(fixture(growth_only=True))
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["cell_growth_and_confluence_comparable"])

    def test_missing_feedback_cannot_claim_predictive_gain(self):
        self.assertEqual(analyze(fixture(missing_feedback=True))["status"], "UNVERIFIED")

    def test_only_three_donors_are_insufficient(self):
        self.assertEqual(analyze(fixture(donors=3))["status"], "UNVERIFIED")

    def test_technical_wells_are_not_extra_donors(self):
        result = analyze(fixture(donors=3, replicated=True))
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertEqual(result["matched_donors"], 3)

    def test_unblinded_metadata_is_unverified(self):
        data = fixture()
        data["metadata"]["blinded_readout"] = False
        self.assertEqual(analyze(data)["status"], "UNVERIFIED")

    def test_exact_sign(self):
        self.assertAlmostEqual(exact_sign_p(8, 8), 1/256)


if __name__ == "__main__":
    unittest.main()


class TestAdditionalFalsification(unittest.TestCase):
    def test_flow_unmatched_must_not_claim_benefit(self):
        data = fixture()
        data["metadata"]["flow_matched"] = False
        r = analyze(data)
        self.assertEqual(r["status"], "UNVERIFIED")
        self.assertIn("flow_matched", r["missing_design_assertions"])

    def test_unchanged_function_must_fail_even_with_viable_growth(self):
        r = analyze(fixture(growth_only=True))
        self.assertEqual(r["reason"], "FUNCTIONAL_SUPERIORITY_GATE_NOT_MET")
        self.assertEqual(r["teer_median_ratio"], 1.0)
        self.assertEqual(r["permeability_median_ratio"], 1.0)
