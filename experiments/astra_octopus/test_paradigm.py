import unittest
from fractions import Fraction
import numpy as np
from paradigm import *
from benchmark_paradigm import context,simulate,run
class Tests(unittest.TestCase):
    def test_projection(self):
        np.testing.assert_allclose(P@A,0,atol=1e-12);np.testing.assert_allclose(P@P,P,atol=1e-12)
    def test_nominal(self):self.assertEqual(run('nominal',74000)['adaptive']['label'],'no_residual_detected')
    def test_interaction(self):self.assertEqual(run('interaction',74000)['adaptive']['label'],'candidate_extension')
    def test_two_latents(self):
        r=run('two_latents',74000)['adaptive'];self.assertEqual(r['rank'],2);self.assertEqual(set(r['terms']),{'x*u','lag(u)'})
    def test_random_rejected(self):self.assertEqual(run('random_hidden',74000)['adaptive']['label'],'unexplained')
    def test_outside_rejected(self):self.assertEqual(run('outside_grammar',74000)['adaptive']['label'],'unexplained')
    def test_history_causal(self):
        x=context(44);y=x.copy();y[30:]+=4
        for k,a in grammar(x).items():np.testing.assert_allclose(a[:30],grammar(y)[k][:30])
    def test_bad_data(self):
        with self.assertRaises(ValueError):fit([Trial(np.zeros((10,2)),np.full((10,len(CHANNELS)),np.nan))])
    def test_alias_exact(self):
        r=alias_certificate();z=list(map(Fraction,r['targets']['physical_force']['counterexample']));self.assertNotEqual(z[0],0)
        self.assertTrue(all(sum(a*b for a,b in zip(tuple(map(int,row))+(int(row[0]),),z))==0 for row in A))
    def test_alias_negative(self):self.assertEqual(run('coherent_alias',74000)['adaptive']['label'],'no_residual_detected')
    def test_measurement_plan(self):
        p=missing_measurement();self.assertEqual(p['ordinary_only']['status'],'impossible');self.assertEqual(p['hypothetical_isolation']['status'],'complete');self.assertEqual(p['hypothetical_isolation']['actions'],['isolated_physical'])
    def test_factors_reconstruct(self):
        t=[simulate('two_latents',5,context(6,3),7)];m=fit(t)[0];f=grammar(t[0].context);y=np.zeros_like(t[0].response)
        for z in m.factors():y+=np.outer(sum(v*f[k] for k,v in z['latent'].items()),list(z['loading'].values()))
        np.testing.assert_allclose(y,m.predict(t[0].context),atol=1e-12)
if __name__=='__main__':unittest.main()
