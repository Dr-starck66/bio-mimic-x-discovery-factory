import pathlib,tempfile,unittest
from validation.orthogroup_proteome_adapter import run,fasta
class TestAdapter(unittest.TestCase):
 def test_identical_cross_species(self):
  with tempfile.TemporaryDirectory() as d:
   a=pathlib.Path(d)/"a.fa";b=pathlib.Path(d)/"b.fa"
   a.write_text(">g1\nACDEFGHIKLMNPQRSTVWY\n>g2\nYYYYYYYYYYYYYYYYYYYY\n")
   b.write_text(">h1\nACDEFGHIKLMNPQRSTVWY\n>h2\nCCCCCCCCCCCCCCCCCCCC\n")
   groups,r=run([a,b]);self.assertIn(["a|g1","b|h1"],groups);self.assertEqual(r["n_genes"],4)
 def test_deterministic(self):
  with tempfile.TemporaryDirectory() as d:
   a=pathlib.Path(d)/"a.fa";b=pathlib.Path(d)/"b.fa";a.write_text(">a\nACDEFGHIK\n");b.write_text(">b\nACDEFGHIK\n")
   self.assertEqual(run([a,b])[0],run([a,b])[0])
 def test_reject_bad_fasta(self):
  with tempfile.TemporaryDirectory() as d:
   a=pathlib.Path(d)/"a.fa";a.write_text("NOHEADER\n")
   with self.assertRaises(ValueError):list(fasta(a))
if __name__=="__main__":unittest.main()
