import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'research' / 'astra_obesity_omega' / 'mission.py'
spec = importlib.util.spec_from_file_location('astra_obesity_mission', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SEED = json.loads((MODULE_PATH.parent / 'research_seed.json').read_text(encoding='utf-8'))


class ResearchMissionTests(unittest.TestCase):
    def test_seed_valid(self):
        self.assertEqual(module.validate_seed(SEED), [])

    def test_deterministic_dossier_hash(self):
        a = module.build_dossier(SEED)
        b = module.build_dossier(SEED)
        self.assertEqual(a['sha256'], b['sha256'])
        self.assertEqual(a['sha256'], module.canonical_sha({k: v for k, v in a.items() if k != 'sha256'}))

    def test_existing_engines_generate_only_unverified_hypotheses(self):
        d = module.build_dossier(SEED)
        self.assertEqual(d['status'], 'PARTIAL')
        self.assertFalse(d['clinical_efficacy_demonstrated'])
        self.assertFalse(d['worldwide_solution_demonstrated'])
        self.assertEqual(len(d['research_questions']), 3)
        self.assertEqual(sum(len(q['hypotheses']) for q in d['research_questions']), 6)
        for q in d['research_questions']:
            self.assertEqual(len(q['hypotheses']), 0 if q['research_mode'] == 'CLASSIFICATION' else 3)
            self.assertTrue(all(h['association_only'] and not h['clinical_efficacy_claim'] for h in q['hypotheses']))
            self.assertTrue(all(p['status'] == 'PROPOSED_NOT_EXECUTED' for p in q['experiments']))
            if q['research_mode'] == 'MECHANISM':
                self.assertEqual(q['adversarial_review']['surviving_hypothesis_ids'], [])
            else:
                self.assertEqual(q['classification_benchmark']['baseline'], 'BMI_ALONE')
                self.assertEqual(q['experiments'], [])
            self.assertFalse(q['human_data_independently_analyzed'])

    def test_unattributed_source_rejected(self):
        s = copy.deepcopy(SEED)
        s['questions'][0]['source_ids'] = ['INVENTED-REFERENCE']
        self.assertIn('invalid_question_provenance:OB-CLASSIFICATION-01', module.validate_seed(s))
        self.assertEqual(module.build_dossier(s)['status'], 'FAIL')

    def test_no_clinical_efficacy_claim(self):
        s = copy.deepcopy(SEED)
        s['questions'][0]['claims_clinical_efficacy'] = True
        self.assertIn('clinical_efficacy_claim_forbidden:OB-CLASSIFICATION-01', module.validate_seed(s))

    def test_bmi_only_rejected(self):
        s = copy.deepcopy(SEED)
        s['questions'][0]['diagnostic_basis'] = 'BMI_ALONE'
        self.assertIn('bmi_alone_cannot_diagnose_clinical_obesity:OB-CLASSIFICATION-01', module.validate_seed(s))

    def test_no_personal_data(self):
        s = copy.deepcopy(SEED)
        s['questions'][1]['individual_data_present'] = True
        self.assertIn('individual_data_not_permitted:OB-DURABILITY-02', module.validate_seed(s))

    def test_duplicate_provenance_rejected(self):
        s = copy.deepcopy(SEED)
        s['questions'][1]['source_ids'].append(s['questions'][1]['source_ids'][0])
        self.assertIn('invalid_question_provenance:OB-DURABILITY-02', module.validate_seed(s))

    def test_missing_falsifier_rejected(self):
        s = copy.deepcopy(SEED)
        s['questions'][0]['falsifier'] = ''
        self.assertIn('missing_falsifier:OB-CLASSIFICATION-01', module.validate_seed(s))

    def test_unapproved_study_design_rejected(self):
        s = copy.deepcopy(SEED)
        s['sources'][0]['design'] = 'proven_cure'
        self.assertIn('unknown_study_design:WHO-OBESITY-2026', module.validate_seed(s))

    def test_fake_url_rejected(self):
        s = copy.deepcopy(SEED)
        s['sources'][0]['url'] = 'http://insecure.example'
        self.assertIn('source_url_not_https:WHO-OBESITY-2026', module.validate_seed(s))

    def test_no_fabricated_pmid(self):
        d = module.build_dossier(SEED)
        self.assertTrue(all(not h['source_pmids'] for q in d['research_questions'] for h in q['hypotheses']))


if __name__ == '__main__':
    unittest.main()
