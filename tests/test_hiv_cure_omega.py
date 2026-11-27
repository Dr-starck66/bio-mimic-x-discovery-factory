import json
import unittest
from copy import deepcopy
from pathlib import Path
from research.hiv_cure_omega.audit import audit_evidence

DATA = json.loads((Path(__file__).resolve().parents[1] / 'research/hiv_cure_omega/evidence.json').read_text(encoding='utf-8'))

class EvidenceTests(unittest.TestCase):
    def test_baseline(self):
        r = audit_evidence(DATA)
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(r['studies_checked'], 6)
        self.assertFalse(r['clinical_cure_proven'])

    def test_false_cure_claim_is_rejected(self):
        d = deepcopy(DATA)
        d['studies'][0]['eradication_demonstrated'] = True
        self.assertEqual(audit_evidence(d)['status'], 'FAIL')

    def test_no_general_cure_claim(self):
        d = deepcopy(DATA)
        d['cure_established_for_general_population'] = True
        self.assertEqual(audit_evidence(d)['status'], 'FAIL')

    def test_missing_source_is_rejected(self):
        d = deepcopy(DATA)
        d['studies'][1]['source'] = ''
        self.assertEqual(audit_evidence(d)['status'], 'FAIL')

    def test_unsafe_stop_is_rejected(self):
        d = deepcopy(DATA)
        d['clinical_safety']['art_stop_without_specialist_supervised_trial'] = 'ALLOWED'
        self.assertEqual(audit_evidence(d)['status'], 'FAIL')

    def test_duplicate_is_rejected(self):
        d = deepcopy(DATA)
        d['studies'][1]['id'] = d['studies'][0]['id']
        self.assertEqual(audit_evidence(d)['status'], 'FAIL')

if __name__ == '__main__':
    unittest.main()
