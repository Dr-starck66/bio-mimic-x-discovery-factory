import unittest,tempfile,zipfile
from pathlib import Path
from validation.archer_cmu_extract_official_tar import extract_local

class ExtractTests(unittest.TestCase):
    def test_rejects_fake_official_archive(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'false.zip';f.write_bytes(b'faux')
            with self.assertRaisesRegex(ValueError,'Official UCI SHA-256 mismatch'):
                extract_local(f,Path(d)/'out.tar.gz')
            self.assertFalse((Path(d)/'out.tar.gz').exists())
    def test_rejects_zip_file_with_valid_zip_structure_but_wrong_hash(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'false.zip'
            with zipfile.ZipFile(f,'w') as z:z.writestr('faces_4.tar.gz',b'gibberish')
            with self.assertRaisesRegex(ValueError,'Official UCI SHA-256 mismatch'):
                extract_local(f,Path(d)/'out.tar.gz')
if __name__=='__main__':unittest.main()
