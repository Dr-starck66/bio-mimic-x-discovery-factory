"""Tests for strict face-vs-context counterfactual validation (no photo pixels included)."""
import hashlib
import unittest
from unittest.mock import patch
import numpy as np
from validation import archer_cmu_counterfactual_faces as cc
from validation.archer_vision_real_cmu import SUBJECTS,TRAIN_VIEWS,TEST_VIEWS

class CounterfactualTests(unittest.TestCase):
    def test_masks_nontrivial_and_face_local(self):
        for m in cc.MASKS:
            mask=cc.feathered_ellipse(m)
            self.assertEqual(mask.shape,(64,64))
            self.assertEqual(mask.dtype,np.float32)
            self.assertEqual(float(mask[0,0]),0.0)
            self.assertEqual(float(mask[33,32]),1.0)
            self.assertGreater(float(mask.sum()),200.0)
            self.assertLess(float(mask.sum()),1800.0)
        self.assertLess(cc.feathered_ellipse('inner_ellipse_strict').sum(),cc.feathered_ellipse('inner_ellipse_broad').sum())

    def test_missing_mask_rejected(self):
        with self.assertRaises(ValueError):cc.feathered_ellipse('invented')

    def test_same_background_outside_face_is_identical(self):
        m=cc.feathered_ellipse('inner_ellipse_strict')
        a=np.random.default_rng(0).random((64,64),dtype=np.float32)
        b=np.random.default_rng(1).random((64,64),dtype=np.float32)
        common=np.random.default_rng(2).random((64,64),dtype=np.float32)
        x=cc.composite(a,common,m);y=cc.composite(b,common,m)
        np.testing.assert_array_equal(x[m==0],y[m==0])
        # Only the masked region may differ; no leak from a/b outside mask.
        aa=a.copy();aa[m==0]=0
        np.testing.assert_array_equal(x,cc.composite(aa,common,m))

    def test_background_permutation_preserves_face_content(self):
        m=cc.feathered_ellipse('inner_ellipse_strict')
        a=np.random.default_rng(10).random((64,64),dtype=np.float32)
        b=np.random.default_rng(11).random((64,64),dtype=np.float32)
        out=cc.composite(a,b,m)
        np.testing.assert_array_equal(out[m==1],a[m==1])
        np.testing.assert_array_equal(out[m==0],b[m==0])
        self.assertTrue(np.isfinite(out).all())

    def test_composite_rejects_invalid(self):
        m=cc.feathered_ellipse('inner_ellipse_strict');a=np.zeros((64,64),dtype=np.float32)
        with self.assertRaises(ValueError):cc.composite(np.zeros((60,64),dtype=np.float32),a,m)
        with self.assertRaises(ValueError):cc.composite(np.full((64,64),np.nan),a,m)
        with self.assertRaises(ValueError):cc.composite(a,a,np.full((64,64),2))

    def test_winner_tie_not_target_first(self):
        scores=np.ones(17)
        choices={cc._argmax_ties(scores,str(x),20261115) for x in range(80)}
        self.assertGreater(len(choices),6)
        self.assertEqual(cc._argmax_ties(scores,'fixture',20261115),cc._argmax_ties(scores,'fixture',20261115))

    @staticmethod
    def synth():
        imgs,hashes={},{}
        views=TRAIN_VIEWS+sum(TEST_VIEWS.values(),())
        for i,person in enumerate(SUBJECTS[:9]):
            for vi,view in enumerate(views):
                rng=np.random.default_rng(7000+i*31+vi)
                a=np.full((64,64),0.1+0.07*i,dtype=np.float32)
                a[20:47,20:45]=0.3+0.05*(i%5)
                a[29+i%3,25:39]=0.13
                a += rng.normal(0,0.005,(64,64)).astype(np.float32)
                a=np.clip(a,0,1)
                imgs[(person,view)]=a
                hashes[(person,view)]=hashlib.sha256(a.tobytes()).hexdigest()
        return imgs,hashes

    def test_provenance_hash_duplicate_rejected(self):
        imgs, hashes=self.synth()
        keys=list(hashes)
        hashes[keys[-1]]=hashes[keys[0]]
        with self.assertRaisesRegex(ValueError,'duplicate|Duplicate'):
            cc.evaluate(imgs,hashes,masks=('inner_ellipse_strict',),swap_offsets=(1,))

    def test_no_fixed_point_swap(self):
        imgs,hashes=self.synth()
        with self.assertRaisesRegex(ValueError,'deranged'):
            cc.evaluate(imgs,hashes,masks=('inner_ellipse_strict',),swap_offsets=(8,))

    def test_synthetic_cue_swap_is_executed_without_claiming_real(self):
        imgs,hashes=self.synth()
        # Pin single method and single test condition for a fast software test.
        with patch.object(cc,'METHODS',('pixels',)),patch.object(cc,'TEST_VIEWS',{'pose_shift':('left_neutral_open',)}):
            r=cc.evaluate(imgs,hashes,masks=('inner_ellipse_strict',),swap_offsets=(1,))
        self.assertEqual(r['subjects_eligible'],9)
        self.assertTrue(r['ROI_not_anatomically_landmark_annotated'])
        pair=r['methods']['pixels']['pose_shift/inner_ellipse_strict']
        self.assertEqual(pair['neutral_flat']['trials'],9)
        self.assertEqual(pair['swapped_background_with_full_enrollment']['trials'],9)
        self.assertEqual(pair['swapped_background_with_full_enrollment']['face_owner_correct']+
                         pair['swapped_background_with_full_enrollment']['background_owner_correct'] <= 9,True)
        self.assertEqual(r['chance_top1'],round(1/8,7))

if __name__=='__main__':unittest.main()
