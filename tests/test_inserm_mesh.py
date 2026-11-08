import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'factory'))
from inserm_mesh import ROLES, run, digest
MISSION=json.loads((ROOT/'examples'/'florence-apparailly-mission.json').read_text(encoding='utf-8'))

class TestInsermMesh(unittest.TestCase):
    def test_full_graph_and_no_fake_science(self):
        x=run(MISSION)
        self.assertEqual(len(x['agents']),len(ROLES))
        self.assertEqual(len(x['handoffs']),len(ROLES))
        self.assertEqual(x['summary']['biological_validation'],'UNVERIFIED')
        self.assertEqual(x['real_wetlab_experiments'],0)
        self.assertEqual(x['external_communication'],'DISABLED')
        self.assertEqual(x['summary']['technical_pipeline'],'PASS')
    def test_dag_and_hashes(self):
        x=run(MISSION)
        for e in x['handoffs']:
            self.assertEqual(e['input_hashes'],[x['agents'][d]['sha256'] for d in e['depends_on']])
        self.assertEqual(x['sha256'],digest({k:v for k,v in x.items() if k!='sha256'}))
        self.assertEqual(x,run(MISSION))
    def test_missing_evidence_fails_closed(self):
        x=run(MISSION)
        self.assertEqual(x['agents']['librarian']['status'],'UNVERIFIED')
        self.assertEqual(x['agents']['clinical_safety']['status'],'UNVERIFIED')
        self.assertEqual(x['agents']['partnership']['status'],'UNVERIFIED')
        self.assertEqual(x['agents']['quality']['status'],'UNVERIFIED')
    def test_no_duplicate_cohort_is_claimed(self):
        m=copy.deepcopy(MISSION); m['evidence']['independent_cohort_ids']=['one','one']
        x=run(m)
        self.assertNotEqual(x['agents']['cohorts']['status'],'PASS')
    def test_sensitive_human_data_blocked(self):
        m=copy.deepcopy(MISSION); m['contains_personal_health_data']=True
        x=run(m)
        self.assertEqual(x['agents']['privacy']['status'],'FAIL')
        self.assertEqual(x['agents']['partnership']['status'],'UNVERIFIED')
    def test_budget_fail_closed(self):
        m=copy.deepcopy(MISSION);m['authorized_additional_cost_eur']=9
        x=run(m)
        self.assertEqual(x['agents']['finance']['status'],'FAIL')
    def test_bad_mission_rejected(self):
        m=copy.deepcopy(MISSION);del m['question']
        with self.assertRaisesRegex(ValueError,'question'):run(m)
    def test_role_names_unique(self):
        ids=[r[0] for r in ROLES]
        self.assertEqual(len(ids),len(set(ids)))

if __name__=='__main__':unittest.main()
