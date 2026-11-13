#!/usr/bin/env python3
"""Structural fixtures ONLY — not biological evidence."""
from __future__ import annotations
import gzip
import io
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'validation'))
import cretostimogene_bcg_tpm as m

class TestPaired(unittest.TestCase):
 def test_actual_geo_metadata_partition(self):
  ids,d,counts=m.patient_deltas(np.ones((2,len(m.GEO_SAMPLE_TITLES))),list(m.GEO_SAMPLE_TITLES))
  self.assertEqual(len(m.GEO_SAMPLE_TITLES),35)
  self.assertEqual(len(counts),14)
  self.assertEqual(len(ids),12)
  self.assertEqual(sum(len(x) for x in [ids]),12)
  self.assertEqual(sum(v['pre'] for v in counts.values()),13)
  self.assertEqual(sum(v['post'] for v in counts.values()),22)
  self.assertEqual(counts['P-11']['pre'],0)
  self.assertEqual(counts['P-14']['post'],0)
 def test_patient_averaging(self):
  x=np.array([[1,3,5,15,31,7],[2,4,6,4,5,8]],dtype=float)
  ids,delta,c=m.patient_deltas(x,['P-1','P-2','P-3','P-1_1','P-2_1','P-3_1'])
  self.assertEqual(ids,['P-1','P-2','P-3'])
  self.assertAlmostEqual(delta[0,0],np.log2(16)-np.log2(2))
 def test_exact_signflip(self):
  self.assertAlmostEqual(m.exact_signflip_p(np.array([1,1,1])),0.25)
  self.assertAlmostEqual(m.exact_signflip_p(np.array([0,0,0])),1.)
 def test_bh(self):
  q=m.bh({'a':.01,'b':.03,'c':.4});self.assertAlmostEqual(q['a'],.03);self.assertAlmostEqual(q['b'],.045)
 def test_parse_matrix_and_exploratory_fixture(self):
  headers=['P-1','P-2','P-3','P-1_1','P-2_1','P-3_1'];genes=['CXADR','STAT1','IL26']
  txt='gene\t'+'\t'.join(headers)+'\n'+'\n'.join(f'{gene}\t'+ '\t'.join(str(float(v)) for v in vals) for gene,vals in zip(genes,[[1,2,3,4,8,4],[3,4,3,6,2,3],[0,0,0,0,0,0]]))+'\n'
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'fixture.txt.gz';path.write_bytes(gzip.compress(txt.encode()))
   ns,x,headers,qc=m.read_tpm(path)
   self.assertEqual(qc['columns'],6)
   report=m.analyze(ns,x,headers,{**qc,'source_accession':'FIXTURE'},boot=100)
   self.assertEqual(report['status'],'FIXTURE_ONLY')
   self.assertEqual(report['qc']['n_patients_with_pairs'],3)
   self.assertEqual(len(report['predeclared_gene_effects']),3)
 def test_fake_matrix_cannot_claim_geo_provenance(self):
  labels=['P-1','P-2','P-3','P-1_1','P-2_1','P-3_1']
  x=np.array([[1.,2.,3.,4.,5.,6.]])
  with self.assertRaisesRegex(ValueError,'GEO_COHORT_IDENTITY_GATE'):
   m.analyze(['CXADR'],x,labels,{'source_accession':'GSE244895'},boot=10)
 def test_metadata_audit_nonfabricated_patient_counts(self):
  r=m.sample_metadata_audit()
  self.assertEqual([r[k] for k in ('n_specimens','n_patients','n_pre','n_post','n_paired_patients')],[35,14,13,22,12])
  self.assertEqual(set(r['unpaired_ids']),{'P-11','P-14'})
  self.assertEqual(r['expression_matrix'],'NOT_ACQUIRED')
 def test_no_duplicated_samples(self):
  txt='gene\tP-1\tP-1\tP-2\tP-2_1\nCXADR\t0\t1\t2\t3\n'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'dups.gz';p.write_bytes(gzip.compress(txt.encode()))
   with self.assertRaises(ValueError):m.read_tpm(p)
 def test_nonfinite_rejected(self):
  txt='gene\tP-1\tP-2\tP-3\tP-1_1\nCXADR\t0\t1\t2\tnan\n'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.gz';p.write_bytes(gzip.compress(txt.encode()))
   with self.assertRaises(ValueError):m.read_tpm(p)

 def test_terminal_source_exception_is_sha_pinned(self):
  bad=[{'gene':'DEFB110','line':4641,'observed_columns':7}]
  self.assertEqual(m.validate_tail_quarantine(bad,4641,m.PINNED_GEO_SHA256,36),bad)
  for bad_input,last,digest,cols in [
   (bad,4641,'a'*64,36),
   (bad,4642,m.PINNED_GEO_SHA256,36),
   ([{'gene':'CXADR','line':4641,'observed_columns':7}],4641,m.PINNED_GEO_SHA256,36),
   (bad*2,4641,m.PINNED_GEO_SHA256,36),
   (bad,4641,m.PINNED_GEO_SHA256,35),
  ]:
   with self.assertRaisesRegex(ValueError,'GEO_SOURCE_INTEGRITY_GATE'):
    m.validate_tail_quarantine(bad_input,last,digest,cols)
 def test_malformed_midfile_is_rejected(self):
  txt='gene\tP-1\tP-2\tP-3\tP-1_1\nCXADR\t0\t1\t2\t3\nDEFB110\t2\t2\nSTAT1\t0\t1\t2\t3\n'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.gz';p.write_bytes(gzip.compress(txt.encode()))
   with self.assertRaisesRegex(ValueError,'GEO_SOURCE_INTEGRITY_GATE'):m.read_tpm(p)

 def test_exploratory_signatures_use_patient_level_averages(self):
  names=['CD8A','CD8B','CXCL9','CXCL10','CD68','CD163']
  samples=['P-1','P-2','P-3','P-1_1','P-2_1','P-3_1']
  x=np.array([[1,1,1,9,9,9],[1,1,1,9,9,9],[2,2,2,4,4,4],
              [2,2,2,4,4,4],[9,9,9,5,5,5],[9,9,9,5,5,5]],dtype=float)
  a=m.analyze(names,x,samples,{'source_accession':'FIXTURE'},boot=100)
  v=a['exploratory_two_gene_signature_effects']
  self.assertEqual(set(v),set(m.EXPLORATORY_SIGNATURES))
  self.assertAlmostEqual(v['T_CELL_CD8_PROXY']['mean_delta_log2_tpm1'],np.log2(10)-np.log2(2),places=6)
  self.assertEqual(v['T_CELL_CD8_PROXY']['two_sided_exact_signflip_p'],0.25)
  self.assertTrue(all(0<=vv['bh_fdr_within_three_proxy_signatures']<=1 for vv in v.values()))

if __name__=='__main__':unittest.main()
