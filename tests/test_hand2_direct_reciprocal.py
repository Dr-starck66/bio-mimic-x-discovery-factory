import copy
import json
import unittest
from pathlib import Path
from validation.hand2_direct_reciprocal import (
  MANIFEST,OLD_BEGIN,OLD_END,MODERN_BEGIN,MODERN_END,
  check_manifest,_validate_bases,score_windows,evaluate
)

class Hand2DirectReciprocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real_observed_manifest=json.loads(MANIFEST.read_text())
    def test_real_manifest_pins_exact_source_and_candidate(self):
        self.assertTrue(check_manifest(self.real_observed_manifest))
        self.assertEqual(OLD_END-OLD_BEGIN+1,4341)
        self.assertEqual(MODERN_END-MODERN_BEGIN+1,4212)
    def test_falsified_coordinate_is_rejected(self):
        m=copy.deepcopy(self.real_observed_manifest)
        m["candidate"]["start_1based"]+=1
        with self.assertRaises(ValueError):check_manifest(m)
    def test_wrong_gene_or_control_is_rejected(self):
        m=copy.deepcopy(self.real_observed_manifest)
        m["candidate"]["id"]="AMEX60DD030069"
        with self.assertRaises(ValueError):check_manifest(m)
        m=copy.deepcopy(self.real_observed_manifest)
        m["negative_control"]["gene_id"]="138516365"
        with self.assertRaises(ValueError):check_manifest(m)
    def test_missing_reproducible_source_evidence_fails(self):
        m=copy.deepcopy(self.real_observed_manifest)
        m["gtf_sha256"]="00"
        with self.assertRaises(ValueError):check_manifest(m)
        m=copy.deepcopy(self.real_observed_manifest)
        m["observed_artifact_id"]=123
        with self.assertRaises(ValueError):check_manifest(m)
    def test_invalid_bases_or_mismatched_genomic_lengths_fails(self):
        with self.assertRaises(ValueError):_validate_bases("ACBX",4,"old")
        with self.assertRaises(ValueError):_validate_bases("ACGT",5,"old")
        self.assertEqual(len(_validate_bases("ACGT",4,"old")),64)
    def test_network_unavailable_is_explicit_not_pass(self):
        def unavailable(*args):raise OSError("test NCBI 500")
        out=evaluate(self.real_observed_manifest,fetcher=unavailable)
        self.assertEqual(out["status"],"UNVERIFIED_SOURCE_FAILURE")
        self.assertEqual(len(out["source_failures"]),3)
        self.assertEqual(out["scientific_identity"],"UNVERIFIED")
    def test_two_way_scores_and_negative_are_separate(self):
        distances=iter([1,1,30,30])
        def mock_align(q,t,ed):
            return {"best":{"edit_distance":next(distances),"strand":"-",
                            "fraction_matching_in_alignment":.98}}
        out=score_windows("A"*45,"A"*40,"A"*50,aligner=mock_align,edlib_module=object())
        self.assertTrue(out["favors_HAND2_over_HAND1_in_tested_windows"])
        self.assertEqual(out["genome_wide_reciprocal_best_hit"],"UNVERIFIED")
        self.assertEqual(out["whole_genome_uniqueness"],"UNVERIFIED")
    def test_favorable_two_way_alignment_does_not_count_as_curator_proof(self):
        distances=iter([0,0,40,40])
        def mock_align(q,t,ed):return {"best":{"edit_distance":next(distances),"strand":"+"}}
        out=score_windows("A"*45,"A"*40,"A"*50,aligner=mock_align,edlib_module=object())
        self.assertTrue(out["favors_HAND2_over_HAND1_in_tested_windows"])
        self.assertEqual(out["independent_curator_confirmation"],"UNVERIFIED")

if __name__=="__main__":unittest.main()
