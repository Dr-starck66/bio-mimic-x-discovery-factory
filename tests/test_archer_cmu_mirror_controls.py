"""Fail-closed tests for mirror-source provenance and real-image negative controls."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
from validation.archer_cmu_mirror_audit import load_mirror_tar, MIRROR_SHA256
from validation.archer_cmu_mirror_controls import mask_center, controls
from validation.archer_vision_real_cmu import images_from_zip, TEST_VIEWS
from tests.test_archer_vision_real_cmu import make_fixture


class MirrorControlsTests(unittest.TestCase):
    def test_mirror_sha_is_pinned(self):
        self.assertEqual(len(MIRROR_SHA256), 64)

    def test_fake_mirror_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.tar.gz"
            p.write_bytes(b"not a real archive")
            with self.assertRaisesRegex(ValueError, "Mirror bytes changed"):
                load_mirror_tar(p)

    def test_mask_center_never_mutates_source(self):
        image = np.linspace(0, 1, 64 * 64, dtype=np.float32).reshape(64, 64)
        original = image.copy()
        result = mask_center(image)
        np.testing.assert_array_equal(image, original)
        self.assertEqual(result.shape, image.shape)
        np.testing.assert_array_equal(result[:9], image[:9])
        np.testing.assert_array_equal(result[55:], image[55:])
        self.assertFalse(np.array_equal(result[9:55, 12:52], image[9:55, 12:52]))

    def test_negative_controls_fixture_reject_real_claims(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "fixture.zip"
            make_fixture(p)
            images, _ = images_from_zip(p, verify_sha=False)
            result = controls(images, seed=20, repetitions=5)
            self.assertEqual(result["n_subjects"], 4)
            self.assertEqual(set(result["method_results"]), {"pixels", "hog", "retina_pool"})
            for conditions in result["method_results"].values():
                self.assertEqual(set(conditions), set(TEST_VIEWS))
                for outcome in conditions.values():
                    self.assertEqual(outcome["randomized_labels_chance"], 0.5)
                    self.assertEqual(
                        outcome["randomized_labels_control_trials"],
                        outcome["trials"] * 5,
                    )
                    self.assertTrue(0 <= outcome["face_center_occluded_top1"] <= 1)

    def test_control_reproducible_on_generated_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "fixture.zip"
            make_fixture(p)
            images, _ = images_from_zip(p, verify_sha=False)
            self.assertEqual(controls(images, seed=20, repetitions=5),
                             controls(images, seed=20, repetitions=5))

    def test_real_mirror_if_supplied_and_checksum_pinned(self):
        p = Path("data/CMU_FACES4_GITHUB_MIRROR.tar.gz")
        if not p.exists():
            self.skipTest("Real images must be separately obtained; not in GitHub")
        images, hashes, provenance = load_mirror_tar(p)
        self.assertFalse(provenance["official_zip_sha256_verified"])
        self.assertEqual(provenance["valid_pgms_in_mirror"], 624)
        self.assertEqual(provenance["selected_views_count"], 118)
        self.assertEqual(len(set(hashes.values())), len(hashes))
        self.assertEqual(len(images), 118)


if __name__ == "__main__":
    unittest.main()
