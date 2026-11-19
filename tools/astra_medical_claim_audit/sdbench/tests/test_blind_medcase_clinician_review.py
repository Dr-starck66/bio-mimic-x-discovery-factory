#!/usr/bin/env python3
import unittest
import copy
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from blind_medcase_clinician_review import prepare,digest

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.cases={
            3:{"pmcid":"PMC111","case_prompt":"A synthetic vignette describing cough and fever.","final_diagnosis":"Asthma"},
            5:{"pmcid":"PMC222","case_prompt":"A synthetic vignette describing palpitations.","final_diagnosis":"Arrhythmia"}
        }
        self.pred=[]
        for i in self.cases:
            for m,p in [("direct","DIAG A"),("evidence_gated_prompt","ABSTAIN")]:
                self.pred.append({"test_row_index":i,"mode":m,
                                  "case_prompt_sha256":digest(self.cases[i]["case_prompt"]),
                                  "prediction":p})
    def test_shape(self):
        a,b,key=prepare(self.cases,self.pred)
        self.assertEqual((len(a),len(b),len(key)),(2,2,2))
    def test_stage1_hides_reference_and_models(self):
        a,_,_=prepare(self.cases,self.pred)
        self.assertNotIn("reference_diagnosis",a[0])
        self.assertNotIn("candidate_A",a[0])
        self.assertNotIn("mode",str(a))
        self.assertIn("case_presentation",a[0])
    def test_stage2_hides_arm_identity(self):
        _,b,_=prepare(self.cases,self.pred)
        self.assertNotIn("direct",str(b))
        self.assertNotIn("evidence_gated_prompt",str(b))
        self.assertEqual({b[0]["candidate_A"],b[0]["candidate_B"]},{"DIAG A","ABSTAIN"})
    def test_stage2_reference(self):
        _,b,_=prepare(self.cases,self.pred)
        self.assertEqual(b[0]["reference_diagnosis"],"Asthma")
    def test_unblind_key_preserves_identity(self):
        _,b,key=prepare(self.cases,self.pred)
        self.assertEqual(len(set(key[0][k] for k in ("candidate_A_mode","candidate_B_mode"))),2)
    def test_determinism(self):
        self.assertEqual(prepare(self.cases,self.pred),prepare(self.cases,self.pred))
    def test_order_independent_of_input_row_order(self):
        self.assertEqual(prepare(self.cases,self.pred),prepare(self.cases,list(reversed(self.pred))))
    def test_missing_prediction_fails(self):
        with self.assertRaises(ValueError):prepare(self.cases,self.pred[:-1])
    def test_duplicate_prediction_fails(self):
        with self.assertRaises(ValueError):prepare(self.cases,self.pred+[self.pred[0]])
    def test_wrong_hash_fails(self):
        p=copy.deepcopy(self.pred)
        p[0]["case_prompt_sha256"]="bad"
        with self.assertRaises(ValueError):prepare(self.cases,p)
    def test_wrong_mode_fails(self):
        p=copy.deepcopy(self.pred)
        p[0]["mode"]="falsified_model"
        with self.assertRaises(ValueError):prepare(self.cases,p)
    def test_extra_case_fails(self):
        p=copy.deepcopy(self.pred);p[0]["test_row_index"]=99
        with self.assertRaises(ValueError):prepare(self.cases,p)
    def test_empty_data_fails(self):
        with self.assertRaises(ValueError):prepare({},[])
    def test_missing_reference_fails(self):
        x=copy.deepcopy(self.cases)
        x[3]["final_diagnosis"]=""
        with self.assertRaises(ValueError):prepare(x,self.pred)
if __name__=="__main__":unittest.main(verbosity=2)
