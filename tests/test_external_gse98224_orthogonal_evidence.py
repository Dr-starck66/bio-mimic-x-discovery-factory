"""Strict persistable evidence: real 48 RNA+DNAm, not a rejuvenation claim."""
import json
import math
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"reports/factory/GSE98224-EXTERNAL-REAL-48-RNA-DNAM-VALIDATION-2026-11-02.json"
class PublicPairedHumanRNAAndDNAmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=json.loads(PATH.read_text(encoding="utf8"))
    def test_forty_eight_real_unique_exact_gsm(self):
        data=self.a["data"]
        self.assertEqual(data["RNA_feature_count"],22188)
        self.assertEqual(data["DNA_beta_CpG_feature_count"],18626)
        self.assertTrue(data["all_48_same_GSM_columns"])
        self.assertFalse(data["same_physical_aliquot_verified"])
        self.assertEqual(data["distinct_GSM_exact_matched_RNA_and_DNAm"],48)
        self.assertEqual(len(data["sample_accessions"]),48)
        self.assertEqual(len(set(data["sample_accessions"])),48)
        self.assertTrue(all(s.startswith("GSM1940") for s in data["sample_accessions"]))
        self.assertEqual(data["clinical_groups"],{"control":18,"preeclampsia":30})
    def test_independently_measured_two_modalities_pinned(self):
        data=self.a["data"]
        self.assertIn("Affymetrix",data["RNA_assay"])
        self.assertIn("Illumina",data["DNA_assay"])
        for digest in data["source_sha256"].values():
            self.assertEqual(len(digest),64)
            self.assertTrue(all(c in "0123456789abcdef" for c in digest))
        a=self.a["actual_executed_analysis"]
        self.assertEqual(a["status"],"PASS_REAL_PUBLIC_PAIRED_RNA_DNAM_ASSOCIATION_ONLY")
        self.assertEqual(a["n_measured_RNA_marker_genes"],10)
    def test_actual_orthogonal_correction_and_negative_outcome(self):
        a=self.a["actual_executed_analysis"]
        self.assertAlmostEqual(a["gestational_week_beta_before"],.00214610459901788)
        self.assertAlmostEqual(a["gestational_week_beta_after_RNA_identity_adjustment"],.00217110614773065)
        self.assertGreater(a["gestational_week_beta_after_RNA_identity_adjustment"],a["gestational_week_beta_before"])
        self.assertTrue(math.isfinite(a["residual_sd_after"]))
        self.assertEqual(a["mechanistic_aging_reversal"],"UNVERIFIED_NOT_A_REPROGRAMMING_STUDY")
        self.assertEqual(self.a["secondary_aging_study"]["matching_conditions_status"],"NOT_YET_VERIFIED")
        self.assertEqual(self.a["reprogramming_study_negative_transport"]["RNA_full_download_after_125k_bytes_HTTP403"],"FAIL_TRANSPORT")
        self.assertFalse(self.a["secondary_aging_study"]["actual_two_assay_raw_values_downloaded"])
    def test_source_artifact_sha256_pinned_and_zero_cost(self):
        a=self.a["audit"]
        self.assertEqual(a["cost_additional_eur"],0)
        self.assertTrue(all(len(v)==64 for v in a["artifact_output_sha256"].values()))
        self.assertIn("41418839761",a["GitHub_actions_job"])
if __name__=="__main__":unittest.main()
