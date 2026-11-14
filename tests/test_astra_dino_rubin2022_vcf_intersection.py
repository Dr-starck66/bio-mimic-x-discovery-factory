import sys,unittest,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'validation'))
from astra_dino_rubin2022_vcf_intersection import internal_controls,load_official_intervals,score_variant,find_oslo_pairs,GENES

class GateTests(unittest.TestCase):
  def test_gene_bodies_exact(self):
    self.assertEqual(GENES['ALX1'],('1A',40877644,40920855))
  def test_flank_width_matches(self):
    d={a['label']:a for a in internal_controls()}
    self.assertEqual(d['HMGA2_GENE_BODY']['end']-d['HMGA2_GENE_BODY']['start'],
                     d['HMGA2_RIGHT_EQUAL_WIDTH']['end']-d['HMGA2_RIGHT_EQUAL_WIDTH']['start'])
  def test_non_overlapping_flanks(self):
    d={a['label']:a for a in internal_controls()}
    self.assertEqual(d['ALX1_GENE_BODY']['end']+1,d['ALX1_RIGHT_EQUAL_WIDTH']['start'])
  def test_source_missing_rejected(self):
    with self.assertRaisesRegex(ValueError,'AUTHENTIC_DATA_S2_NOT_AVAILABLE'):
      load_official_intervals(None)
  def test_source_no_hash_rejected(self):
    with tempfile.TemporaryDirectory() as tmp:
      p=Path(tmp)/'x.json';p.write_text(json.dumps({'source_doi':'10.1126/sciadv.abm5982','assembly':'GCA_902806625.1','coordinate_convention':'1-based-inclusive','evidence_kind':'author_supplement_Data_S2','intervals':[{'locus':1,'chrom':'1A','start':1,'end':3},{'locus':2,'chrom':'1A','start':4,'end':5}]}))
      with self.assertRaisesRegex(ValueError,'DATA_S2_SOURCE_PDF_BYTES_REQUIRED'):load_official_intervals(p)
  def test_assembly_mismatch_rejected(self):
    with tempfile.TemporaryDirectory() as tmp:
      p=Path(tmp)/'x.json';p.write_text(json.dumps({'source_doi':'10.1126/sciadv.abm5982','assembly':'GCA_FAKE','coordinate_convention':'1-based-inclusive','evidence_kind':'author_supplement_Data_S2','source_pdf_sha256':'a'*64,'intervals':[]}))
      with self.assertRaisesRegex(ValueError,'DATA_S2_SOURCE_PDF_BYTES_REQUIRED'):load_official_intervals(p)
  def test_data_s2_inclusive_min_boundary(self):
    with tempfile.TemporaryDirectory() as tmp:
      p=Path(tmp)/'x.json';p.write_text(json.dumps({'source_doi':'10.1126/sciadv.abm5982','assembly':'GCA_902806625.1','coordinate_convention':'1-based-inclusive','evidence_kind':'author_supplement_Data_S2','source_pdf_sha256':'a'*64,'intervals':[{'locus':1,'chrom':'1A','start':100,'end':100},{'locus':2,'chrom':'1A','start':101,'end':200}]}))
      import hashlib
      pdf=Path(tmp)/'source.pdf';pdf.write_bytes(b'%PDF-1.4\n'+b'SYNTHETIC-TEST-DATA\n'*100)
      m=json.loads(p.read_text());m['source_pdf_sha256']=hashlib.sha256(pdf.read_bytes()).hexdigest()
      m['source_pdf_url']='https://pmc.ncbi.nlm.nih.gov/articles/PMC9269886/bin/sciadv.abm5982_sm.pdf'
      p.write_text(json.dumps(m))
      iv=load_official_intervals(p,pdf)
      self.assertEqual((iv[0]['start'],iv[0]['end']),(100,100))
  def test_pdf_sha_mismatch_rejected(self):
    with tempfile.TemporaryDirectory() as tmp:
      p=Path(tmp)/'x.json';pdf=Path(tmp)/'s.pdf';pdf.write_bytes(b'%PDF-1.4\n'+b'fixture'*200)
      p.write_text(json.dumps({'source_doi':'10.1126/sciadv.abm5982','assembly':'GCA_902806625.1','coordinate_convention':'1-based-inclusive','evidence_kind':'author_supplement_Data_S2','source_pdf_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC9269886/bin/sciadv.abm5982_sm.pdf','source_pdf_sha256':'a'*64,'intervals':[{'locus':1,'chrom':'1A','start':1,'end':3},{'locus':2,'chrom':'1A','start':4,'end':5}]}))
      with self.assertRaisesRegex(ValueError,'DATA_S2_SOURCE_PDF_SHA_MISMATCH'):load_official_intervals(p,pdf)
  def test_maf_filter_rejects_fixed(self):
    self.assertEqual(score_variant(['0/0']*50,'GT',list(range(50))),(True,False))
  def test_maf_filter_accepts_common(self):
    self.assertEqual(score_variant(['0/1']*50,'GT',list(range(50))),(True,True))
  def test_call_rate_rejected(self):
    self.assertEqual(score_variant(['./.']*11+['0/1']*39,'GT',list(range(50))),(True,False))

if __name__=='__main__':unittest.main()