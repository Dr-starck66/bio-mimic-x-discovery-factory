import csv
import tempfile
import unittest
import zipfile
from pathlib import Path
from vendor_probe_bridge import convert,read_map
A='ACGTACGTACGTACGTACGTACGTA'
B='TGCATGCATGCATGCATGCATGCAT'
class TestThermoBridge(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.d=Path(self.t.name);self.z=self.d/'vendor.zip';self.dst=self.d/'out'
        self.make_zip([('17200001','1','2',A),('17200001','1','3',B)])
    def tearDown(self):self.t.cleanup()
    def make_zip(self,rows):
        t='Probe Set Name\tProbe X\tProbe Y\tProbe Interrogation Position\tProbe Sequence\tTarget Strandedness\n'
        t+=''.join('\t'.join([ps,x,y,'13',seq,'sense'])+'\n' for ps,x,y,seq in rows)
        with zipfile.ZipFile(self.z,'w') as f:f.writestr('MoGene-2_0-st-v1-mm10-probe-tab.txt',t)
    def test_realistic_format(self):
        r=convert(self.z,self.dst);self.assertEqual(r['probe_rows'],2)
        self.assertEqual(r['unique_sequences'],2)
        with (self.dst/'gpl16570_probes.tsv').open() as f:
            rows=list(csv.DictReader(f,delimiter='\t'))
        self.assertTrue(all(row['gene_id'].startswith('UNMAPPED_PROBESET_') for row in rows))
    def test_gene_annotation_with_authored_mapping(self):
        mapf=self.d/'mapping.tsv';mapf.write_text('probeset\tgene_id\n17200001\tCUSTOM_GENE_1\n')
        r=convert(self.z,self.dst,mapf);self.assertTrue(r['gene_annotation_complete'])
        self.assertEqual(len(r['gene_map_sha256']),64)
    def test_partial_gene_annotation_fails_closed(self):
        self.make_zip([('17200001','1','2',A),('17200002','1','3',B)])
        mapf=self.d/'mapping.tsv';mapf.write_text('probeset\tgene_id\n17200001\tGENE_1\n')
        r=convert(self.z,self.dst,mapf);self.assertFalse(r['gene_annotation_complete'])
        self.assertEqual(r['probesets_without_authoritative_gene_id'],1)
    def test_invalid_length_rejected(self):
        self.make_zip([('17200001','1','2','ACGT')])
        with self.assertRaisesRegex(ValueError,'invalid_25mer'):convert(self.z,self.dst)
    def test_invalid_base_rejected(self):
        self.make_zip([('17200001','1','2','N'+A[1:])])
        with self.assertRaisesRegex(ValueError,'invalid_25mer'):convert(self.z,self.dst)
    def test_duplicate_coordinates_rejected(self):
        self.make_zip([('17200001','1','2',A),('17200001','1','2',B)])
        with self.assertRaisesRegex(ValueError,'duplicate_probe_coordinates'):convert(self.z,self.dst)
    def test_no_probe_table_rejected(self):
        with zipfile.ZipFile(self.z,'w') as f:f.writestr('readme.txt','This is an unrelated file\n')
        with self.assertRaisesRegex(ValueError,'no_valid_vendor_probe_table'):convert(self.z,self.dst)
    def test_gene_map_duplicate_rejected(self):
        p=self.d/'m.tsv';p.write_text('probeset\tgene_id\na\t1\na\t2\n')
        with self.assertRaisesRegex(ValueError,'blank_or_duplicate'):read_map(p)
    def test_provenance_sha256(self):
        r=convert(self.z,self.dst);self.assertEqual(len(r['vendor_zip_sha256']),64)
        self.assertFalse(r['cross_species_probe_alignment_executed'])
        self.assertFalse(r['biological_replication_validated'])
if __name__=='__main__':unittest.main()
