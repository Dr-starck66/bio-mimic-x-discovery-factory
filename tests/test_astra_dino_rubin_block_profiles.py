"""Tests intentionally include negative controls and synthetic positive control."""
from __future__ import annotations
import hashlib,sys,tempfile,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'validation'))
from astra_dino_rubin_block_profiles import (
    read_matched,variant_dosages,genotype_pca,group_indices,residualize_by_group,
    orthonormal_design,r2,permutation_maxT,GateError,load_author_loci,
)

class Tests(unittest.TestCase):
    def test_maf_pass(self):
        a=variant_dosages(['0/1']*50,'GT',list(range(50)))
        self.assertEqual(len(a),50)
    def test_maf_fail_fixed(self):
        self.assertIsNone(variant_dosages(['0/0']*50,'GT',list(range(50))))
    def test_missing_exceeds_twenty_percent(self):
        self.assertIsNone(variant_dosages(['./.']*11+['0/1']*39,'GT',list(range(50))))
    def test_exact_40_calls_pass(self):
        self.assertIsNotNone(variant_dosages(['./.']*10+['0/1']*40,'GT',list(range(50))))
    def test_non_biallelic_rejected(self):
        self.assertIsNone(variant_dosages(['0/2']*50,'GT',list(range(50))))
    def test_format_gt_index(self):
        self.assertIsNotNone(variant_dosages(['9:0/1']*50,'DP:GT',list(range(50))))
    def test_phenotype_blind_pca(self):
        v=np.arange(50)%3
        m=[(i,np.array((v+i)%3,dtype=float)) for i in range(1,8)]
        p,e=genotype_pca(m)
        self.assertEqual(p.shape,(50,2));self.assertEqual(len(e),2)
    def test_pca_rank_deficient_rejected(self):
        m=[(i,np.array(np.arange(50)%2,dtype=float)) for i in range(10)]
        with self.assertRaises(GateError):genotype_pca(m)
    def test_residualize_pop(self):
        g=group_indices(['a']*5+['b']*5)
        v=residualize_by_group(np.array([[1.]]*5+[[20.]]*5),g)
        self.assertTrue(np.allclose(v,0))
    def test_r2_synthetic_perfect(self):
        g=group_indices(['a']*20+['b']*20)
        x=np.linspace(-1,1,40).reshape(-1,1)
        q=orthonormal_design(x,g)
        y=residualize_by_group(x,g)
        self.assertAlmostEqual(float(r2(q,y)[0]),1,places=9)
    def test_within_pop_permutation_and_family_correction(self):
        g=group_indices(['a']*15+['b']*15)
        rng=np.random.default_rng(123)
        x=rng.normal(size=(30,2));y=np.column_stack((x[:,0],rng.normal(size=30)))
        y=residualize_by_group(y,g)
        models={'a':orthonormal_design(x,g),'b':orthonormal_design(rng.normal(size=(30,2)),g)}
        keys,obs,praw,padj,dist=permutation_maxT(models,y,g,199,101)
        self.assertEqual(dist.shape,(199,));self.assertTrue(np.all(padj>=praw-1e-9))
        self.assertGreater(float(obs[0,0]),.8)
    def test_nperm_gate(self):
        g=group_indices(['a']*10+['b']*10);x=np.random.default_rng(2).normal(size=(20,2))
        with self.assertRaises(GateError):permutation_maxT({'a':orthonormal_design(x,g)},x,g,98,1)
    def test_source_not_fabricated(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'a.txt';f.write_text('fake positions')
            with self.assertRaisesRegex(ValueError,'AUTHOR_INTERVAL_SOURCE_GIT_BLOB_MISMATCH'):
                load_author_loci(f)
    def test_bad_morph_crosswalk_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            from pathlib import Path
            folder=Path(td)
            (folder/'pPCAeigen.txt').write_text('SampleID\tPopulation\nfoo_S1\ta\n')
            (folder/'Morphometrics.txt').write_text('AccNo\tBeak_length\tBeak_height\tBeak_width\nfoo\t1\t1\t1\n')
            with self.assertRaises(GateError):read_matched(folder,['foo_S1'])

if __name__=='__main__':unittest.main()
