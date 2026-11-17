import csv,gzip,hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'validation'))
from astra_dino_external_locked import GateError, LOCK, sha,check_crosswalk, assess,build_external_predictors,ridge_predictor,deterministic_pca

class ExternalLocked(unittest.TestCase):
 def setUp(self):
  self.n=30
  self.samples=[f'X_{i:04d}' for i in range(self.n)]
  self.rows=[{'sample_id':s,'specimen_id':f'BIRD{i:05d}','species':'Geospiza fortis',
              'validation_cluster':f'year_{i//6}', 'beak_length':'10', 'beak_height':'5','beak_width':'3'}
             for i,s in enumerate(self.samples)]
  self.model={'training_sample_id_hashes':[sha(b'OSLO_1')],
              'training_specimen_id_hashes':[sha(b'810001')]}
 def test_freeze_protocol_immutable(self):
  self.assertEqual(LOCK['genotype_pcs_per_block'],2)
  self.assertEqual(LOCK['permutation_count'],20000)
  self.assertEqual(LOCK['ridge_lambda'],10)
 def test_join_pass_synthetic(self):
  a,c,y=check_crosswalk(self.rows,self.samples,self.model)
  self.assertEqual((len(a),len(set(c)),y.shape),(30,5,(30,2)))
 def test_no_fake_independent(self):
  with self.assertRaisesRegex(GateError,'EXTERNAL_N_TOO_SMALL'):
   check_crosswalk(self.rows[:29],self.samples,self.model)
 def test_reject_duplicate_sample(self):
  self.rows[1]['sample_id']=self.rows[0]['sample_id']
  with self.assertRaisesRegex(GateError,'DUPLICATE_OR_EMPTY_IDS'):
   check_crosswalk(self.rows,self.samples,self.model)
 def test_reject_duplicate_specimen(self):
  self.rows[1]['specimen_id']=self.rows[0]['specimen_id']
  with self.assertRaisesRegex(GateError,'DUPLICATE_OR_EMPTY_SPECIMEN_IDS'):
   check_crosswalk(self.rows,self.samples,self.model)
 def test_reject_oslo_sample(self):
  self.rows[0]['sample_id']='OSLO_1'
  with self.assertRaisesRegex(GateError,'OSLO_SAMPLE_LEAKAGE'):
   check_crosswalk(self.rows,self.samples+['OSLO_1'],self.model)
 def test_reject_oslo_specimen(self):
  self.rows[0]['specimen_id']='810001'
  with self.assertRaisesRegex(GateError,'OSLO_SPECIMEN_LEAKAGE'):
   check_crosswalk(self.rows,self.samples,self.model)
 def test_reject_unmatched_subjects(self):
  self.rows[0]['sample_id']='different_subject'
  with self.assertRaisesRegex(GateError,'GENOTYPE_PHENOTYPE_ID_NOT_MATCHED'):
   check_crosswalk(self.rows,self.samples,self.model)
 def test_reject_museum_cohort(self):
  for r in self.rows:r['validation_cluster']='museum'
  with self.assertRaisesRegex(GateError,'INSUFFICIENT_INDEPENDENT_CLUSTERS'):
   check_crosswalk(self.rows,self.samples,self.model)
 def test_reject_nonphysical_measurements(self):
  self.rows[1]['beak_height']='0'
  with self.assertRaisesRegex(GateError,'INVALID_PHENOTYPE'):
   check_crosswalk(self.rows,self.samples,self.model)
 def test_ridge_exact_zero_on_mean(self):
  x=np.zeros((30,4));y=np.repeat([[2.,3.]],30,axis=0)
  a,b=ridge_predictor(x,y)
  self.assertTrue(np.allclose(a,[2.,3.]))
  self.assertTrue(np.allclose(b,0))
 def test_pca_independent_of_phenotype(self):
  rng=np.random.default_rng(8);m=rng.normal(size=(30,5));mean,std,load,Z=deterministic_pca(m)
  self.assertEqual(Z.shape,(30,2))
  self.assertTrue(np.allclose((m-mean)/std@load,Z))
  self.assertTrue(all(load[np.argmax(np.abs(load[:,i])),i]>0 for i in (0,1)))
 def test_evaluation_positive_synthetic(self):
  rng=np.random.default_rng(15)
  X=rng.normal(size=self.n)
  y=np.column_stack((X,X*0.5+ rng.normal(scale=.04,size=self.n)))
  P={'HMGA2':np.zeros((self.n,2)),'ALX1':np.zeros((self.n,2)),'JOINT_HMGA2_ALX1':y.copy()}
  out=assess([r['validation_cluster'] for r in self.rows],y,P,{'test':'synthetic'},np.array([0.,0.]),nperm=1000)
  self.assertEqual(out['status'],'PASS_EXTERNAL_EXECUTION__SUCCESS')
  self.assertLessEqual(out['models'][2]['size_p_raw'],.05)
  self.assertGreater(out['models'][2]['size_mse_gain'],.99)
 def test_evaluation_rejects_false_improvement(self):
  rng=np.random.default_rng(16)
  Y=rng.normal(size=(self.n,2))
  P={'HMGA2':-Y,'ALX1':-Y,'JOINT_HMGA2_ALX1':-Y}
  out=assess([r['validation_cluster'] for r in self.rows],Y,P,{'test':'synthetic'},np.array([0.,0.]),nperm=1000)
  self.assertFalse(out['primary_hypothesis_confirmed'])
  self.assertLess(out['models'][2]['size_mse_gain'],0)
 def test_insufficient_permutations(self):
  with self.assertRaisesRegex(GateError,'INSUFFICIENT_PERMUTATION_COUNT'):
   assess([r['validation_cluster'] for r in self.rows],np.ones((self.n,2)),{'JOINT_HMGA2_ALX1':np.ones((self.n,2))}, {},np.array([0,0]),nperm=99)
 def test_external_vcf_strict_source_manifest(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t)
   model={'components':{'HMGA2':{'markers':[]},'ALX1':{'markers':[]}}}
   (t/'m.json').write_text(json.dumps(model))
   (t/'src.json').write_text(json.dumps({'assembly':'incorrect','dataset_doi':'10.11/fake','sample_level_genotype_phenotype_join_verified':True}))
   (t/'p.tsv').write_text('sample_id\n')
   with self.assertRaisesRegex(GateError,'ASSEMBLY_MISMATCH'):
    build_external_predictors(t/'x.vcf',t/'p.tsv',t/'m.json',t/'src.json')
 def test_source_crosswalk_flag_required(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);(t/'m.json').write_text('{}')
   (t/'s.json').write_text(json.dumps({'assembly':'GCA_902806625.1','dataset_doi':'10.11/mock','source_url':'https://example.org','id_crosswalk_evidence_url':'https://example.org/file'}))
   with self.assertRaisesRegex(GateError,'EXTERNAL_CROSSWALK_UNVERIFIED'):
    build_external_predictors(t/'x',t/'y',t/'m.json',t/'s.json')
if __name__=='__main__':unittest.main()
