import unittest
from dataclasses import replace
import numpy as np
from discovery import *
from benchmark_discovery import GRID,P,Experiment,run

class TestDiscovery(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(42);x,v,u=rng.uniform(-.3,.3,(3,300));self.c=np.array([0,1,-1,-.4,0,-8,0,0,1.2]);self.data=np.column_stack([x,v,u,features(x,v,u)@self.c]);self.models=fit(self.data)
    def test_sparse_recovery(self):
        self.assertEqual(self.models[0].support,(1,2,3,5,8));np.testing.assert_allclose(self.models[0].coefficients,self.c,atol=1e-8)
    def test_bad_data(self):
        for bad in [self.data[:5],self.data[:,:3],np.full((40,4),np.nan)]:
            with self.assertRaises(ValueError):fit(bad)
    def test_denial(self):
        for p in (replace(P,authorized=False),replace(P,isolated=False),replace(P,age=.2),replace(P,clearance=.01)):
            self.assertEqual(choose(self.models,GRID,p),(None,{}))
    def test_invalid_experiment(self):
        for e in [Experiment(0,0,.7,'balanced'),Experiment(0,.1,.3,'balanced'),Experiment(float('nan'),0,.3,'balanced'),Experiment(0,0,.3,'bad')]:self.assertFalse(e.authorized(P))
    def test_max_disagreement(self):
        selected,scores=choose(self.models,GRID,P);self.assertEqual(selected,max(scores,key=scores.get))
        predictions=np.array([rollout(m,selected) for m in self.models[:8]])
        self.assertAlmostEqual(scores[selected],float(np.mean(np.var(predictions,axis=0))),places=10)
    def test_falsification(self):
        self.assertTrue(audit(self.models[0],self.data)['accepted']);bad=self.data.copy();bad[:,3]+=.3
        self.assertFalse(audit(self.models[0],bad)['accepted'])
    def test_no_candidate(self):self.assertEqual(choose(self.models[:1],GRID,P),(None,{}))
    def test_paired_case(self):
        r=run('mixed',5000);self.assertTrue(r['modes']['active']['support_exact']);self.assertTrue(r['modes']['active']['test_accepted']);self.assertEqual(len(r['modes']['active']['chosen']),2)
if __name__=='__main__':unittest.main()
