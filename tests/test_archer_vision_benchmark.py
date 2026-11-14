"""Reproducible software tests; they do not validate a fish-brain hypothesis."""
import unittest
import numpy as np
from validation.archer_vision_benchmark import (
    make_portrait,encode,benchmark,N_CHOICES,N_NOVEL,_identity_traits,_wilson)


class ArcherVisionTests(unittest.TestCase):
    def test_exactly_44_unseen_distractors(self):
        self.assertEqual(N_CHOICES,45)
        self.assertEqual(N_NOVEL,44)
        r=benchmark(seed=8,episodes=2,shots=2)
        self.assertEqual(r["train_ids"],[0,1])
        self.assertEqual(r["novel_test_ids"],list(range(2,46)))
        self.assertEqual(r["identities_total"],46)
        self.assertTrue(r["disjoint_train_test_view_ranges"])

    def test_portrait_shapes_and_reproducibility(self):
        a=make_portrait(3,102,17)
        b=make_portrait(3,102,17)
        self.assertTrue(np.array_equal(a,b))
        self.assertEqual(a.shape,(64,64))
        self.assertGreater(np.std(a),0.05)
        self.assertFalse(np.array_equal(a,make_portrait(4,102,17)))
        self.assertFalse(np.array_equal(a,make_portrait(3,102,17,condition="shifted")))

    def test_feature_dimensions_and_normalization(self):
        img=make_portrait(0,19,0)
        for name,dim in (("pixels",256),("hog",576),("retina_pool",320)):
            with self.subTest(name=name):
                encoded=encode(img,name)
                self.assertEqual(encoded.shape,(dim,))
                self.assertAlmostEqual(float(np.linalg.norm(encoded)),1.0,places=5)

    def test_bad_inputs_fail_closed(self):
        with self.assertRaises(ValueError): make_portrait(46,4,0)
        with self.assertRaises(ValueError): make_portrait(1,4,-3)
        with self.assertRaises(ValueError): make_portrait(1,4,2,condition="other")
        with self.assertRaises(ValueError): encode(np.zeros((64,63)),"pixels")
        with self.assertRaises(ValueError): encode(np.full((64,64),np.nan),"pixels")
        with self.assertRaises(ValueError): encode(np.zeros((64,64)),"unknown")
        with self.assertRaises(ValueError): benchmark(episodes=0)
        with self.assertRaises(ValueError): benchmark(shots=0)

    def test_report_counts_and_boundaries(self):
        r=benchmark(seed=6,episodes=3,shots=2)
        self.assertFalse(r["real_faces"])
        self.assertEqual(r["status"],"SOFTWARE_BENCHMARK_ONLY")
        self.assertAlmostEqual(r["chance_45way"],1/45)
        self.assertAlmostEqual(r["chance_2afc"],0.5)
        for method in ("pixels","hog","retina_pool"):
            for condition in ("matched","shifted"):
                m=r["methods"][method][condition]
                self.assertEqual(m["total"],3)
                self.assertEqual(m["top1_accuracy"],round(m["correct"]/3,6))
                self.assertTrue(1<=m["mean_target_rank"]<=45)
                self.assertEqual(len(m["score_sha256"]),64)
                self.assertEqual(m["two_choice_total_pairs"],3*44)
                self.assertTrue(0<=m["two_choice_select_familiar_correct"]<=132)
                self.assertTrue(0<=m["two_choice_avoid_familiar_correct"]<=132)

    def test_seeded_scores_deterministic(self):
        a=benchmark(seed=12,episodes=2,shots=2)
        b=benchmark(seed=12,episodes=2,shots=2)
        for method in a["methods"]:
            for condition in a["methods"][method]:
                self.assertEqual(a["methods"][method][condition]["score_sha256"],
                                 b["methods"][method][condition]["score_sha256"])

    def test_identity_geometry_independent_of_view(self):
        self.assertTrue(np.array_equal(_identity_traits(3,9),_identity_traits(3,9)))
        self.assertFalse(np.array_equal(_identity_traits(3,9),_identity_traits(4,9)))

    def test_identity_ablated_mode_is_explicit(self):
        r=benchmark(seed=1,episodes=2,shots=2,identity_ablated=True)
        self.assertTrue(r["identity_ablated"])
        self.assertFalse(r["real_faces"])

    def test_null_and_confidence_interval(self):
        self.assertEqual(_wilson(0,0),[0,1])
        low,high=_wilson(10,20)
        self.assertLess(low,0.5)
        self.assertGreater(high,0.5)

if __name__=="__main__": unittest.main()
