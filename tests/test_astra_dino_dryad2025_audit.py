"""Standard-library unit tests with deliberately synthetic samples and variants."""
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'validation'))
from astra_dino_dryad2025_audit import (
    EvidenceError,phenotypes,pca_samples,read_regions,read_vcf,
    join_samples,audit,ASSEMBLY
)

class DryadAuditTest(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.path=Path(self.dir.name)
        self.morph=self.path/'Morphometrics.txt'
        self.pca=self.path/'pPCAeigen.txt'
        self.vcf=self.path/'Prun64_3miss2mafNoZ_1.vcf.gz'
        self.intervals=self.path/'intervals.json'
        self.morph.write_text('AccNo\tSpecies\tIsland\tBeak_length\tBeak_height\tBeak_width\n123456\tfortis\tSanta Cruz\t12.5\t8.0\t7.2\n654321\tfuliginosa\tSanta Cruz\t10.0\t6.5\t4.5\n')
        self.pca.write_text('SampleID\tPopulation\tPC1\n123456_R1\tfortis_Z\t0.2\n654321_R1\tfuliginosa_Z\t-0.3\n')
        self.create_vcf()
        self.intervals.write_text(json.dumps({'assembly':ASSEMBLY,'coordinate_system':'1-based-closed','regions':[
          {'gene':'ALX1','assembly':ASSEMBLY,'contig':'chr1A','start':100,'end':200,'source':'synthetic_fixture_only'},
          {'gene':'HMGA2','assembly':ASSEMBLY,'contig':'chr1A','start':300,'end':400,'source':'synthetic_fixture_only'}]}))
    def tearDown(self):self.dir.cleanup()
    def create_vcf(self,assembly=ASSEMBLY):
        lines=['##fileformat=VCFv4.2',f'##reference={assembly}','##contig=<ID=chr1A,length=1000>',
          '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t123456_R1\t654321_R1',
          'chr1A\t150\t.\tA\tG\t99\tPASS\t.\tGT\t0/1\t1/1',
          'chr1A\t350\t.\tC\tT\t99\tPASS\t.\tGT\t./.\t0/0',
          'chr1A\t500\t.\tG\tA\t99\tPASS\t.\tGT\t0/1\t0/0']
        with gzip.open(self.vcf,'wt') as f:f.write('\n'.join(lines)+'\n')
    def test_strict_phenotypes(self):
        m,s=phenotypes(self.morph)
        self.assertEqual(len(m),2);self.assertEqual(s['rejected_rows'],0)
        self.assertEqual(m['123456']['traits']['Beak_width'],7.2)
    def test_crosswalk_only_candidates(self):
        m,_=phenotypes(self.morph);p=pca_samples(self.pca)
        out=join_samples(m,p,['123456_R1','654321_R1','NOT_FOUND'])
        self.assertEqual(out['candidate_pairs'],2)
        self.assertEqual(out['independently_verified_pairs'],0)
        self.assertEqual(len(out['samples_not_in_pca']),1)
    def test_duplicate_accno_rejected(self):
        with open(self.morph,'a') as f:f.write('123456\tfortis\tSanta Cruz\t12.5\t8.0\t7.2\n')
        with self.assertRaises(EvidenceError):phenotypes(self.morph)
    def test_wrong_reference_abstains(self):
        self.create_vcf(assembly='GCF_ANOTHER')
        result=read_vcf(self.vcf,read_regions(self.intervals))
        self.assertEqual(result['status'],'UNVERIFIED_ASSEMBLY')
        self.assertIsNone(result['variants_by_gene'])
    def test_variant_scan_on_pinned_reference(self):
        out=read_vcf(self.vcf,read_regions(self.intervals))
        self.assertEqual(out['status'],'SCANNED_HEADER_AND_INTERVALS_NOT_INDEPENDENTLY_REVIEWED')
        self.assertEqual(out['variants_by_gene'],{'ALX1':1,'HMGA2':1})
        self.assertEqual(out['genotype_calls_by_gene']['ALX1']['called_genotypes'],2)
        self.assertEqual(out['genotype_calls_by_gene']['HMGA2']['missing_genotypes'],1)
        self.assertEqual(out['observed_vcf_records'],3)
    def test_contig_mismatch_abstains_not_zero(self):
        d=json.loads(self.intervals.read_text());d['regions'][0]['contig']='chrX'
        self.intervals.write_text(json.dumps(d))
        result=read_vcf(self.vcf,read_regions(self.intervals))
        self.assertEqual(result['status'],'UNVERIFIED_CONTIG')
        self.assertIsNone(result['variants_by_gene'])
    def test_missing_interval_never_claims_zero(self):
        r=read_vcf(self.vcf)
        self.assertEqual(r['status'],'HEADER_ONLY_NO_INTERVALS')
        self.assertIsNone(r['variants_by_gene'])
    def test_reject_wrong_interval_assembly(self):
        d=json.loads(self.intervals.read_text());d['assembly']='GCF_OTHER'
        self.intervals.write_text(json.dumps(d))
        with self.assertRaises(EvidenceError):read_regions(self.intervals)
    def test_reject_incomplete_loci(self):
        d=json.loads(self.intervals.read_text());d['regions'].pop()
        self.intervals.write_text(json.dumps(d))
        with self.assertRaises(EvidenceError):read_regions(self.intervals)
    def test_full_audit_remains_partial(self):
        out=audit(self.morph,self.pca,self.vcf,self.intervals)
        self.assertEqual(out['status'],'PARTIAL')
        self.assertEqual(out['crosswalk']['independently_verified_pairs'],0)
        self.assertEqual(out['variants']['variants_by_gene']['ALX1'],1)

if __name__=='__main__':unittest.main()

# Added as a separate test case to exercise the actual command-line entrypoint.
class CLITest(unittest.TestCase):
    create_vcf = DryadAuditTest.create_vcf
    def setUp(self): DryadAuditTest.setUp(self)
    def tearDown(self): DryadAuditTest.tearDown(self)
    def test_subprocess_cli_outputs_partial_not_pass(self):
        import subprocess
        program=Path(__file__).parents[1]/'validation/astra_dino_dryad2025_audit.py'
        r=subprocess.run([sys.executable,str(program),'--morph',str(self.morph),
                '--pca',str(self.pca),'--vcf',str(self.vcf),'--intervals',str(self.intervals)],
                capture_output=True,text=True,check=False,timeout=15)
        self.assertEqual(r.returncode,0)
        payload=json.loads(r.stdout)
        self.assertEqual(payload['status'],'PARTIAL')
        self.assertEqual(payload['crosswalk']['independently_verified_pairs'],0)
        self.assertEqual(payload['variants']['variants_by_gene']['HMGA2'],1)
