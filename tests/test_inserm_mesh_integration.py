import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'factory'))
from inserm_mesh import (run,digest,select_existing_program,ENGINE_BLOBS,verified_engine_fingerprints)
MISSION=json.loads((ROOT/'examples'/'florence-apparailly-validated-mission.json').read_text(encoding='utf-8'))
# Existing BIO-MIMIC X original state is preferred; in the isolated offline
# reproduction an exact extracted Acomys record is used, with original blob ID.
REAL_STATE=ROOT/'state'/'factory'/'programs.json'
FIXTURE=ROOT/'examples'/'acomys-existing-program-snapshot.json'
PROG_PATH=REAL_STATE if REAL_STATE.is_file() else FIXTURE
PROGRAM=select_existing_program(MISSION,PROG_PATH)

class TestRealBioMimicE2E(unittest.TestCase):
    def test_engines_are_original_git_blobs(self):
        actual=verified_engine_fingerprints()
        self.assertEqual(set(actual),set(ENGINE_BLOBS))
        self.assertTrue(all(v['status']=='PASS' for v in actual.values()))
    def test_full_pipeline_with_genuine_registered_program(self):
        out=run(MISSION,existing_program=PROGRAM)
        self.assertEqual(out['summary']['technical_pipeline'],'PASS')
        self.assertEqual(out['summary']['roles_executed'],23)
        self.assertEqual(len(out['scientific_artifacts']['hypotheses']),3)
        self.assertEqual(len(out['scientific_artifacts']['debate']['ranked']),3)
        self.assertEqual(len(out['scientific_artifacts']['plans']),2)
        self.assertTrue(all(h['clinical_efficacy_claim'] is False for h in out['scientific_artifacts']['hypotheses']))
        self.assertTrue(all(p['status']=='PROPOSED_NOT_EXECUTED' for p in out['scientific_artifacts']['plans']))
        self.assertEqual(out['existing_program']['id'],'PRG-c73037fcfb')
    def test_bibliography_negative_control_and_false_replicates(self):
        out=run(MISSION,existing_program=PROGRAM)
        a=out['bibliography_audit']
        self.assertEqual(a['supporting_primary_pmids'],['PMID:38228141','PMID:40534468'])
        self.assertEqual(a['negative_context_pmids'],['PMID:42194064'])
        self.assertEqual(a['review_pmids'],['PMID:41732917'])
        self.assertEqual(a['unverified_pmids'],['PMID:42792965'])
        self.assertEqual(a['independent_replications_of_same_mechanism'],'UNVERIFIED')
        self.assertEqual(out['existing_program']['original_source_count_claimed'],3)
        self.assertEqual(out['existing_program']['source_count_revalidated'],'UNVERIFIED')
        for h in out['scientific_artifacts']['hypotheses']:
            self.assertNotIn('PMID:41732917',h['source_pmids'])
            self.assertNotIn('PMID:42194064',h['source_pmids'])
            self.assertNotIn('PMID:42792965',h['source_pmids'])
        for b in out['scientific_artifacts']['debate']['ranked']:
            self.assertIn('negative context evidence must be kept',b['objections'])
            self.assertTrue(all('independent PMID-linked sources' not in txt for txt in b['evidence_support']))
    def test_zero_verified_support_never_converts_legacy_to_proof(self):
        m=copy.deepcopy(MISSION)
        m['evidence']['source_records']=[r for r in m['evidence']['source_records'] if r['study_role']!='SUPPORTING_PRIMARY']
        out=run(m,existing_program=PROGRAM)
        self.assertFalse(out['bibliography_audit']['supporting_primary_pmids'])
        for h in out['scientific_artifacts']['hypotheses']:
            self.assertEqual(h['source_pmids'],[])
        self.assertTrue(all(x['status']!='SURVIVES_AS_ALTERNATIVE' for x in out['scientific_artifacts']['debate']['ranked']))
    def test_disabled_engine_never_gets_pass(self):
        import inserm_mesh
        original=inserm_mesh.ENGINE_BLOBS.copy()
        try:
            inserm_mesh.ENGINE_BLOBS['hypothesis_engine']='0'*40
            out=run(MISSION,existing_program=PROGRAM)
            self.assertEqual(out['summary']['technical_pipeline'],'PARTIAL')
            self.assertEqual(out['engine_fingerprints']['hypothesis_engine']['status'],'MISMATCH')
        finally:
            inserm_mesh.ENGINE_BLOBS.clear()
            inserm_mesh.ENGINE_BLOBS.update(original)
    def test_bad_scientific_program_mapping_rejected(self):
        m=copy.deepcopy(MISSION)
        m['existing_program_id']='PRG-not-real'
        with self.assertRaisesRegex(ValueError,'missing or ambiguous'):
            select_existing_program(m,PROG_PATH)
        with self.assertRaisesRegex(ValueError,'Wrong scientific-program'):
            run(m,existing_program=PROGRAM)
    def test_hash_handoffs_reproducible(self):
        a=run(MISSION,existing_program=PROGRAM)
        b=run(MISSION,existing_program=PROGRAM)
        self.assertEqual(a['sha256'],b['sha256'])
        self.assertEqual(a['sha256'],digest({k:v for k,v in a.items() if k!='sha256'}))
        for handoff in a['handoffs']:
            self.assertEqual(handoff['output_hash'],a['agents'][handoff['role']]['sha256'])
            self.assertEqual(handoff['input_hashes'],[a['agents'][n]['sha256'] for n in handoff['depends_on']])
    def test_no_unauthorized_actions(self):
        a=run(MISSION,existing_program=PROGRAM)
        self.assertEqual(a['new_cost_eur'],0)
        self.assertEqual(a['new_scheduled_jobs'],0)
        self.assertEqual(a['external_communication'],'DISABLED')
        self.assertEqual(a['real_wetlab_experiments'],0)
        self.assertEqual(a['summary']['biological_validation'],'UNVERIFIED')
        self.assertEqual(a['summary']['institutional_partnership'],'UNVERIFIED')

if __name__=='__main__':unittest.main()
