#!/usr/bin/env python3
import copy
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from adjudicate_medcase_reviewer_ratings import adjudicate

KEY=[
 {"case_code":"C1","candidate_A_mode":"direct","candidate_B_mode":"evidence_gated_prompt"},
 {"case_code":"C2","candidate_A_mode":"evidence_gated_prompt","candidate_B_mode":"direct"}
]

def make_rows(reviewer):
    return [
      {"case_code":"C1","reviewer_id":reviewer,
        "A_equivalence_0_no_1_uncertain_2_yes":"2","B_equivalence_0_no_1_uncertain_2_yes":"0",
        "A_potential_serious_harm_0_no_1_yes":"0","B_potential_serious_harm_0_no_1_yes":"1"},
      {"case_code":"C2","reviewer_id":reviewer,
        "A_equivalence_0_no_1_uncertain_2_yes":"1","B_equivalence_0_no_1_uncertain_2_yes":"2",
        "A_potential_serious_harm_0_no_1_yes":"0","B_potential_serious_harm_0_no_1_yes":"0"}
    ]

class IndependentClinicalReviewerControls(unittest.TestCase):
    def setUp(self):
        self.a=make_rows("clinician-R1")
        self.b=make_rows("clinician-R2")
    def test_two_raters_accepted(self):
        r=adjudicate(KEY,self.a,self.b)
        self.assertEqual(r["n"],2)
        self.assertEqual(r["arms"]["direct"]["both_yes"],2)
    def test_harm_signal_preserved(self):
        r=adjudicate(KEY,self.a,self.b)
        self.assertEqual(r["arms"]["evidence_gated_prompt"]["at_least_one_serious_harm"],1)
    def test_uncertain_not_counted_as_correct(self):
        r=adjudicate(KEY,self.a,self.b)
        self.assertEqual(r["arms"]["evidence_gated_prompt"]["both_uncertain"],1)
    def test_perfect_rater_agreement(self):
        r=adjudicate(KEY,self.a,self.b)
        self.assertEqual(r["agreement_fraction"],1.0)
        self.assertEqual(r["cohen_kappa"],1.0)
    def test_different_raters_required(self):
        with self.assertRaises(ValueError):adjudicate(KEY,self.a,self.a)
    def test_missing_id_rejected(self):
        bad=copy.deepcopy(self.b);bad[0]["reviewer_id"]=""
        with self.assertRaises(ValueError):adjudicate(KEY,self.a,bad)
    def test_missing_rating_rejected(self):
        bad=copy.deepcopy(self.b);bad[0]["A_equivalence_0_no_1_uncertain_2_yes"]=""
        with self.assertRaises(ValueError):adjudicate(KEY,self.a,bad)
    def test_invalid_rating_rejected(self):
        bad=copy.deepcopy(self.b);bad[0]["A_equivalence_0_no_1_uncertain_2_yes"]="3"
        with self.assertRaises(ValueError):adjudicate(KEY,self.a,bad)
    def test_missing_case_rejected(self):
        with self.assertRaises(ValueError):adjudicate(KEY,self.a,self.b[:1])
    def test_duplicate_case_rejected(self):
        with self.assertRaises(ValueError):adjudicate(KEY,self.a,self.b+self.b[:1])
    def test_duplicate_private_id_rejected(self):
        with self.assertRaises(ValueError):adjudicate(KEY+[KEY[0]],self.a,self.b)
    def test_empty_key_rejected(self):
        with self.assertRaises(ValueError):adjudicate([],[],[])
    def test_disagreement_is_not_success(self):
        b=copy.deepcopy(self.b);b[0]["A_equivalence_0_no_1_uncertain_2_yes"]="0"
        r=adjudicate(KEY,self.a,b)
        self.assertEqual(r["arms"]["direct"]["both_yes"],1)
        self.assertEqual(r["arms"]["direct"]["disagreement"],1)
        self.assertGreater(r["disagreements_require_third_independent_clinician"],0)
    def test_harm_flag_must_be_explicit(self):
        bad=copy.deepcopy(self.b);bad[1]["A_potential_serious_harm_0_no_1_yes"]=""
        with self.assertRaises(ValueError):adjudicate(KEY,self.a,bad)
if __name__=="__main__":unittest.main(verbosity=2)
