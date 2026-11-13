import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kaggle_public_expression_qc import analyze

class Tests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.path=Path(self.dir.name)/'public.csv'
        self.path.write_text('sample_id,HAND1,HAND2\na,1,2\nb,0,3\n')
    def tearDown(self): self.dir.cleanup()
    def check(self, **options):
        v={'csv_path':self.path,'source_url':'https://example.org/public-expression','public_approved':True};v.update(options)
        return analyze(**v)
    def test_qc_only(self):
        r=self.check();self.assertEqual(r['n_samples'],2);self.assertEqual(r['n_genes'],2);self.assertEqual(r['status'],'PARTIAL')
    def test_no_public_approval(self):
        with self.assertRaises(PermissionError):self.check(public_approved=False)
    def test_duplicate_sample(self):
        self.path.write_text('sample_id,HAND1,HAND2\na,1,2\na,0,3\n')
        with self.assertRaises(ValueError):self.check()
    def test_negative_counts(self):
        self.path.write_text('sample_id,HAND1,HAND2\na,1,-2\nb,0,3\n')
        with self.assertRaises(ValueError):self.check()
    def test_missing(self):
        self.path.write_text('sample_id,HAND1,HAND2\na,1,\nb,0,3\n')
        with self.assertRaises(ValueError):self.check()
    def test_http_rejected(self):
        with self.assertRaises(ValueError):self.check(source_url='http://example.org/public')
    def test_infinite_rejected(self):
        self.path.write_text('sample_id,HAND1,HAND2\na,1,inf\nb,0,3\n')
        with self.assertRaises(ValueError):self.check()

if __name__=='__main__':unittest.main()
