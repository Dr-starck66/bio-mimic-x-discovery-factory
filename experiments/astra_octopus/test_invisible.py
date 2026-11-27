import unittest
import numpy as np
from invisible import *
from benchmark_invisible import protocol, simulate, run

class Tests(unittest.TestCase):
    def test_delay_causal(self):
        u=np.arange(12.);z=history(u,u,u,'delay',4)
        np.testing.assert_array_equal(z,np.r_[np.zeros(4),u[:-4]])
    def test_relaxation(self):
        u=np.ones(30);z=history(u,u,u,'memory_u',.2)
        np.testing.assert_allclose(z,1-np.exp(-DT*np.arange(1,31)/.2))
    def test_hysteresis_history(self):
        x=np.array([0.,.3,.1,-.3,.1]);z=history(x,x,x,'hysteresis',.1)
        self.assertAlmostEqual(x[2],x[4]);self.assertNotAlmostEqual(z[2],z[4])
    def test_future_independence(self):
        a=protocol(1);u=a.u.copy();u[100:]*=-1;x=a.x.copy();x[100:]+=5
        for f,p in SPEC:np.testing.assert_allclose(history(a.x,a.v,a.u,f,p)[:100],history(x,a.v,u,f,p)[:100])
    def test_no_holdout_leak(self):
        t=protocol(1);m=Model((0,1),np.array([0.,1.]),True,0.);a=Trial(t.x,t.v,t.u,t.u+.2);b=Trial(t.x,t.v,t.u,np.r_[a.y[:CAL],a.y[CAL:]+5]);np.testing.assert_allclose(m.predict(a),m.predict(b));self.assertTrue(audit(m,[a])['accepted']);self.assertFalse(audit(m,[b])['accepted'])
    def test_invalid(self):
        t=protocol(1);bad=Trial(t.x,t.v,t.u,t.y+np.nan)
        with self.assertRaises(ValueError):fit([bad])
    def test_recover_combined(self):
        r=run('delay+memory_x',12345)['adaptive'];self.assertTrue(r['exact']);self.assertTrue(r['audit']['accepted'])
    def test_reject_unknown(self):
        r=run('switch_hidden',12345)['adaptive'];self.assertFalse(r['audit']['accepted'])
    def test_sensor_bias_equivalence(self):
        t=protocol(1);physical=Trial(t.x,t.v,t.u,t.u+.2);sensor_bias=Trial(t.x,t.v,t.u,t.u+.2);np.testing.assert_array_equal(design(physical),design(sensor_bias));np.testing.assert_array_equal(physical.y,sensor_bias.y)
    def test_select_independent_of_future_y(self):
        tr=[simulate(protocol(0,p),'delay',25,20+j) for j,p in enumerate((0,.7,1.4,2.1))];m=fit(tr);probes=[protocol(1),protocol(2),protocol(3)];other=[Trial(t.x,t.v,t.u,np.full(len(t.y),999.)) for t in probes];self.assertEqual(select(m,probes),select(m,other))
if __name__=='__main__':unittest.main()
