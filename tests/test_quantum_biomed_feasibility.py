"""Local correctness, no-leakage contract, null-control and reproducibility gates."""
import unittest
import numpy as np
from validation.quantum_biomed_feasibility import fidelity_kernel, preprocess_fold, run


class QuantumFeasibilityTests(unittest.TestCase):
    def test_kernel_symmetry_normalization_and_psd(self):
        x=np.random.default_rng(4).normal(size=(9,4))
        k=fidelity_kernel(x,x)
        np.testing.assert_allclose(k,k.T,atol=1e-12)
        np.testing.assert_allclose(np.diag(k),np.ones(len(x)),atol=1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(k).min(),-1e-10)

    def test_identical_vectors_unit_fidelity(self):
        x=np.array([[0,1,2,3],[2,3,4,5]],dtype=float)
        np.testing.assert_allclose(np.diag(fidelity_kernel(x,x)),[1,1],atol=1e-12)

    def test_invalid_feature_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            fidelity_kernel(np.ones((2,3)),np.ones((4,2)))

    def test_train_only_transform_unaffected_by_test_perturbations(self):
        r=np.random.default_rng(5)
        x=r.normal(size=(60,30)); y=np.r_[np.zeros(30,dtype=int),np.ones(30,dtype=int)]
        train=x[:50]; test=x[50:]
        a1,b1=preprocess_fold(train,y[:50],test)
        a2,b2=preprocess_fold(train,y[:50],test+1000)
        np.testing.assert_array_equal(a1,a2)
        self.assertFalse(np.allclose(b1,b2))

    def test_control_is_explicitly_nonclinical(self):
        out=run(seed=12,repeats=1,null_permutations=1)
        self.assertFalse(out["claims"]["quantum_hardware_executed"])
        self.assertEqual(out["claims"]["longevity_efficacy"],"UNVERIFIED")
        self.assertEqual(out["method"]["samples"],569)
        self.assertEqual(out["null_label_permutation"]["folds"],5)

    def test_repeatability(self):
        a=run(seed=7,repeats=1,null_permutations=1)
        b=run(seed=7,repeats=1,null_permutations=1)
        self.assertEqual(a,b)


if __name__=="__main__":
    unittest.main()