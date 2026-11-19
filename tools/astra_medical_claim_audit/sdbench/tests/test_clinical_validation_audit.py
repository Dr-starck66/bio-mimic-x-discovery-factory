import json
import pathlib
import tempfile
import unittest
from clinical_validation_audit import AuditError, audit, exact_mcnemar, wilson95

PROVENANCE={
 "dataset_id":"mimic-iv-ext-sdbench/1.0.0","case_set":"test",
 "gatekeeper_mode":"original_model","judge_mode":"original_model",
 "data_use_authorized":True,"reference_labels_sealed_before_run":True,
 "patient_level_leakage_screened":True,"model_identifier":"test-fixture",
 "model_sha256":"test-fixture-sha","sdbench_commit":"test-fixture-commit",
 "evaluation_date":"2026-11-19","evaluator_record":"test-fixture record",
 "surrogate_roles_used":False,
}

class AuditTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.root=pathlib.Path(self.temp.name)
  self.b=self.root/'baseline';self.a=self.root/'astra'
  (self.b/'json').mkdir(parents=True);(self.a/'json').mkdir(parents=True)
  self.prov=self.root/'manifest.json'
  self.write_provenance()
  for d,vals in [(self.b,[True,True,False,False]),(self.a,[True,False,True,False])]:
   self.write_results(d,vals)
 def tearDown(self):self.temp.cleanup()
 def write_provenance(self,fields=None):
  self.prov.write_text(json.dumps(PROVENANCE if fields is None else fields))
 def write_results(self,d,truths):
  for f in (d/'json').glob('*.json'):f.unlink()
  for i,c in enumerate(truths):
   (d/'json'/f'case_k0_{i}.json').write_text(json.dumps({
    'dataset':'mimic','case_set':'test','case_id':str(i),'k':0,
    'correct':c,'diagnosis_score':5 if c else 1,
    'model_diagnosis':f'fictional-{i}','num_test_rounds':2}))
 def test_valid_pairing(self):
  r=audit(self.b,self.a,self.prov,4)
  self.assertEqual(r['paired']['both_correct'],1)
  self.assertEqual(r['paired']['both_wrong'],1)
  self.assertEqual(r['paired']['astra_only_correct'],1)
  self.assertEqual(r['paired']['baseline_only_correct'],1)
  self.assertEqual(r['paired']['mcnemar_exact_p'],1.0)
  self.assertEqual(r['astra']['score_fraction'],.5)
  self.assertTrue(r['clinical_validity'].startswith('NOT ESTABLISHED'))
 def test_reject_synthetic(self):
  p=self.a/'json'/'case_k0_0.json';d=json.loads(p.read_text());d['dataset']='synthetic';p.write_text(json.dumps(d))
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_train_leak(self):
  p=self.a/'json'/'case_k0_0.json';d=json.loads(p.read_text());d['case_set']='train';p.write_text(json.dumps(d))
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_surrogate_provenance(self):
  z=dict(PROVENANCE,judge_mode='deterministic_surrogate')
  self.write_provenance(z)
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_surrogate_flag(self):
  self.write_provenance(dict(PROVENANCE,surrogate_roles_used=True))
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_unlicensed_data(self):
  self.write_provenance(dict(PROVENANCE,data_use_authorized=False))
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_missing_file(self):
  (self.a/'json'/'case_k0_0.json').unlink()
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_error(self):
  p=self.a/'json'/'case_k0_1.json';d=json.loads(p.read_text());d.pop('diagnosis_score');p.write_text(json.dumps(d))
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_wrong_judge_consistency(self):
  p=self.a/'json'/'case_k0_1.json';d=json.loads(p.read_text());d['diagnosis_score']=5;p.write_text(json.dumps(d))
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_nonpaired(self):
  p=self.a/'json'/'case_k0_0.json';d=json.loads(p.read_text());d['case_id']='wrong';p.write_text(json.dumps(d))
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_duplicate_cases(self):
  p=self.a/'json'/'case_k0_0.json';d=json.loads(p.read_text());d['case_id']='1';p.write_text(json.dumps(d))
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_reject_repeat(self):
  p=self.a/'json'/'case_k0_0.json';d=json.loads(p.read_text());d['k']=1;p.write_text(json.dumps(d))
  with self.assertRaises(AuditError):audit(self.b,self.a,self.prov,4)
 def test_abstention_count(self):
  p=self.a/'json'/'case_k0_1.json';d=json.loads(p.read_text());d['model_diagnosis']='Unable to provide diagnosis';p.write_text(json.dumps(d))
  r=audit(self.b,self.a,self.prov,4)
  self.assertEqual(r['astra']['abstentions'],1)
 def test_confidence_interval(self):
  low,high=wilson95(5,10);self.assertLess(low,.5);self.assertGreater(high,.5)
  self.assertEqual(wilson95(0,0),[0.0,1.0])
 def test_mcnemar(self):
  self.assertEqual(exact_mcnemar(0,0),1.0)
  self.assertAlmostEqual(exact_mcnemar(0,5),.0625)
 def test_no_cases_in_report(self):
  r=audit(self.b,self.a,self.prov,4)
  self.assertNotIn('case_id',json.dumps(r))
  self.assertNotIn('fictional-',json.dumps(r))

if __name__=='__main__':unittest.main(verbosity=2)