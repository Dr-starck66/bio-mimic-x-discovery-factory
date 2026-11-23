#!/usr/bin/env python3
"""Only synthetic fixtures for implementation checks; never publish as biological findings."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vva_repair_gate import analyze, validate, two_sided_permutation_p


def fixture(mode='null'):
    rows = []
    for arm in ('active', 'vehicle'):
        for n in range(8):
            sid=f'{arm}-{n}'
            pre={'epithelial_thickness_um':100+n,'barrier_teer_ohm_cm2':200+n,
                 'ecm_architecture_score':0.30 + n/1000, 'hydration_index':0.40,
                 'symptom_score':7.0}
            post=pre.copy()
            if arm == 'active' and mode == 'structure':
                post['epithelial_thickness_um']+=30
                post['barrier_teer_ohm_cm2']+=40
                post['ecm_architecture_score']+=0.25
            if arm == 'active' and mode == 'hydration':
                post['hydration_index']+=0.25
                post['symptom_score']-=3
            for time, metrics in [('pre', pre), ('post', post)]:
                rows.append({'subject_id':sid,'arm':arm,'timepoint':time,**metrics})
    return rows

class TestVvaGate(unittest.TestCase):
    def test_null_fails(self):
        out=analyze(fixture())
        self.assertEqual(out['classification'],'NO_CONCORDANT_STRUCTURAL_SIGNAL')
        self.assertFalse(out['biological_repair_proven'])
    def test_hydration_only_negative(self):
        out=analyze(fixture('hydration'))
        self.assertEqual(out['classification'],'HYDRATION_OR_SYMPTOMS_ONLY_NOT_STRUCTURAL_REPAIR')
    def test_large_structure_is_still_not_regeneration(self):
        out=analyze(fixture('structure'))
        self.assertEqual(out['classification'],'MULTIDOMAIN_STRUCTURAL_SIGNAL_NOT_REGENERATION_PROOF')
        self.assertFalse(out['clinical_efficacy_proven'])
        for x in ('epithelium','barrier','matrix'):
            self.assertLess(out['metrics'][x]['holm_p_three_core_endpoints'],0.05)
    def test_no_pseudoreplication(self):
        rows=fixture(); rows.append(rows[0].copy())
        with self.assertRaisesRegex(ValueError,'duplicate'):
            validate(rows)
    def test_missing_timepoint(self):
        rows=fixture(); rows.pop()
        with self.assertRaisesRegex(ValueError,'missing matched'):
            validate(rows)
    def test_nonfinite_rejected(self):
        rows=fixture();rows[1]['hydration_index']=float('nan')
        with self.assertRaisesRegex(ValueError,'nonfinite'):
            validate(rows)
    def test_nonblinded_score_not_auto_verified(self):
        out=analyze(fixture('structure'))
        self.assertTrue(any('blinded' in x for x in out['limitations']))
    def test_permutation_null(self):
        p, kind=two_sided_permutation_p([0,0,0,0,0,0],[0,0,0,0,0,0]);self.assertEqual(p,1)
        self.assertEqual(kind,'exact')
    def test_small_n_refused(self):
        rows=[r for r in fixture() if r['subject_id'] not in ('active-7','active-6','active-5')]
        with self.assertRaisesRegex(ValueError,'at least 6'):
            validate(rows)
    def test_arms_cannot_change(self):
        rows=fixture();rows[1]['arm']='vehicle'
        with self.assertRaisesRegex(ValueError,'both arms'):
            validate(rows)

if __name__ == '__main__':
    unittest.main(verbosity=2)
