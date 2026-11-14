import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from Bio import Phylo
import benchmark_frozen_adapter as m

ROOT=Path(__file__).resolve().parent

class ExternalFrozenBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_nchar=m.NCHAR
        m.NCHAR=4
        cls.tree=Phylo.read(io.StringIO('((A,B),C);'),'newick')
        cls.rows={'A':list('0012'),'B':list('1112'),'C':list('002?')}

    @classmethod
    def tearDownClass(cls):
        m.NCHAR=cls.original_nchar

    def test_numeric_weight_is_unchanged(self):
        d=m.distances(self.tree)
        self.assertEqual(d['A']['B'],2)
        self.assertEqual(d['B']['A'],2)
        self.assertEqual(d['A']['A'],0)

    def test_nearest_never_reads_hidden_target(self):
        changed=copy.deepcopy(self.rows)
        changed['A']=list('????')
        self.assertEqual(m.nearest_predictions(self.rows,m.distances(self.tree))['A'],m.nearest_predictions(changed,m.distances(self.tree))['A'])

    def test_fitch_never_reads_hidden_target(self):
        changed=copy.deepcopy(self.rows)
        changed['A']=list('????')
        self.assertEqual(m.predictions(self.rows,self.tree)['A'],m.predictions(changed,self.tree)['A'])

    def test_weighted_never_reads_hidden_target(self):
        changed=copy.deepcopy(self.rows)
        changed['A']=list('????')
        d=m.distances(self.tree)
        self.assertEqual(m.trait_score(self.rows,d,None)['A'],m.trait_score(changed,d,None)['A'])

    def test_trivial_mode_deterministic_ties(self):
        self.assertEqual(m.mode(['2','1']), '1')
        self.assertEqual(m.mode(['2','2','0']), '2')

    def test_evaluation_reproducibility_without_fit(self):
        out=m.assess(self.rows,[self.tree]*4,n_perm=0)
        self.assertEqual(out['matrix']['characters'],4)
        self.assertEqual(out['matrix']['taxa'],3)
        self.assertEqual(out['matrix']['unambiguous_states'],11)
        self.assertIn('astra_topology_ensemble',out['evaluation'])
        self.assertIn('fitch_ensemble_fallback',out['evaluation'])

    def test_external_authenticity_manifest_frozen(self):
        evidence=json.loads((ROOT/'evidence_summary_v07.json').read_text())
        sha=hashlib.sha256((ROOT/'benchmark_frozen_adapter.py').read_bytes()).hexdigest()
        self.assertEqual(sha,'f42a15764dd7d85590f2d423f1f708f3f2681f8d05f7b5d6eedecb2afb04c445')
        self.assertEqual(sha,evidence['frozen_model']['adapter_script_sha256_locally_and_in_vercel'])
        self.assertEqual(len(m.TREE_SOURCES),4)

    def test_missing_source_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            m.parse_nexus('/tmp/this-file-does-not-exist-ast-dino-v07.nex')

if __name__=='__main__': unittest.main()