import unittest, math
from dataclasses import replace
from active_doubt import Permit
from hypothesis_engine import *
class Tests(unittest.TestCase):
    def setUp(self):self.permit=Permit(True,True,0.,.18,.015,1.2,.55)
    def test_normalization(self):
        self.assertAlmostEqual(sum(PRIOR.values()),1)
        for e in COST:
            for h in H:self.assertAlmostEqual(sum(likelihood(e,h).values()),1)
    def test_information(self):
        for e in COST:self.assertTrue(0<=information(PRIOR,e)<=entropy(PRIOR.values())+1e-8)
    def test_update(self):
        p=update(PRIOR,'pulse',(0,1,1,1));self.assertAlmostEqual(sum(p.values()),1);self.assertGreater(p['encoder_gain'],.95)
    def test_ambiguity(self):
        p=update(PRIOR,'pulse',(0,0,0,0));self.assertAlmostEqual(p['actuator_low'],p['all_gain']);self.assertLess(max(p.values()),.95)
    def test_external(self):
        p=update(PRIOR,'pulse',(0,0,0,0));p=update(p,'external_pulse',(0,0,0,0,1));self.assertGreater(p['all_gain'],.95)
    def test_denial(self):
        e=Engine();p=replace(self.permit,authorized=False);self.assertEqual(e.choose(p),'static');self.assertFalse(e.begin('pulse',p));self.assertFalse(e.begin('external_pulse',p))
    def test_budget(self):
        e=Engine();self.assertFalse(e.begin('external_pulse',self.permit,budget=3));self.assertIsNone(e.choose(self.permit,budget=0))
    def test_no_external(self):
        e=Engine();self.assertFalse(e.begin('static',self.permit,False));self.assertFalse(e.begin('external_pulse',self.permit,False));self.assertEqual(e.choose(self.permit,False),'pulse')
    def test_replay_and_pending(self):
        e=Engine();self.assertTrue(e.begin('pulse',self.permit));self.assertIsNone(e.choose(self.permit));self.assertFalse(e.begin('static',self.permit));self.assertTrue(e.observe('pulse',(0,1,1,1)));self.assertFalse(e.observe('pulse',(0,1,1,1)));self.assertEqual(e.verdict(),'inconclusive')
    def test_missing(self):
        e=Engine();e.begin('pulse',self.permit);self.assertFalse(e.observe('pulse',None));self.assertEqual(e.verdict(),'inconclusive');self.assertIsNone(e.choose(self.permit))
    def test_unknown(self):
        e=Engine();e.begin('pulse',self.permit);e.observe('pulse',(2,1,1,1));self.assertEqual(e.verdict(),'inconclusive')
if __name__=='__main__':unittest.main()
