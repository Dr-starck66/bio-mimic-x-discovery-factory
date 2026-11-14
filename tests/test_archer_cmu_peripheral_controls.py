import unittest
from pathlib import Path
import numpy as np
from validation.archer_cmu_peripheral_controls import preprocess,evaluate,CORE,_winner
from validation.archer_cmu_mirror_audit import load_mirror_tar
from validation.archer_vision_real_cmu import eligible_subjects

class PeripheralTests(unittest.TestCase):
    def test_invariant_fixed_background(self):
        a=np.random.default_rng(2).random((64,64),dtype=np.float32)
        b=a.copy();mask=np.ones_like(a,dtype=bool);mask[CORE]=False;b[mask]=0
        np.testing.assert_array_equal(preprocess(a,'central_only'),preprocess(b,'central_only'))
        np.testing.assert_array_equal(preprocess(a,'central_crop'),preprocess(b,'central_crop'))
        np.testing.assert_array_equal(preprocess(a,'central_contrast'),preprocess(b,'central_contrast'))
    def test_periphery_invariant_to_inside(self):
        a=np.random.default_rng(3).random((64,64),dtype=np.float32)
        b=a.copy();b[CORE]=0
        np.testing.assert_array_equal(preprocess(a,'peripheral_only'),preprocess(b,'peripheral_only'))
    def test_all_constant_no_target_leakage(self):
        a=np.ones((64,64),dtype=np.float32)
        np.testing.assert_array_equal(preprocess(a,'all_constant'),np.full_like(a,.5))
        # When scores tied, winner should depend on tie-seed, never target-index 0.
        self.assertGreater(len({_winner(np.zeros(17),seed) for seed in range(80)}),5)
    def test_input_validation(self):
        with self.assertRaises(ValueError):preprocess(np.ones((64,63)),'full')
        with self.assertRaises(ValueError):preprocess(np.full((64,64),np.nan),'full')
        with self.assertRaises(ValueError):preprocess(np.zeros((64,64)),'unknown')
    def test_original_image_not_modified(self):
        a=np.random.default_rng(8).random((64,64),dtype=np.float32);b=a.copy()
        for m in ['full','central_only','central_crop','central_contrast','peripheral_only','border_only','all_constant']:
            self.assertEqual(preprocess(a,m).shape,(64,64))
        np.testing.assert_array_equal(a,b)
    def test_mirror_eval_reproducible(self):
        path=Path('data/CMU_FACES4_GITHUB_MIRROR.tar.gz')
        if not path.exists():self.skipTest('No mirror')
        images,sha,_=load_mirror_tar(path)
        a=evaluate(images,sha,seed=9)
        b=evaluate(images,sha,seed=9)
        self.assertEqual(a,b)
        self.assertFalse(a['source_zip_uci_verified'])
        self.assertEqual(a['n_complete_subjects'],18)
        self.assertTrue(a['roi_selected_after_dataset_inspection'])
        for m in a['methods']:
            for mode in a['methods'][m]:
                for cond,v in a['methods'][m][mode].items():
                    self.assertEqual(v['total'],36 if cond=='frontal_expression' else 18)
                    self.assertLessEqual(v['correct'],v['total'])
        # Negative control with constant inputs must not look like accurate classification.
        self.assertLessEqual(a['methods']['pixels']['all_constant']['pose_shift']['correct'],5)
    def test_duplicate_checksums_rejected(self):
        path=Path('data/CMU_FACES4_GITHUB_MIRROR.tar.gz')
        if not path.exists():self.skipTest('No mirror')
        images,sha,_=load_mirror_tar(path)
        bad=sha.copy();keys=list(bad);bad[keys[-1]]=bad[keys[0]]
        with self.assertRaisesRegex(ValueError,'Duplicated'):evaluate(images,bad)

if __name__=='__main__':unittest.main()
