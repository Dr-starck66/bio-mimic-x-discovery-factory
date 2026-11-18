import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
sys.path.insert(0, str(Path(__file__).parent))
from umhet3_site_audit import validate, standardized_gaps, fit, complete_bw, bootstrap_male_models, permute_bw_within_strata


def row(id,site,sex,yr,tx,days,bw):
    return dict(mouse_id=id,site_code=site,sex_code=sex,cohort_year=yr,treatment_code=tx,longevity_days=str(days),bw6=str(bw),bw12='',bw18='',bw24='')

class SiteAuditTests(unittest.TestCase):
    def setUp(self):
        self.data=[]
        for site,prefix,effect in [('1.0','JL',0),('2.0','UM',20),('3.0','UT',10)]:
            for yr in ['2005.0','2006.0','2009.0']:
                for tx in ['0.0','1.0']:
                    for sex in ['0','1']:
                        for i in range(12):
                            wt=28+(sex=='1')*10+(site=='1.0')*3+i/3
                            lifespan=700+effect+(sex=='0')*70-8*wt+int(float(yr))-2005+(tx=='1.0')*8
                            self.data.append(row(f'{prefix}{site[0]}{yr[:4]}{tx[0]}{sex}{i:03d}',site,sex,yr,tx,lifespan,wt))
    def test_valid_unique_ids_and_site_names(self):
        self.assertEqual(validate(self.data)['unique_ids'],len(self.data))
    def test_duplicate_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            validate(self.data + [self.data[0]])
    def test_site_prefix_is_validated(self):
        d=[{**self.data[0],"site_code":"2.0"}]+self.data[1:]
        with self.assertRaisesRegex(ValueError,'Site label'):
            validate(d)
    def test_sex_and_treatment_are_validated(self):
        d=[{**self.data[0],"sex_code":"Unknown"}]+self.data[1:]
        with self.assertRaisesRegex(ValueError,'Unrecognized'):
            validate(d)
    def test_nonfinite_lifespan_rejected(self):
        d=[{**self.data[0],"longevity_days":"nan"}]+self.data[1:]
        with self.assertRaisesRegex(ValueError,'Out-of-range'):
            validate(d)
    def test_standardization_has_expected_sign(self):
        gaps=standardized_gaps(self.data,years=('2005.0','2006.0','2009.0'))
        self.assertAlmostEqual(gaps['JL']['female_minus_male_days'],150.0,delta=0.001)
    def test_weight_negatively_associated_with_lifespan(self):
        male=complete_bw(self.data,'1')
        self.assertAlmostEqual(fit(male,True)['bw6_days_per_gram'],-8.0,delta=0.001)
    def test_predictable_site_covariate(self):
        male=complete_bw(self.data,'1')
        self.assertAlmostEqual(fit(male,True)['UM_minus_JL'],20.0,delta=0.001)
    def test_swap_sex_reverses_standardized_delta(self):
        before=standardized_gaps(self.data,years=('2005.0','2006.0','2009.0'))
        swapped=[{**r,'sex_code':'1' if r['sex_code']=='0' else '0'} for r in self.data]
        after=standardized_gaps(swapped,years=('2005.0','2006.0','2009.0'))
        self.assertAlmostEqual(before['JL']['female_minus_male_days'],-after['JL']['female_minus_male_days'])
    def test_missing_support_is_rejected(self):
        d=[r for r in self.data if not(r['site_code']=='2.0' and r['cohort_year']=='2005.0' and r['sex_code']=='0')]
        with self.assertRaisesRegex(ValueError,'No shared support'):
            standardized_gaps(d,years=('2005.0','2006.0','2009.0'))
    def test_bootstrap_is_finite(self):
        male=complete_bw(self.data,'1')
        r=bootstrap_male_models(male,5)
        self.assertEqual(len(r['slope']),2)
    def test_permutation_runs(self):
        male=complete_bw(self.data,'1')
        r=permute_bw_within_strata(male,10)
        self.assertEqual(r['n_perm'],10)
        self.assertTrue(0<r['one_sided_p']<=1)

if __name__=='__main__': unittest.main()