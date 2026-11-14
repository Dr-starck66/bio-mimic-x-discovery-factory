import unittest,io,zipfile,tarfile,hashlib
from validation.archer_cmu_official_zip_verifier import inspect_zip_bytes,pgm_manifest


def fixture_tar(payload=b'P5\n2 1\n255\n\x00\xff'):
    buff=io.BytesIO()
    with tarfile.open(fileobj=buff,mode='w:gz') as out:
        data=payload
        t=tarfile.TarInfo('faces_4/an2i/an2i_straight_neutral_open_4.pgm');t.size=len(data)
        out.addfile(t,io.BytesIO(data))
    return buff.getvalue()


def fixture_zip(b):
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,'w') as z:
        z.writestr('faces_4.tar.gz',b)
    return buff.getvalue()

class OfficialZipVerifierTests(unittest.TestCase):
    def test_fake_zip_rejected_as_official(self):
        z=fixture_zip(fixture_tar())
        with self.assertRaisesRegex(ValueError,'Official ZIP SHA-256 mismatch'):
            inspect_zip_bytes(z,fixture_tar(),expected_pgm_count=1)
    def test_fixture_sha_override_never_claims_official_pass(self):
        t=fixture_tar();z=fixture_zip(t)
        x=inspect_zip_bytes(z,t,expected_zip_sha=hashlib.sha256(z).hexdigest(),expected_pgm_count=1)
        self.assertEqual(x['status'],'PARTIAL_MISMATCH_OR_FIXTURE')
        self.assertFalse(x['official_zip_sha256_matches_published'])
        self.assertTrue(x['nested_tar_matches_mirror_bytewise'])
        self.assertTrue(x['same_pgm_file_bytes'])
    def test_fixture_data_difference_reported(self):
        t=fixture_tar();u=fixture_tar(b'P5\n2 1\n255\n\xff\x00');z=fixture_zip(t)
        x=inspect_zip_bytes(z,u,expected_zip_sha=hashlib.sha256(z).hexdigest(),expected_pgm_count=1)
        self.assertFalse(x['same_pgm_file_bytes'])
        self.assertEqual(len(x['changed_pgm_entries']),1)
    def test_missing_nested_rejected(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('other.txt','x')
        with self.assertRaisesRegex(ValueError,'Expected exactly one'):
            inspect_zip_bytes(b.getvalue(),fixture_tar(),expected_zip_sha=hashlib.sha256(b.getvalue()).hexdigest(),expected_pgm_count=1)
    def test_bounded_payload(self):
        with self.assertRaisesRegex(ValueError,'missing or outside bounded'):
            inspect_zip_bytes(b'',b'fake')
    def test_manifest_count(self):
        self.assertEqual(len(pgm_manifest(fixture_tar())),1)

if __name__=='__main__':unittest.main()
