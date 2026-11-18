import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sequential_diagnosis import (entropy, information_gain, posterior, run_case, run_suite, select_next, validate_case)


def case():
    return {
      "synthetic": True, "case_id": "synthetic-001", "ground_truth": "A",
      "hypotheses": [{"id":"A","prior":0.5},{"id":"B","prior":0.5}],
      "tests": [
        {"id":"uninformative","cost":0, "outcomes":{"A":{"pos":0.5,"neg":0.5},"B":{"pos":0.5,"neg":0.5}}},
        {"id":"marker","cost":1, "outcomes":{"A":{"pos":0.95,"neg":0.05},"B":{"pos":0.05,"neg":0.95}}}
      ], "observations":{"uninformative":"neg","marker":"pos"}}

class SequentialResearchTests(unittest.TestCase):
    def test_validate(self): self.assertEqual(validate_case(case()), {"A":0.5,"B":0.5})
    def test_information_gain(self):
        c=case(); self.assertAlmostEqual(information_gain({"A":0.5,"B":0.5}, c["tests"][0]),0)
        self.assertGreater(information_gain({"A":0.5,"B":0.5}, c["tests"][1]), 0.5)
    def test_select_informative(self):
        c=case(); self.assertEqual(select_next({"A":0.5,"B":0.5},c["tests"])[0]["id"],"marker")
    def test_first_decision(self):
        r=run_case(case()); self.assertEqual(r["outcome"],"SIMULATED_CLASSIFICATION")
        self.assertEqual(r["predicted_label"],"A"); self.assertEqual(r["tests_used"],1)
        self.assertEqual(r["synthetic_cost_units"],1)
    def test_negative_observation_reverses(self):
        c=case(); c["ground_truth"]="B"; c["observations"]["marker"]="neg"
        self.assertEqual(run_case(c)["predicted_label"],"B")
    def test_zero_information_abstain(self):
        c=case(); c["tests"]=c["tests"][:1]; c["observations"]={"uninformative":"neg"}
        self.assertEqual(run_case(c)["outcome"],"ABSTAIN")
    def test_leakage_ground_truth_not_used(self):
        c=case(); other=copy.deepcopy(c); other["ground_truth"]="B"
        self.assertEqual(run_case(c)["predicted_label"],run_case(other)["predicted_label"])
    def test_leakage_observations_not_used_in_test_selection(self):
        c=case(); c2=copy.deepcopy(c); c2["observations"]["marker"]="neg"
        self.assertEqual(run_case(c)["steps"][0]["test_id"],run_case(c2)["steps"][0]["test_id"])
    def test_synthetic_only(self):
        c=case(); c["synthetic"]=False
        with self.assertRaises(ValueError):run_case(c)
    def test_personal_fields_rejected(self):
        for key in ("name","dob","email","patient_id"):
            c=case(); c[key]="Synthetic Subject"
            with self.assertRaises(ValueError):run_case(c)
    def test_bad_priors(self):
        c=case(); c["hypotheses"][0]["prior"]=0.8
        with self.assertRaises(ValueError):run_case(c)
    def test_bad_likelihood(self):
        c=case(); c["tests"][1]["outcomes"]["A"]["pos"]=0.99
        with self.assertRaises(ValueError):run_case(c)
    def test_unknown_observation(self):
        c=case(); c["observations"]["marker"]="invalid"
        with self.assertRaises(ValueError):run_case(c)
    def test_bayesian_posterior(self):
        c=case(); p=posterior({"A":0.5,"B":0.5},c["tests"][1],"pos")
        self.assertAlmostEqual(p["A"],0.95)
    def test_cost_tradeoff(self):
        c=case(); new=copy.deepcopy(c["tests"][1]); new["id"]="expensive"; new["cost"]=100
        c["tests"].append(new);c["observations"]["expensive"]="pos"
        self.assertEqual(run_case(c)["steps"][0]["test_id"],"marker")
    def test_determinism_and_hash(self):
        c=[case()]; self.assertEqual(run_suite(c),run_suite(copy.deepcopy(c)))
    def test_disclaimer(self):
        r=run_suite([case()]); self.assertEqual(r["clinical_validation"],"UNVERIFIED")
    def test_abstention_coverage(self):
        c=case(); c["tests"]=[]; c["observations"]={}
        r=run_suite([c]); self.assertEqual(r["coverage"],0);self.assertIsNone(r["accuracy_among_decided"])
    def test_unreachable_observation_refused_to_classify(self):
        c=case(); c["tests"][1]["outcomes"]={"A":{"pos":0,"neg":1},"B":{"pos":0,"neg":1}}
        # With zero-information marker it is never selected.
        self.assertEqual(run_case(c)["outcome"], "ABSTAIN")

if __name__ == "__main__": unittest.main()