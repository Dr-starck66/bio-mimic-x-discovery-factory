import unittest,tempfile,pathlib,gzip
from validation.geo_pairing_audit import parse_human,audit,read_matrix
class Test(unittest.TestCase):
 def test_metadata_match(self):
  a=[{'gsm':'GSM1','title':'Methylation_HC1_sp2_Normal_Control_ox21_p6'}]
  b=[{'gsm':'GSM2','title':'HC1_sp2_Normal_Control_ox21_p6'}]
  r=audit(a,b);self.assertEqual(r['n_exact_metadata_pairs'],1);self.assertEqual(r['same_aliquot'],'UNVERIFIED')
 def test_passage_negative(self):
  a=[{'gsm':'GSM1','title':'Methylation_HC1_sp2_Normal_Control_ox21_p6'}]
  b=[{'gsm':'GSM2','title':'HC1_sp2_Normal_Control_ox21_p7'}]
  self.assertEqual(audit(a,b)['n_exact_metadata_pairs'],0)
 def test_duplicate_fail_closed(self):
  a=[{'gsm':'GSM1','title':'Methylation_HC1_sp2_Normal_Control_ox21_p6'},{'gsm':'GSM3','title':'Methylation_HC1_sp2_Normal_Control_ox21_p6'}]
  b=[{'gsm':'GSM2','title':'HC1_sp2_Normal_Control_ox21_p6'}]
  r=audit(a,b);self.assertEqual(len(r['duplicates_dnam']),1);self.assertEqual(r['n_exact_metadata_pairs'],0)
 def test_parse(self):
  self.assertIsNone(parse_human('Technical_replicate_sp2_Normal__ox21_p_150'))
 def test_matrix(self):
  with tempfile.TemporaryDirectory() as d:
   f=pathlib.Path(d)/'test.txt.gz'
   with gzip.open(f,'wt') as o:o.write('!Sample_geo_accession\t"GSM1"\n!Sample_title\t"HC1_sp2_Normal_Control_ox21_p6"\n')
   self.assertEqual(read_matrix(f)[0]['gsm'],'GSM1')
if __name__=='__main__':unittest.main()
