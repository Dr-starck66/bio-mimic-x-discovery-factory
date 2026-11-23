import copy
import json
import unittest
from pathlib import Path
from vva_duration_registry import audit, evaluate

SAMPLE = json.loads((Path(__file__).parent/'data'/'vva_longitudinal_study_registry_20261123.json').read_text(encoding='utf8'))

class TestLiteratureSafety(unittest.TestCase):
    def test_registry_has_five_separate_families(self):
        self.assertEqual(audit(SAMPLE)['literature_study_families'],5)
    def test_no_real_data_complete(self):
        self.assertEqual(audit(SAMPLE)['strictly_eligible_dataset_count'],0)
    def test_report_refuses_regeneration_claim(self):
        self.assertFalse(audit(SAMPLE)['durable_structural_repair_proven'])
    def test_jacobsen_ecm_yes_but_uncontrolled(self):
        r=evaluate(SAMPLE['studies'][0])
        self.assertIn('SHAM_OR_PLACEBO_CONTROL_ABSENT',r['reasons'])
    def test_gaspar_longitudinal_lacks_quantitative_ecm(self):
        r=evaluate(SAMPLE['studies'][1])
        self.assertEqual(r['observed_cessation_months'],[1,3,6,12])
        self.assertIn('QUANTITATIVE_COLLAGEN_ELASTIN_MISSING',r['reasons'])
    def test_light_followup_not_new_cohort(self):
        self.assertEqual(len([s for s in SAMPLE['studies'] if s['cohort_family']=='LIGHT_NCT04619485']),1)
    def test_li_first_vs_last_time(self):
        self.assertIn('LAST_TREATMENT_TIME_ORIGIN_UNVERIFIED',evaluate(SAMPLE['studies'][3])['reasons'])
    def test_gse_rna_not_histo(self):
        self.assertIn('REPORTED_PAIRED_HISTOLOGY_ABSENT',evaluate(SAMPLE['studies'][4])['reasons'])
    def test_no_booster_gaps_cannot_be_assumed(self):
        self.assertIn('RE_TREATMENT_NOT_EXCLUDED',evaluate(SAMPLE['studies'][3])['reasons'])
    def test_duplicate_publication_family_rejected(self):
        d=copy.deepcopy(SAMPLE)
        s=copy.deepcopy(d['studies'][2]);s['id']='LIGHT_2026_DUPLICATE';d['studies'].append(s)
        with self.assertRaisesRegex(ValueError,'double-counting'):audit(d)
    def test_duplicate_study_id_rejected(self):
        d=copy.deepcopy(SAMPLE)
        d['studies'].append(copy.deepcopy(d['studies'][1]))
        with self.assertRaisesRegex(ValueError,'duplicated study id'):audit(d)
    def test_missing_observations_rejected(self):
        d=copy.deepcopy(SAMPLE['studies'][0]);del d['source_urls']
        with self.assertRaisesRegex(ValueError,'missing required'):evaluate(d)
    def test_duplicate_timepoints_rejected(self):
        d=copy.deepcopy(SAMPLE['studies'][1]);d['observations_after_last_treatment_months']=[1,3,3,6,12]
        with self.assertRaisesRegex(ValueError,'duplicate timepoints'):evaluate(d)
    def test_non_numeric_timepoint_rejected(self):
        d=copy.deepcopy(SAMPLE['studies'][1]);d['observations_after_last_treatment_months']=[1,3,'12']
        with self.assertRaisesRegex(ValueError,'invalid cessation'):evaluate(d)
    def test_synthetic_complete_dataset_only_eligibility(self):
        d=copy.deepcopy(SAMPLE['studies'][0]);d.update(comparison='sham',sham_or_placebo=True,
          histology_paired=True,quantitative_epithelium=True,quantitative_ecm=True,
          observations_after_last_treatment_months=[3,6,12],time_reference='last_treatment',
          post_treatment_biopsy_per_timepoint=True,any_booster_before_followup=False,
          participant_level_data_available_to_pipeline=True,participant_level_pairing_verified=True)
        self.assertTrue(evaluate(d)['independent_durability_dataset_eligible'])
        registry={'schema':SAMPLE['schema'],'studies':[d]}
        self.assertFalse(audit(registry)['durable_structural_repair_proven'])
    def test_synthetic_no_booster_fails(self):
        d=copy.deepcopy(SAMPLE['studies'][1]);d.update(comparison='sham',sham_or_placebo=True,
          quantitative_epithelium=True,quantitative_ecm=True,
          post_treatment_biopsy_per_timepoint=True,participant_level_data_available_to_pipeline=True,
          participant_level_pairing_verified=True,any_booster_before_followup=True)
        self.assertFalse(evaluate(d)['independent_durability_dataset_eligible'])
        self.assertIn('RE_TREATMENT_NOT_EXCLUDED',evaluate(d)['reasons'])

if __name__=='__main__':unittest.main(verbosity=2)
