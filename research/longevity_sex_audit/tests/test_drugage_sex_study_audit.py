import csv, tempfile, unittest
from pathlib import Path
from analysis.drugage_sex_study_audit import pairs, studies, audit, bh, run, load

def r(sex='Female',effect='20',drug='X',dose='2ppm',study='123',species='Mus musculus'):
    return dict(compound_name=drug,species=species,strain='UM-HET3',dosage=dose,
      age_at_initiation='4 months',treatment_duration='until death',pubmed_id=study,
      gender=sex,avg_lifespan_change_percent=effect)

class DrugAgeTests(unittest.TestCase):
    def test_paired_difference(self):
        self.assertEqual(pairs([r(),r('Male','10')])[0]['delta_female_minus_male'],10)
    def test_dose_mismatch_excluded(self):
        self.assertEqual(pairs([r(),r('Male','10',dose='4ppm')]),[])
    def test_publication_mismatch_excluded(self):
        self.assertEqual(pairs([r(),r('Male','10',study='456')]),[])
    def test_repeated_measurement_not_falsely_independent(self):
        z=pairs([r(),r(effect='30'),r('Male','10')]);self.assertEqual(len(z),1)
        self.assertEqual(z[0]['delta_female_minus_male'],15)
    def test_unknown_and_missing_values_excluded(self):
        self.assertEqual(pairs([r('Unknown','22'),r('Male','10'),r(effect='')]),[])
    def test_pubmed_group(self):
        z=pairs([r(),r('Male','10'),r(drug='Y'),r('Male','15',drug='Y')])
        self.assertEqual(len(z),2);self.assertEqual(len(studies(z)),1)
        self.assertAlmostEqual(list(studies(z).values())[0],7.5)
    def test_all_zero_is_null(self):
        z=pairs([r(effect='0'),r('Male','0')]);v=audit(z,n_perm=100,n_boot=100)
        self.assertEqual(v['p_two_sided_study_sign_flip'],1.0)
        self.assertEqual(v['bootstrap_95pct_CI_over_study_means'],[0.0,0.0])
    def test_seeded_determinism(self):
        z=pairs([r(),r('Male','10'),r(study='456'),r('Male','25',study='456')])
        self.assertEqual(audit(z,n_perm=101,n_boot=101),audit(z,n_perm=101,n_boot=101))
    def test_bh(self):
        self.assertAlmostEqual(bh([0.01,0.04,0.2])[0],.03)
        self.assertAlmostEqual(bh([0.01,0.04,0.2])[1],.06)
    def test_csv_comma_quoted(self):
        data=[r(drug='a,b'),r('Male','10',drug='a,b')]
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'v.csv'
            with f.open('w',encoding='utf-8',newline='') as h:
                w=csv.DictWriter(h,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
            self.assertEqual(pairs(load(f))[0]['compound_name'],'a,b')
    def test_male_female_inversion(self):
        self.assertEqual(pairs([r(effect='10'),r('Male','20')])[0]['delta_female_minus_male'],-10)
    def test_run_no_false_clinical_conclusion(self):
        z=[r(),r('Male','10')];o=run(z,n_perm=100,n_boot=100)
        self.assertEqual(o['source_rows'],2)
        self.assertEqual(o['distinct_pubmed'],1)
        self.assertFalse(any(x.get('status')=='PASS_HUMAN_LONGEVITY' for x in o['species']))

if __name__=='__main__':unittest.main()