"""Software-only tests using tiny generated PGM fixtures; never claim real faces."""
import io
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np

from validation.archer_vision_real_cmu import (
    SUBJECTS, TRAIN_VIEWS, TEST_VIEWS, eligible_subjects, images_from_zip,
    compare, sha256, DATASET_SHA256,
)


def make_fixture(path, people=4, *, duplicate=False, width=32):
    tarblob=io.BytesIO()
    specs=TRAIN_VIEWS + sum(TEST_VIEWS.values(), ())
    with tarfile.open(fileobj=tarblob,mode="w:gz") as tar:
        for person_index,person in enumerate(SUBJECTS[:people]):
            for view_index,view in enumerate(specs):
                if duplicate:
                    pix=np.zeros((30,width),dtype=np.uint8)
                else:
                    rng=np.random.default_rng(np.random.SeedSequence([person_index,view_index,88]))
                    pix=rng.integers(0,256,(30,width),dtype=np.uint8)
                data=f"P5\n{width} 30\n255\n".encode()+pix.tobytes()
                item=tarfile.TarInfo(f"faces_4/{person}/{person}_{view}_4.pgm")
                item.size=len(data)
                tar.addfile(item,io.BytesIO(data))
    with zipfile.ZipFile(path,"w") as zipf:
        zipf.writestr("faces_4.tar.gz",tarblob.getvalue())


class RealCmuSoftwareTests(unittest.TestCase):
    def test_source_fingerprint_is_pinned(self):
        self.assertEqual(len(DATASET_SHA256),64)
        self.assertNotEqual(DATASET_SHA256, sha256(b"fake archive"))

    def test_reject_unofficial_archive_default(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fake.zip"
            make_fixture(path)
            with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):
                images_from_zip(path)

    def test_parse_and_split_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fixture.zip"
            make_fixture(path)
            images, provenance=images_from_zip(path,verify_sha=False)
            self.assertFalse(provenance["source"]["archive_sha_verified"])
            self.assertEqual(len(images),24)
            subjects,excluded=eligible_subjects(images)
            self.assertEqual(len(subjects),4)
            self.assertEqual(len(excluded),16)
            self.assertEqual(images[(subjects[0],"straight_neutral_open")].shape,(64,64))
            self.assertNotEqual(
                provenance["sha256_by_sample"][(subjects[0],"straight_neutral_open")],
                provenance["sha256_by_sample"][(subjects[0],"straight_sad_open")]
            )

    def test_methods_and_negative_control_fixture_only(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fixture.zip"
            make_fixture(path)
            images,meta=images_from_zip(path,verify_sha=False)
            report=compare(images=images,checksums=meta["sha256_by_sample"],seed=78,verified_source=False)
            self.assertEqual(report["status"],"FIXTURE_ONLY")
            self.assertFalse(report["source_verified"])
            self.assertEqual(report["eligible_identities"],4)
            self.assertEqual(report["novel_identities_per_fold"],2)
            self.assertEqual(set(report["methods"]),{"pixels","hog","retina_pool"})
            for method in report["methods"]:
                for cond in TEST_VIEWS:
                    m=report["methods"][method][cond]
                    self.assertEqual(m["episodes"], 8 if cond=="frontal_expression" else 4)
                    self.assertEqual(m["two_choice_pairs_correlated"],m["episodes"]*2)
                    self.assertTrue(0 <= m["top1_accuracy"] <=1)

    def test_duplicates_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"duplicated.zip"
            make_fixture(path,duplicate=True)
            images,meta=images_from_zip(path,verify_sha=False)
            with self.assertRaisesRegex(ValueError,"Duplicate raw images"):
                compare(images=images,checksums=meta["sha256_by_sample"])

    def test_wrong_image_size_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"wrong-size.zip"
            make_fixture(path,width=31)
            with self.assertRaisesRegex(ValueError,"PGM dimensions"):
                images_from_zip(path,verify_sha=False)

    def test_insufficient_complete_subjects_fail(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"few.zip"
            make_fixture(path,people=3)
            images,meta=images_from_zip(path,verify_sha=False)
            with self.assertRaisesRegex(ValueError,"Insufficient complete"):
                compare(images=images,checksums=meta["sha256_by_sample"])

    def test_deterministic_fixture_results(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fixture.zip"
            make_fixture(path)
            images,meta=images_from_zip(path,verify_sha=False)
            a=compare(images=images,checksums=meta["sha256_by_sample"],seed=78)
            b=compare(images=images,checksums=meta["sha256_by_sample"],seed=78)
            self.assertEqual(a,b)

if __name__=="__main__":unittest.main()