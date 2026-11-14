import sys, unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'validation'))
from astra_dino_data_s2_author_intersect import load_author_loci,find_interval,git_blob_sha,checked_source_csv
L=Path(__file__).resolve().parents[1]/'data/Rubin2022_28Loci_start_stop_author_original.txt'
class TestRubinSource(unittest.TestCase):
 def test_28_exact_regions(self):self.assertEqual(len(load_author_loci(L)[0]),28)
 def test_author_hmga2_region(self):
  data,n,_=load_author_loci(L); self.assertEqual(n['HMGA2'],3);self.assertEqual(next(x for x in data if x['author_locus_number']==3)['start_as_published'],32232902)
 def test_author_alx1_region(self):
  data,n,_=load_author_loci(L);self.assertEqual(n['ALX1'],7);self.assertEqual(next(x for x in data if x['author_locus_number']==7)['end_as_published'],42199937)
 def test_source_mutation_rejected(self):
  b=L.read_bytes().replace(b'32232902',b'32232903');
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.txt';p.write_bytes(b)
   with self.assertRaisesRegex(ValueError,'AUTHOR_INTERVAL_SOURCE_GIT_BLOB_MISMATCH'):load_author_loci(p)
 def test_locus_lookup(self):
  a,_,_=load_author_loci(L)
  by={'1A':sorted((x for x in a if x['chrom']=='1A'),key=lambda x:x['start_as_published'])}
  starts={'1A':[x['start_as_published'] for x in by['1A']]}
  self.assertEqual(find_interval(by,starts,'1A',33408202)['author_locus_number'],3)
  self.assertEqual(find_interval(by,starts,'1A',40877644)['author_locus_number'],7)
 def test_not_in_gap(self):
  a,_,_=load_author_loci(L);by={'1A':sorted((x for x in a if x['chrom']=='1A'),key=lambda x:x['start_as_published'])};starts={'1A':[x['start_as_published'] for x in by['1A']]}
  self.assertIsNone(find_interval(by,starts,'1A',37000000))
 def test_crosscheck_rejects_wrong_csv(self):
  a,_,_=load_author_loci(L)
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'x.csv';f.write_text('bad csv\n')
   with self.assertRaisesRegex(ValueError,'GIT_BLOB_MISMATCH'):checked_source_csv(f,a)
 def test_sha_git_blob(self):self.assertEqual(git_blob_sha(L.read_bytes()),'dc6ec1da23aa6426fcc16dc5b5d1124d55699616')
if __name__=='__main__':unittest.main()