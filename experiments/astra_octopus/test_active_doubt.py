import unittest,math
from active_doubt import *
class TestActive(unittest.TestCase):
    def setUp(self):self.p=Permit(True,True,0.,.18,.015,1.2,.55)
    def test_waveform(self):
        u=waveform(5);self.assertAlmostEqual(sum(u),0);self.assertAlmostEqual(sum((COUNT-i)*v for i,v in enumerate(u)),0);self.assertLessEqual(max(map(abs,u)),AMP)
    def test_permit(self):self.assertTrue(permitted(self.p))
    def test_denial(self):
        from dataclasses import replace
        for change in ({'authorized':False},{'isolated':False},{'age':.1},{'clearance':.02},{'speed_limit':.1},{'accel_bound':float('nan')},{'accel_bound':.1}):self.assertFalse(permitted(replace(self.p,**change)))
    def test_no_scheduled(self):self.assertEqual(request('normal',False,self.p),'no_probe')
    def test_revoke(self):
        from dataclasses import replace
        a=ActiveDoubt(0,'fallback',False,self.p);self.assertNotEqual(a.command(self.p),0);a.observe({});self.assertEqual(a.command(replace(self.p,authorized=False)),0);self.assertEqual(a.command(self.p),0)
    def test_missing_observation(self):
        a=ActiveDoubt(0,'degraded',False,self.p);a.command(self.p);self.assertEqual(a.command(self.p),0);self.assertEqual(a.state,'external_observation')
    def test_passive_unidentifiable(self):self.assertEqual(diagnose([0.]*COUNT,{k:[0.]*COUNT for k in CHANNELS})[0],'inconclusive')
    def test_no_tracking_reopen(self):
        a=ActiveDoubt(0,'normal',True,self.p);x=v=0.
        for k in range(COUNT):
            u=a.command(self.p);v+=DT*u;x+=DT*v;a.observe(dict(encoder=x,vision=x,imu=u,effort=u))
        self.assertEqual(a.result()[0],'response_consistent');self.assertEqual(a.state,'external_revalidation');self.assertEqual(a.command(self.p),0.)
if __name__=='__main__':unittest.main()
