import unittest, math
from sensor_guard import quorum, Guard, AnchoredGuard
class Tests(unittest.TestCase):
    def test_quorum(self):
        self.assertAlmostEqual(quorum([.01,.02,10],.05),.015)
        self.assertIsNone(quorum([0,.04,.08],.05))
        self.assertIsNone(quorum([math.nan,math.inf,1],.05))
    def test_recovery(self):
        g=Guard(0.)
        self.assertEqual(g.step([1,1,0],[0]*3,1)[1],'fallback')
        for _ in range(4):self.assertEqual(g.step([0]*3,[0]*3,1)[1],'fallback')
        self.assertEqual(g.step([0]*3,[0]*3,1)[1],'normal')
    def test_velocity_loss_latched(self):
        g=Guard(0.);self.assertEqual(g.step([0]*3,[math.nan]*3,1),(0.,'fallback'))
        for _ in range(20):self.assertEqual(g.step([0]*3,[0]*3,1)[1],'fallback')
    def test_anchor(self):
        g=AnchoredGuard(0.)
        for i in range(5):u,s=g.step([0]*3,[0]*3,1,0. if i==0 else None)
        self.assertEqual(s,'normal')
        self.assertEqual(g.step([0]*3,[0]*3,1,1.),(0.,'fallback'))
    def test_stale_anchor(self):
        g=AnchoredGuard(0.)
        g.step([0]*3,[0]*3,1,0.)
        for _ in range(20):u,s=g.step([0]*3,[0]*3,1)
        self.assertEqual((u,s),(0.,'fallback'))
if __name__=='__main__':unittest.main()
