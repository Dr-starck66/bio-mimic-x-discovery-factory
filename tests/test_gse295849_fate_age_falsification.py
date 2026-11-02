"""Adversarial tests: authentic previously verified GSE295849 source + synthetic negatives."""
import json
import math
import unittest

from validation.gse295849_fate_age_falsification import (
    SOURCE, build, compare, sign_p_two_sided, validate,
)


class FateVsAgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.report = build(cls.source)

    def test_committed_scientific_evidence_does_not_overclaim(self):
        from pathlib import Path
        p=SOURCE.parent / "GSE295849-FATE-AGE-RESULTS-2026-11-02.json"
        evidence=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(evidence["source_report_git_blob_sha"],
                         "949b0f822023d121a3af759097722dd4cbb1294d")
        self.assertEqual(evidence["status_fate_independent_age_reset"],"UNVERIFIED")
        self.assertEqual(evidence["status_mechanistic_causality"],"UNVERIFIED")
        self.assertEqual(evidence["negative_control_GSE74387"],"FAIL_RETAINED")
        for reported_key,analysis_key in (
            ("D14_to_LP_within_iNSC","iNSC_D14_to_LP"),
            ("LP_iNSC_to_LP_smNPC_fate_control",None),
        ):
            actual=(self.report["same_label_time_course"][analysis_key] if analysis_key
                    else self.report["alternative_fate_negative_control_iNSC_vs_smNPC"])
            recorded=evidence["comparisons"][reported_key]
            self.assertEqual(actual["n_independent_donors"],recorded["independent_donors"])
            self.assertEqual(actual["n_clock_decreases"],recorded["decrease_donors"])
            self.assertAlmostEqual(actual["mean_delta_years"],recorded["mean_delta_years"],places=4)

    def test_real_iNSC_D14_to_LP_donor_paired(self):
        c = self.report["same_label_time_course"]["iNSC_D14_to_LP"]
        self.assertEqual((c["n_independent_donors"], c["n_clock_decreases"]), (6,6))
        self.assertAlmostEqual(c["mean_delta_years"], -39.58073, places=4)
        self.assertAlmostEqual(c["median_delta_years"], -40.48185, places=4)
        self.assertEqual(c["two_sided_exact_sign_p_unadjusted"], .03125)

    def test_same_identity_label_not_same_molecular_identity(self):
        self.assertEqual(self.report["identity_constant_at_molecular_level"],"UNVERIFIED")
        self.assertEqual(self.report["age_reset_independent_of_cell_fate"],"UNVERIFIED")
        self.assertIn("consolidation", self.report["interpretation"])

    def test_timecourse_scientific_controls(self):
        cs = self.report["same_label_time_course"]
        self.assertEqual((cs["iNSC_D14_to_D26"]["n_independent_donors"],
                          cs["iNSC_D14_to_D26"]["n_clock_decreases"]), (4,4))
        self.assertEqual((cs["iNSC_D26_to_LP"]["n_independent_donors"],
                          cs["iNSC_D26_to_LP"]["n_clock_decreases"]), (4,4))
        self.assertEqual((cs["iNSC_LP_to_HP"]["n_independent_donors"],
                          cs["iNSC_LP_to_HP"]["n_clock_decreases"]), (3,3))
        self.assertEqual(cs["iNSC_LP_to_HP"]["two_sided_exact_sign_p_unadjusted"], .25)

    def test_same_slide_batch_restriction(self):
        c=self.report["same_slide_sensitivity_D14_to_LP"]
        self.assertEqual(c["n_independent_donors"],3)
        self.assertEqual(c["n_clock_decreases"],3)
        self.assertEqual({x["genotype"] for x in c["pairs"]},{"286","287","288"})
        self.assertTrue(all(x["same_Illumina_slide"] for x in c["pairs"]))

    def test_alternative_cell_fate_negative_control(self):
        c=self.report["alternative_fate_negative_control_iNSC_vs_smNPC"]
        self.assertEqual(c["n_independent_donors"],9)
        self.assertEqual(c["n_clock_decreases"],9)
        self.assertEqual(self.report["fate_matters"],"YES_ALTERNATIVE_FATE_HAS_DIFFERENT_CLOCK_OUTPUT")

    def test_perturbations_are_not_clinical_anti_aging(self):
        cs=self.report["LP_perturbations_not_age_treatments"]
        self.assertEqual(cs["NGN2"]["n_independent_donors"],3)
        self.assertEqual(cs["NGN2"]["n_increased"],3)
        self.assertEqual(cs["Glycerol"]["n_increased"],3)
        self.assertEqual(cs["Thymidine"]["n_increased"],1)
        self.assertEqual(cs["Thymidine"]["n_decreased"],2)
        self.assertEqual(self.report["clinical_anti_aging"],"UNVERIFIED")

    def test_real_source_is_60_independent_chips_not_60_donors(self):
        self.assertEqual(self.report["sample_count"],60)
        self.assertEqual(self.report["donor_count"],12)

    def test_source_hash_change_fails_closed(self):
        mutated=json.loads(json.dumps(self.source))
        mutated["model_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"model SHA"):
            build(mutated)

    def test_duplicate_GSM_fails_closed(self):
        mutated=json.loads(json.dumps(self.source))
        mutated["sample_level_ages"][1]["gsm"]=mutated["sample_level_ages"][0]["gsm"]
        with self.assertRaisesRegex(ValueError,"duplicate/missing"):
            build(mutated)

    def test_missing_one_raw_sample_fails_closed(self):
        mutated=json.loads(json.dumps(self.source))
        mutated["sample_level_ages"].pop()
        with self.assertRaisesRegex(ValueError,"60 GEO"):
            build(mutated)

    def test_adversarial_one_donor_increases_age(self):
        fixture=[
            dict(chip_sample_id="111111111111_R01C01",gsm="GSM1",
                 donor_genotype="1",cell_type="iNSC",stage="D14",treatment="None",part="1",clock_age_years=20.0),
            dict(chip_sample_id="111111111111_R02C01",gsm="GSM2",
                 donor_genotype="1",cell_type="iNSC",stage="LP",treatment="None",part="1",clock_age_years=35.0),
            dict(chip_sample_id="222222222222_R01C01",gsm="GSM3",
                 donor_genotype="2",cell_type="iNSC",stage="D14",treatment="None",part="2",clock_age_years=40.0),
            dict(chip_sample_id="222222222222_R02C01",gsm="GSM4",
                 donor_genotype="2",cell_type="iNSC",stage="LP",treatment="None",part="2",clock_age_years=10.0)
        ]
        validate(fixture,strict=False)
        c=compare(fixture,"iNSC","D14","iNSC","LP")
        self.assertEqual(c["n_clock_increases"],1)
        self.assertEqual(c["n_clock_decreases"],1)
        self.assertEqual(c["two_sided_exact_sign_p_unadjusted"],1)

    def test_sign_test_small_n_not_overstated(self):
        self.assertEqual(sign_p_two_sided([-1]*6),.03125)
        self.assertEqual(sign_p_two_sided([-1]*4),.125)
        self.assertEqual(sign_p_two_sided([-1]*3),.25)
        self.assertIsNone(sign_p_two_sided([0,0]))


if __name__=="__main__":
    unittest.main()
