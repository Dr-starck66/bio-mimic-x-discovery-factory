import unittest
import numpy as np
from independent_check import *
from benchmark_witness import trial
class Tests(unittest.TestCase):
    def test_gain_interval(self):
        for g in GAIN:
            w=witness(np.full(N,.2),np.full(N,.2+g*.3),np.full(N,.2));self.assertLessEqual(w['interval'][0],.3);self.assertGreaterEqual(w['interval'][1],.3)
    def test_negative_force(self):
        w=witness(np.zeros(N),np.full(N,-.3),np.zeros(N));self.assertEqual(classify(w['interval']),'present')
    def test_linear_drift(self):
        w=witness(np.zeros(N),np.full(N,.31),np.full(N,.02));self.assertTrue(w['interval'][0]<=.3<=w['interval'][1])
    def test_unavailable(self):self.assertEqual(witness([],[],[],available=False)['status'],'unavailable')
    def test_drift(self):self.assertEqual(witness(np.zeros(N),np.zeros(N),np.full(N,.1))['status'],'unstable_zero')
    def test_invalid(self):self.assertEqual(witness(np.full(N,np.nan),np.zeros(N),np.zeros(N))['status'],'invalid')
    def test_conflict(self):self.assertEqual(trial('coherent_deception',31000)['after'],'witness_conflict')
    def test_common_mode_negative(self):self.assertEqual(trial('all_channels_coherent',31000)['after'],'force')
    def test_abstain(self):self.assertEqual(trial('witness_unavailable',31000)['after'],'unverified')
if __name__=='__main__':unittest.main()
