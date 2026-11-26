import unittest,math
from cross_sense import consensus,CrossSense
class TestCrossSense(unittest.TestCase):
    def test_unique_quorum(self):
        x,k=consensus({'a':(0,.1),'b':(.03,.1),'c':(-.03,.1),'d':(1,.1)},3)
        self.assertAlmostEqual(x,0);self.assertEqual(set(k),{'a','b','c'})
    def test_two_against_two(self):
        self.assertEqual(consensus({'a':(0,.1),'b':(0,.1),'c':(1,.1),'d':(1,.1)},3),(None,()))
    def test_ambiguous_cliques(self):
        self.assertEqual(consensus({'a':(0,.1),'b':(.1,.1),'c':(.2,.1),'d':(.3,.1)},3),(None,()))
    def test_nonfinite(self):
        self.assertEqual(consensus({'a':(0,.1),'b':(float('nan'),.1),'c':(0,.1)},3),(None,()))
    def test_replay_does_not_refresh(self):
        g=CrossSense()
        for k in range(40):g.step((0,0),0,0,(0,0) if k%10==0 else None,1)
        self.assertEqual(g.frame,(0,0))
    def test_double_loss_blocks(self):
        g=CrossSense()
        for k in range(40):u,s,_=g.step((0,0),math.nan,math.nan,(k,0) if k%10==0 else None,1)
        self.assertEqual((u,s),(0.,'fallback'))
    def test_reopen_delay(self):
        g=CrossSense()
        for k in range(4):self.assertEqual(g.step((0,0),0,0,None,1)[1],'fallback')
        self.assertEqual(g.step((0,0),0,0,None,1)[1],'degraded')
if __name__=='__main__':unittest.main()
