import unittest,json
import numpy as np
import scientific_evolution as s
from benchmark_evolution import development,evaluate,digest,ROOT
from metascience import predict
class Tests(unittest.TestCase):
    def setUp(self):
        r=np.random.default_rng(42);self.X=r.normal(size=(100,3));self.y=self.X[:,0]+r.normal(0,.1,100)
    def row(self,**kw):return dict({'task':'a','candidate':.8,'parent':1.,'reference':1.,'lower_parent':.1,'lower_reference':.1},**kw)
    def test_mutation_count(self):self.assertEqual(len(s.mutations()),16);self.assertEqual(len(set(s.mutations())),16)
    def test_parent(self):
        for name,(X,y,t,p) in development().items():
            with self.subTest(name=name):
                orig=predict(X,y,temporal=t);r=s.predict_policy(X,y,t,p,s.PARENT);self.assertEqual(r['method'],orig['selected']);self.assertAlmostEqual(s.rmse(y[r['test_idx']],r['prediction']),orig['test_rmse'][orig['selected']],places=9)
    def test_test_labels_hidden(self):
        for temporal in (False,True):
            for policy in s.mutations():
                r=s.predict_policy(self.X,self.y,temporal,12 if temporal else 0,policy);y=self.y.copy();y[r['test_idx']]+=1000;v=s.predict_policy(self.X,y,temporal,12 if temporal else 0,policy);self.assertEqual(r['method'],v['method']);np.testing.assert_array_equal(r['prediction'],v['prediction'])
    def test_future_features(self):
        X=self.X.copy();X[80:]+=100
        for k,f in s.model_features(self.X,np.arange(60),True,True).items():np.testing.assert_array_equal(f[:80],s.model_features(X,np.arange(60),True,True)[k][:80])
    def test_reject_regression(self):self.assertEqual(s.gate([self.row(),self.row(task='b',candidate=1.01)])['decision'],'REJECT')
    def test_reference_stronger(self):self.assertEqual(s.gate([self.row(reference=.7)])['decision'],'REJECT')
    def test_no_confirmed_gain(self):self.assertEqual(s.gate([self.row(lower_parent=-.01)])['decision'],'REJECT')
    def test_promotion(self):self.assertEqual(s.gate([self.row(),self.row(task='b',candidate=1.,lower_parent=0.,lower_reference=0.)])['decision'],'PROMOTE')
    def test_invalid(self):
        for rows in ([],[self.row(),self.row()],[self.row(candidate=np.nan)],[self.row(reference=0)]):self.assertEqual(s.gate(rows)['decision'],'REJECT')
    def test_identical_bootstrap(self):self.assertEqual(s.lower_gain(self.y,self.X[:,0],self.X[:,0],4,42,.01),0.)
    def test_bootstrap_seed(self):self.assertEqual(s.lower_gain(self.y,self.X[:,1],self.X[:,0],4,42,.01),s.lower_gain(self.y,self.X[:,1],self.X[:,0],4,42,.01))
    def test_lock_tamper(self):
        r=json.loads((ROOT/'frozen.json').read_text());r['lock']['policy']['refit']=not r['lock']['policy']['refit']
        with self.assertRaises(AssertionError):evaluate(r)
    def test_observational_abstention(self):self.assertEqual(s.predict_policy(self.X,self.y,False,0,s.PARENT)['causal_claim'],'abstain_observational')
if __name__=='__main__':unittest.main()
