"""Do not confuse open peer-reviewed DEG tallies with controlled donor-linked RNA counts."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"reports/factory/GSE295849-OPEN-CCBY-RNA-SUMMARY-2026-11-02.json"

class PublishedRNASummaryEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(PATH.read_text(encoding="utf-8"))
    def test_six_real_published_RNA_DEG_aggregate_numbers(self):
        d=self.data["derived_published_summary"]
        self.assertEqual([x["differentially_expressed_genes"] for x in d["fate_progression_DGE"]],[6270,5978,2267])
        self.assertEqual([x["differentially_expressed_genes"] for x in d["donor_age_group_DGE"]],[1871,20,12])
        self.assertEqual(self.data["publication"]["doi"],"10.1111/acel.70751")
        self.assertEqual(self.data["publication"]["figure"],"Figure 3D and 3E; Results §3.4 and Methods §2.2.2")

    def test_license_is_for_published_aggregates_not_individual_counts(self):
        self.assertEqual(self.data["public_reuse"]["article_license"],
                         "Creative Commons Attribution 4.0 International (CC BY 4.0)")
        self.assertTrue(self.data["transparent_access_receipt"]["published_licensed_aggregate_available"])
        self.assertFalse(self.data["transparent_access_receipt"]["subject_level_RNA_gene_counts_available"])
        self.assertEqual(self.data["transparent_access_receipt"]["subject_level_RNA_gene_counts_access"],"CONTROLLED_DBGAP")

    def test_no_false_mechanistic_claim_or_author_approval(self):
        d=self.data
        self.assertFalse(d["match_to_existing_work"]["ability_to_compute_donor_level_identity_residual"])
        self.assertFalse(d["match_to_existing_work"]["ability_to_compute_age_after_independently_measured_RNA_identity_adjustment"])
        self.assertEqual(d["match_to_existing_work"]["RNA_identity_adjusted_effect_status"],"UNVERIFIED")
        self.assertFalse(d["transparent_access_receipt"]["external_author_permission_or_released_matrix_granted"])
        self.assertFalse(d["transparent_access_receipt"]["authorized_access_granted"])
        self.assertFalse(d["transparent_access_receipt"]["request_approval_or_reply_received"])

    def test_degs_are_not_mislabelled_as_gene_counts(self):
        self.assertTrue(self.data["derived_published_summary"]["count_type"].startswith(
            "COUNT_OF_DIFFERENTIALLY_EXPRESSED_GENES"))
        self.assertNotIn("raw_counts",self.data)
        self.assertEqual(self.data["transparent_access_receipt"]["status"],"PARTIAL_FOR_REQUIRED_MECHANISTIC_TEST")

if __name__=="__main__":unittest.main()
