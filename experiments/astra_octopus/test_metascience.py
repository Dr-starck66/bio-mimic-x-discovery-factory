import unittest
import numpy as np
import metascience as m
from benchmark_meta import run
class Tests(unittest.TestCase):
    def setUp(self):
        r=np.random.default_rng(42); self.X=r.normal(size=(100,3));self.y=self.X[:,0]+r.normal(0,.1,100)
    def test_split_disjoint(self):
        for temporal in (False,True):
            a,b,c=m.split(100,temporal);self.assertEqual(len(set(a)|set(b)|set(c)),100);self.assertFalse(set(a)&set(c));self.assertFalse(set(a)&set(b));self.assertFalse(set(b)&set(c))
    def test_time_order(self):
        a,b,c=m.split(100,True);self.assertLess(max(a),min(b));self.assertLess(max(b),min(c))
    def test_no_fake_history(self):self.assertNotIn('invisible_lags',m.features(self.X,np.arange(60),False))
    def test_future_features(self):
        X=self.X.copy();X[80:]+=100;f=m.features(self.X,np.arange(60),True);g=m.features(X,np.arange(60),True)
        for k in f:np.testing.assert_allclose(f[k][:80],g[k][:80])
    def test_holdout_labels_not_selection(self):
        a=m.predict(self.X,self.y);y=self.y.copy();y[a['test_indices']]+=1000;b=m.predict(self.X,y);self.assertEqual(a['selected'],b['selected']);self.assertEqual(a['validation'],b['validation'])
    def test_validation_training_only(self):
        a=m.predict(self.X,self.y);self.assertEqual(a['causal_claim'],'abstain_observational');self.assertFalse(a['ambiguity']['targets']['causal_effect']['identifiable'])
    def test_bad_input(self):
        with self.assertRaises(ValueError):m.predict(self.X,self.y*float('nan'))
    def test_unknown_protocol(self):
        with self.assertRaises(ValueError):m.route('physical_audit',observations={},protocol='observational')
    def test_unknown_task(self):
        with self.assertRaises(ValueError):m.route('unknown')
    def test_native_integration(self):self.assertEqual(run()['synthetic_integration'],{'causal':'force','axiom':'absent','paradigm':'candidate_extension'})
if __name__=='__main__':unittest.main()
