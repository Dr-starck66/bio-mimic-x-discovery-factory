#!/usr/bin/env python3
"""Synthetic negative controls for ASTRA DINO Ω joint real-data auditor.
Real-data integrity and results are tested separately against authenticated originals.
"""
import math
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'validation'))
import astra_dino_alx1_hmga2_joint_real as a

class JointAuditTests(unittest.TestCase):
    def fake_data(self):
        samples=[f'{100000+i}_S{i}' for i in range(50)]+[f'SRR2275{i:04}' for i in range(14)]
        morph={str(100000+i):{'Beak_length':'15','Beak_height':'10','Beak_width':'8'} for i in range(50)}
        pca={s:{'Population':('P1' if i%2==0 else 'P2')} for i,s in enumerate(samples)}
        return samples,morph,pca

    def test_authorized_50_plus_14_rule(self):
        samples,m,p=self.fake_data()
        z=a.checked_pairs(samples,m,p)
        self.assertEqual(len(z),50)
        self.assertEqual({x['AccNo'] for x in z},set(m))

    def test_missing_morphometry_fails_closed(self):
        s,m,p=self.fake_data()
        del m['100012']
        with self.assertRaises(a.GateError):a.checked_pairs(s,m,p)

    def test_ambiguous_duplicate_sample_fails_closed(self):
        s,m,p=self.fake_data()
        s[49]=s[48]
        with self.assertRaises(a.GateError):a.checked_pairs(s,m,p)

    def test_bad_phenotype_fails_closed(self):
        s,m,p=self.fake_data()
        m['100018']['Beak_width']='nan'
        with self.assertRaises(a.GateError):a.checked_pairs(s,m,p)

    def test_gt_parsing(self):
        self.assertEqual(a.fields('0|1:9','GT:DP'),1)
        self.assertEqual(a.fields('1/1','GT'),2)
        self.assertEqual(a.fields('0/0','GT'),0)
        self.assertIsNone(a.fields('./.:11','GT:DP'))
        self.assertIsNone(a.fields('2/1','GT'))
        self.assertIsNone(a.fields('10','DP'))

    def test_reference_header_not_sufficient(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad.fa'
            path.write_text('>1A dna_sm:primary_assembly primary_assembly:Camarhynchus_parvulus_V1.1:1A:1:72438334:1 REF\nACGT\n')
            with self.assertRaises(a.GateError):a.reference_sequence(path)

    def test_wrong_original_hash_or_length_fails(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'Morphometrics.txt').write_text('tampered\n')
            with self.assertRaises(a.GateError):a.check_inputs(d)

    def test_collinear_joint_model_fails_closed(self):
        with self.assertRaises(a.GateError):a.r2([1.,2.,3.],[1.,2.,3.],[2.,4.,6.])

    def test_within_population_constant_degenerate(self):
        groups={'a':[0,1],'b':[2,3]}
        self.assertEqual(a.demean([2,2,4,4],groups),[0,0,0,0])

    def test_gene_score_rejects_monorphic_inputs(self):
        snps=[{'pos':7,'dosages':[0]*50},{'pos':13,'dosages':[1]*50}]
        with self.assertRaises(a.GateError):a.gene_score(snps,50)

    def test_gene_score_keeps_alt_frequency_variant(self):
        snps=[{'pos':7,'dosages':[0]*25+[2]*25},{'pos':13,'dosages':[2]*25+[0]*25}]
        vec,qc=a.gene_score(snps,50)
        self.assertEqual(len(qc),2)
        self.assertEqual(len(vec),50)
        self.assertTrue(all(math.isfinite(x) for x in vec))

    def test_joint_permutation_seed_is_deterministic(self):
        pairs=[{'population':f'P{i//10}','Beak_length':10+i%4,
                'Beak_height':5+(i*3)%7,'Beak_width':4+i%5} for i in range(50)]
        x=[math.sin(i) for i in range(50)]
        y=[math.cos(2*i) for i in range(50)]
        a1=a.permutation_test(pairs,x,y,100,20261114)
        a2=a.permutation_test(pairs,x,y,100,20261114)
        self.assertEqual(a1,a2)
        for stat in a1['endpoints'].values():
            self.assertTrue(0<=stat['familywise_empirical_p']<=1)
            self.assertTrue(0<=stat['within_population_r2']<=1)

if __name__=='__main__':unittest.main()
