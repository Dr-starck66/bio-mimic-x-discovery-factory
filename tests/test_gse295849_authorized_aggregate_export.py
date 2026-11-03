"""Only synthetic + verified PUBLIC metadata tests. Never require private dbGaP RNA."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from validation.gse295849_authorized_aggregate_export import (
    ROOT, METH, RNA, EXPECTED_DONORS, EXPECTED_RUNS,
    ensure_private_runtime, condition_and_run_gate, release_safe_aggregate,
)

class AuthorizedInstitutionalAggregateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meth=json.loads(METH.read_text(encoding="utf-8"))
        cls.meta=json.loads(RNA.read_text(encoding="utf-8"))

    def setUp(self):
        self.env=patch.dict(os.environ,{"GITHUB_ACTIONS":"false","CI":"false"})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def synthetic_internal(self):
        return {
            "status":"PASS_EXPLORATORY_ORTHOGONAL_RNA_ASSOCIATION_ONLY",
            "donor_pairs":6,
            "pairs":[
                {"donor_genotype":donor,"rna_runs":[f"SECRET{donor}",f"SECRETLP{donor}"],
                 "delta_age_clock_years":-i,"delta_RNA_identity_score":i*0.32}
                for i,donor in enumerate(EXPECTED_DONORS,1)],
            "observed_mean_age_delta_years":-39.58,
            "observed_mean_identity_delta":0.88,
            "slope_age_per_identity_unit":-14.2,
            "identity_constant_intercept_age_delta":-8.11,
            "fit_residual_sd_years":9.2,
            "zero_identity_change_within_observed_support":False,
            "identity_constant_effect_interpretation":"UNVERIFIED_EXTRAPOLATED_OUTSIDE_IDENTITY_SUPPORT",
        }

    def test_public_six_donor_stages_and_12_run_manifest(self):
        runs=condition_and_run_gate(self.meth,self.meta)
        self.assertEqual(tuple(runs),EXPECTED_RUNS)
        self.assertEqual(len(runs),12)
        self.assertEqual(len(EXPECTED_DONORS),6)

    def test_private_counts_absent_requires_independent_institutional_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            x=Path(temp)/"counts.tsv"
            x.write_text("TEST\n",encoding="utf-8")
            y=Path(temp)/"report.json"
            with self.assertRaises(PermissionError):
                ensure_private_runtime(x,y,False,True,"PROCESSING-REFERENCE-001","RELEASE-REFERENCE-001")
            with self.assertRaises(PermissionError):
                ensure_private_runtime(x,y,True,False,"PROCESSING-REFERENCE-001","RELEASE-REFERENCE-001")
            self.assertFalse(y.exists())

    def test_forbid_ci_even_with_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            x=Path(temp)/"counts.tsv"
            x.write_text("TEST\n")
            with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}):
                with self.assertRaisesRegex(PermissionError,"Never run controlled"):
                    ensure_private_runtime(x,Path(temp)/"report.json",True,True,
                                          "PROCESSING-REFERENCE-001","RELEASE-REFERENCE-001")

    def test_forbid_counts_or_report_inside_repo(self):
        with tempfile.TemporaryDirectory() as temp:
            x=Path(temp)/"counts.tsv"
            x.write_text("TEST\n")
            with self.assertRaisesRegex(PermissionError,"output may not be written"):
                ensure_private_runtime(x,ROOT/"reports/factory/private_summary.json",True,True,
                                       "PROCESSING-REFERENCE-001","RELEASE-REFERENCE-001")
            with self.assertRaisesRegex(PermissionError,"input may not be stored"):
                ensure_private_runtime(ROOT/"private_counts.tsv",Path(temp)/"summary.json",True,True,
                                       "PROCESSING-REFERENCE-001","RELEASE-REFERENCE-001")

    def test_aggregate_no_donor_or_RNA_leak_and_no_extrapolated_intercept(self):
        report=release_safe_aggregate(self.synthetic_internal())
        encoded=json.dumps(report)
        for key in ("pairs","donor_genotype","rna_runs","SECRET","190","216","218","286","287","288"):
            self.assertNotIn('"'+key+'"',encoded)
        self.assertNotIn("identity_constant_intercept_age_delta",encoded)
        self.assertEqual(report["statistics"]["donor_pairs"],6)
        self.assertEqual(report["causal_fate_independent_rejuvenation"],"UNVERIFIED")

    def test_extrapolating_result_cannot_be_treated_as_established_rejuvenation(self):
        report=release_safe_aggregate(self.synthetic_internal())
        self.assertFalse(report["statistics"]["zero_identity_change_within_observed_support"])
        self.assertEqual(report["statistics"]["identity_constant_effect_interpretation"],
                         "UNVERIFIED_EXTRAPOLATED_OUTSIDE_IDENTITY_SUPPORT")

    def test_incomplete_donors_and_nonfinite_outputs_rejected(self):
        input_=self.synthetic_internal()
        input_["donor_pairs"]=5
        with self.assertRaisesRegex(ValueError,"six complete"):
            release_safe_aggregate(input_)
        input_=self.synthetic_internal()
        input_["observed_mean_identity_delta"]=float("nan")
        with self.assertRaisesRegex(ValueError,"Nonfinite"):
            release_safe_aggregate(input_)

    def test_public_metadata_mutation_rejected(self):
        fake=json.loads(json.dumps(self.meta))
        for record in fake["rna_samples"]:
            if record["rna_run"]=="SRR34149245":
                record["rna_run"]="SRR_UNKNOWN"
                break
        with self.assertRaises(ValueError):
            condition_and_run_gate(self.meth,fake)

if __name__=="__main__":
    unittest.main()
