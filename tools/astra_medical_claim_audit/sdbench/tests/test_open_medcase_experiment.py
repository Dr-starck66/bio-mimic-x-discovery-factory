#!/usr/bin/env python3
"""Offline controls for public-case evaluation and conservative interpretation."""
import unittest
import sys
import random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import open_medcase_qwen05b_experiment as m

class MedCaseEvaluationControls(unittest.TestCase):
    def test_pinned_official_test_partition(self):
        self.assertEqual((m.DATASET,m.SPLIT,m.EXPECTED),("zou-lab/MedCaseReasoning","test",897))
    def test_fixed_selection(self):
        self.assertEqual(sorted(random.Random(m.SEED).sample(range(m.EXPECTED),m.N)),
                         sorted(random.Random(m.SEED).sample(range(m.EXPECTED),m.N)))
    def test_selection_unique(self):
        self.assertEqual(len(set(random.Random(m.SEED).sample(range(m.EXPECTED),m.N))),m.N)
    def test_exact_case_insensitive(self):
        self.assertEqual(m.normalize("Primary Aldosteronism"),m.normalize("primary aldosteronism!"))
    def test_conservative_no_synonym_inference(self):
        self.assertNotEqual(m.normalize("MI"),m.normalize("myocardial infarction"))
    def test_guard_requires_literal_abstention(self):
        self.assertEqual(m.ABSTAIN,"ABSTAIN")
    def test_guard_prompt_defines_abstention(self):
        self.assertIn("ABSTAIN",m.PROMPTS["evidence_gated_prompt"])
    def test_no_treatment_prompt(self):
        self.assertIn("No rationale",m.PROMPTS["direct"])
    def test_wilson_bounds_all_success(self):
        low,upper=m.wilson95(10,10);self.assertLess(low,1);self.assertEqual(upper,1)
    def test_wilson_bounds_no_success(self):
        low,upper=m.wilson95(0,10);self.assertEqual(low,0);self.assertGreater(upper,0)
    def test_wilson_n_zero(self):
        self.assertEqual(m.wilson95(0,0),[0.0,1.0])
    def test_source_is_public_test_only(self):
        self.assertNotIn("mimic",m.DATASET.lower())
    def test_model_is_local_qwen(self):
        self.assertTrue(m.MODEL_ID.endswith(":q4_k_m"))
    def test_parse_prompt_no_reference_names(self):
        for s in m.PROMPTS.values():
            self.assertNotIn("final_diagnosis",s)
    def test_invalid_sample_rejected_before_fetch(self):
        with self.assertRaises(AssertionError):m.run("/nonexistent",Path("."),n=1)
if __name__=="__main__":unittest.main(verbosity=2)
