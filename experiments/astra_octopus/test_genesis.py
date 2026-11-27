import unittest
from dataclasses import replace
import numpy as np
from genesis import Atom,neighbors,search,select_probe,audit,Symbolic
from benchmark_genesis import P,GRID,run
class TestGenesis(unittest.TestCase):
    def setUp(self):
        r=np.random.default_rng(42);x,v,u=r.uniform(-.3,.3,(3,300));y=u-x-.4*v+.3*np.sin(29*x);self.data=np.column_stack([x,v,u,y])
    def test_exact_sine(self):
        m,n=search(self.data);self.assertEqual(m[0].atom,Atom('sin','x'));self.assertAlmostEqual(m[0].k,29,places=3);self.assertGreater(n,72)
    def test_dimensions(self):
        self.assertEqual(Atom('sin','x+v','v').dimensions(),(0,0))
        with self.assertRaises(ValueError):Atom('sin','x+v').dimensions(False)
        with self.assertRaises(ValueError):Atom('sin','x').dimensions(False)
    def test_mutation(self):
        a=Atom('sin','x');b=Atom('cos','v','u');n=neighbors([a,b]);self.assertIn(Atom('sin','v','u'),n);self.assertIn(Atom('sin','x','v'),n)
    def test_bad_data(self):
        for d in (self.data[:5],self.data[:,:3],np.full((40,4),np.nan),np.zeros((40,4))):
            with self.assertRaises(ValueError):search(d)
    def test_refute(self):
        m,_=search(self.data);self.assertTrue(audit(m[0],self.data)['accepted']);d=self.data.copy();d[:,3]+=.3;self.assertFalse(audit(m[0],d)['accepted'])
    def test_permission(self):
        m,_=search(self.data)
        for p in (replace(P,authorized=False),replace(P,isolated=False),replace(P,age=.2),replace(P,clearance=.01)):
            self.assertIsNone(select_probe(m,GRID,p))
    def test_heldout_product(self):
        r=run('modulated',9000);self.assertTrue(r['adaptive']['structure']);self.assertTrue(r['adaptive']['accepted']);self.assertEqual(len(r['chosen']),2)
    def test_unknown_memory(self):
        r=run('hidden_memory',9001);self.assertFalse(r['adaptive']['accepted'])
if __name__=='__main__':unittest.main()
