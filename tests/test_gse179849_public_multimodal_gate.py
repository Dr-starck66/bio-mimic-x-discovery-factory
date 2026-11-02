import gzip
import unittest

from validation.gse179849_public_multimodal_gate import (
    csv_inspect, norm_label, read_geo_matrix_metadata, join_series,
)

class PublicLifespanOrthogonalGateTests(unittest.TestCase):
    def test_modality_prefix_only(self):
        self.assertEqual(norm_label('Methylation_HC2_sp1_Normal_Control_ox21_p5'),
                         'HC2_sp1_Normal_Control_ox21_p5')
        self.assertEqual(norm_label('RNAseq_HC2_sp1_Normal_Control_ox21_p5'),
                         'HC2_sp1_Normal_Control_ox21_p5')
        self.assertNotEqual(norm_label('HC2_sp1_Normal_DEX_ox21_p5'),
                            norm_label('HC2_sp1_Normal_Control_ox21_p5'))

    def test_genuine_metadata_form_and_accessions(self):
        raw=('!Series_title\t"Test"\n'
             '!Sample_title\t"Methylation_HC1_sp1_Normal_Control_ox21_p6"\t"Methylation_HC2_sp1_Normal_Control_ox21_p9"\n'
             '!Sample_geo_accession\t"GSM5435111"\t"GSM5435112"\n')
        out=read_geo_matrix_metadata(gzip.compress(raw.encode()))
        self.assertEqual(len(out),2)
        self.assertEqual(out[0]['GSM'],'GSM5435111')
        self.assertEqual(out[1]['join_key'],'HC2_sp1_Normal_Control_ox21_p9')

    def test_strict_assay_titles_pair_but_never_aliquot(self):
        d=[{'GSM':'GSM5435111','join_key':'HC1_sp1_Normal_Control_ox21_p6'}]
        r=[{'GSM':'GSM5435888','join_key':'HC1_sp1_Normal_Control_ox21_p6'},
           {'GSM':'GSM5435889','join_key':'HC1_sp1_Normal_Control_ox21_p7'}]
        res=join_series(d,r)
        self.assertEqual(len(res),1)
        self.assertFalse(res[0]['same_physical_aliquot_verified'])
        self.assertEqual(res[0]['RNA_GSM'],'GSM5435888')

    def test_ambiguous_metadata_fails_closed(self):
        dna=[{'GSM':'GSM5435111','join_key':'HC1_sp1_Normal_Control_ox21_p6'},
             {'GSM':'GSM5435112','join_key':'HC1_sp1_Normal_Control_ox21_p6'}]
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            join_series(dna,[])

    def test_public_figshare_biomarker_metadata_not_faked_as_RNA(self):
        contents='donor,passage,DNAmAge,RNA_proxies\n'+'\n'.join('HC%d,%d,%d,2.0'%(i,i,i) for i in range(12))
        report=csv_inspect(contents.encode())
        self.assertEqual(report['rows'],12)
        self.assertIn('DNAmAge',report['aging_or_multiomic_columns'])
        self.assertFalse(report['real_transcriptomic_gene_matrix'])
        self.assertFalse(report['real_methylation_beta_matrix'])

if __name__=="__main__":unittest.main()
