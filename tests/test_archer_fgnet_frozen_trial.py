import unittest
import numpy as np
from validation.archer_fgnet_frozen_trial import preprocess,inner_mask,tie_winner
class FrozenTrialTests(unittest.TestCase):
    def test_mask_is_fixed_bounded(self):
        m=inner_mask()
        self.assertEqual(m.shape,(64,64))
        self.assertTrue(np.all((m>=0)&(m<=1)))
    def test_inner_regions_have_weight(self):
        m=inner_mask()
        for x,y in [(20,25),(44,25),(32,37),(32,49)]:
            self.assertGreater(m[y,x],.5)
    def test_ties_are_not_biased_to_first_identity(self):
        self.assertGreater(len({tie_winner(np.zeros(82),n) for n in range(100)}),30)
    def test_reject_degenerate_eye_gap(self):
        z=np.zeros((64,64),dtype=np.float32)
        with self.assertRaisesRegex(ValueError,"Eye gap implausible"):
            preprocess(z,np.zeros((68,2),dtype=np.float32))
    def test_expected_masks_on_generated_geometry(self):
        img=np.random.default_rng(1).random((128,128),dtype=np.float32)
        pts=np.zeros((68,2),dtype=np.float32)
        pts[36:42]=[32,50];pts[42:48]=[84,50]
        pts[30]=[58,76];pts[62]=[58,100]
        p=preprocess(img,pts)
        self.assertEqual(len(p),4)
        self.assertTrue(np.allclose(p["uniform_negative"],.5))
        self.assertTrue(np.allclose(p["inner_face_only"]+p["outside_inner_face"],
                                     p["aligned_full"]+.5,atol=1e-5))
    def test_nans_rejected(self):
        img=np.zeros((128,128),dtype=np.float32)
        pts=np.full((68,2),np.nan,dtype=np.float32)
        with self.assertRaisesRegex(ValueError,"Bad photo/landmarks"):
            preprocess(img,pts)
if __name__=="__main__":unittest.main()
