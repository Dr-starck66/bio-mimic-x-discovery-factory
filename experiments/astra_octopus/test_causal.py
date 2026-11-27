import unittest
from dataclasses import replace
import numpy as np
from causal import *
from benchmark_causal import P,run
from repeat_audit import repeat_check

def data(names,theta):return {n:np.full(N,np.dot(ACTIONS[n].row,theta)) for n in names}
class Tests(unittest.TestCase):
    def test_passive_equivalence(self):
        self.assertEqual(identifiable(['passive']),(False,False));a=data(['passive'],[.3,0,0]);b=data(['passive'],[0,.3,0]);np.testing.assert_equal(a,b);self.assertEqual(infer(a)['verdict'],'inconclusive')
    def test_reference_unknown_bias(self):self.assertEqual(identifiable(['passive','reference']),(False,False))
    def test_identifiable_not_confirmed(self):
        d=data(['passive','reference','reference_zero'],[.3,.2,.4]);r=infer(d);self.assertEqual(r['identifiable'],[True,True]);self.assertEqual(r['verdict'],'inconclusive')
    def test_both(self):self.assertEqual(infer(data(['passive','primary_zero','reference','reference_zero'],[.3,-.2,.4]))['verdict'],'both')
    def test_force(self):self.assertEqual(infer(data(['passive','primary_zero','reverse'],[-.3,0,.4]))['verdict'],'force')
    def test_bias(self):self.assertEqual(infer(data(['passive','primary_zero','reverse'],[0,.3,.4]))['verdict'],'bias')
    def test_reject_inconsistent(self):
        d=data(['passive','primary_zero','reference','reference_zero'],[.3,.2,.4]);d['primary_zero']+=.3;self.assertEqual(infer(d)['verdict'],'model_rejected')
    def test_boundary_abstains(self):self.assertEqual(infer(data(['passive','primary_zero','reverse'],[.06,0,0]))['verdict'],'inconclusive')
    def test_no_motion(self):
        p=replace(P,authorized=False);self.assertEqual(choose(['passive'],p,True,5),'reference');self.assertFalse(eligible('reverse',p,True));self.assertIsNone(choose(['passive'],p,False,5))
    def test_budget(self):self.assertIsNone(choose(['passive'],P,True,0))
    def test_no_external(self):self.assertEqual(run('no_external',12,'adaptive')['motion'],2)
    def test_invalid(self):self.assertEqual(infer({'passive':np.full(N,np.nan)})['verdict'],'invalid')
    def test_common_mode_counterexample(self):
        r=run('coherent_deception',12,'adaptive');self.assertEqual(r['truth'],'neither');self.assertEqual(r['verdict'],'force')
    def test_repeat(self):
        a=data(['passive','primary_zero','reverse'],[.3,.2,0]);b={k:v.copy() for k,v in a.items()};self.assertTrue(repeat_check(a,b));b['reverse']+=.2;self.assertFalse(repeat_check(a,b))
    def test_repeat_invalid(self):self.assertFalse(repeat_check({'passive':np.zeros(N)},{'passive':np.full(N,np.nan)}))
    def test_no_passive_no_confirmation(self):self.assertEqual(infer(data(['primary_zero','reverse'],[.3,.2,0]))['verdict'],'inconclusive')
    def test_unknown_action(self):self.assertEqual(infer({'unknown':np.zeros(N)})['verdict'],'invalid')
if __name__=='__main__':unittest.main()
