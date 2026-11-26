import unittest
from axiom import *
from benchmark_axiom import case
class TestAxiom(unittest.TestCase):
    def setUp(self):self.obs={'passive':(.24,.01),'reference':(.24,.01),'reference_zero':(0,.01),'primary_zero':(0,.01),'isolated':(.24,.01),'late':(.24,.01)}
    def test_worlds(self):self.assertEqual(len(WORLDS),8);self.assertEqual(FULL.free,('C','D','T'))
    def test_false_strict(self):self.assertEqual(audit(self.obs,worlds=(WORLDS[0],))['targets']['force']['label'],'present');self.assertEqual(audit(self.obs)['targets']['force']['label'],'non_identifiable')
    def test_counterexample(self):
        r=solve(FULL,self.obs,TARGETS['force']);from fractions import Fraction
        z=list(map(Fraction,r['counterexample']));self.assertNotEqual(z[0],0);self.assertTrue(all(sum(a*b for a,b in zip(CATALOG[k].row,z))==0 for k in self.obs))
    def test_artifacts_refuted(self):
        r=audit({**self.obs,'artifact_check':(.24,.01),'isolation_check':(.24,.01)});self.assertEqual(r['targets']['force']['label'],'absent');self.assertEqual(r['assumptions'],{'C':'refuted','D':'refuted','T':'not_established'})
    def test_zero_not_proven(self):self.assertEqual(audit({**self.obs,'artifact_check':(0,.01),'isolation_check':(0,.01)})['assumptions']['C'],'not_established')
    def test_all_refuted(self):self.assertEqual(audit({**self.obs,'artifact_check':(0,.01),'isolation_check':(.5,.01)})['status'],'all_refuted')
    def test_plan(self):self.assertEqual(recommend(self.obs,('isolation_check','artifact_check'),2)['actions'],['isolation_check'])
    def test_unavailable(self):self.assertEqual(recommend(self.obs,(),100)['status'],'partial')
    def test_challenge(self):self.assertEqual(challenge(self.obs,('isolation_check',),2)['checks']['D']['plan']['actions'],['isolation_check'])
    def test_overlap_nested(self):self.assertFalse(any(prediction_overlap(self.obs,'isolation_check')['guaranteed_separation'].values()))
    def test_bad_radius(self):
        with self.assertRaises(ValueError):audit({'passive':(0,-1)})
    def test_near_threshold(self):self.assertEqual(case('near_threshold',65000)['after'],'uncertain')
    def test_outside_model(self):self.assertEqual(case('outside_model',65000)['after'],'all_refuted')
    def test_joint_violation(self):self.assertEqual(case('both_artifacts',65000)['after'],'absent')
    def test_unmodelled_coherent_negative(self):
        r=case('unmodelled_coherent',65000);self.assertEqual(r['truth'],'absent');self.assertEqual(r['after'],'present');self.assertFalse(r['covered'])
if __name__=='__main__':unittest.main()
