import unittest
from epistemic import *

class Tests(unittest.TestCase):
    def setUp(self):
        self.m=catalog(True);self.t={'F':(1,0,0,0),'B':(0,1,0,0)}
    def rows(self,*keys):return [self.m[k].row for k in keys]
    def test_exact_kernel(self):
        a=self.rows('passive','reference','reference_zero','reverse','witness')
        z=knowledge(a,self.t);self.assertEqual(z['rank'],3)
        self.assertEqual(z['targets']['F']['counterexample'],['-1','0','0','1'])
        self.assertTrue(z['targets']['B']['identifiable'])
    def test_duplicate(self):
        a=self.rows('passive');self.assertEqual(knowledge(a,self.t),knowledge(a*100,self.t))
    def test_empty_knowledge(self):self.assertEqual(knowledge([],self.t)['rank'],0)
    def test_linear_combination(self):
        self.assertTrue(knowledge(self.rows('passive'),{'sum':(1,1,0,1)})['targets']['sum']['identifiable'])
    def test_fraction(self):
        z=nullspace([(2,3)],2)[0];self.assertEqual(z,(Q(-3,2),Q(1)))
    def test_bad_shape(self):
        with self.assertRaises(ValueError):knowledge([(1,2)],self.t)
    def test_ordinary_partial(self):
        p=plan(['passive'],self.m,self.t,('motion','external','witness'),100)
        self.assertEqual(p['status'],'partial');self.assertFalse(p['knowledge']['targets']['F']['identifiable'])
    def test_permission(self):
        p=plan(['passive'],self.m,self.t,(),100);self.assertEqual(p['actions'],[])
    def test_budget(self):
        a=('motion','external','witness','isolated');p=plan(['passive'],self.m,self.t,a,5);self.assertEqual(p['status'],'partial')
        p=plan(['passive'],self.m,self.t,a,6);self.assertEqual(p['actions'],['primary_zero','isolated_force']);self.assertEqual(p['cost'],6)
    def test_unbounded(self):self.assertEqual(bounds(self.rows('passive'),[.3],[.01],self.t)['intervals'],{'F':[None,None],'B':[None,None]})
    def test_inconsistent(self):self.assertEqual(bounds(self.rows('passive','passive'),[0.,1.],[.01,.01],self.t)['status'],'inconsistent')
    def test_precision(self):
        a=self.rows('isolated_force');t={'F':self.t['F']}
        self.assertEqual(assess(bounds(a,[.07],[.02],t)['intervals']['F']),'uncertain')
        self.assertEqual(assess(bounds(a,[.07],[.005],t)['intervals']['F']),'present')
    def test_no_false_absence(self):self.assertEqual(assess([-.1,.1]),'uncertain')
    def test_invalid_radius(self):
        with self.assertRaises(ValueError):bounds(self.rows('passive'),[.3],[-.1],self.t)
    def test_conditional_assumption_failure(self):
        a=self.rows('passive','primary_zero','isolated_force');r=bounds(a,[.24,0,.24],[.01]*3,self.t)
        # True force can be zero if the supposedly isolated channel shares the artifact.
        self.assertEqual(assess(r['intervals']['F']),'present')
        self.assertFalse(knowledge([self.m['passive'].row,self.m['primary_zero'].row,self.m['witness'].row],self.t)['targets']['F']['identifiable'])
if __name__=='__main__':unittest.main()
