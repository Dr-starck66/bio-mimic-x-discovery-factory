from __future__ import annotations
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from umhet3_decomposition_v2 import (check_and_convert, gap,
                                     eligible_weight, coarsened_weight_match)


def row(site, year, tx, sex, t, mass, i):
    return {'id':f'{ {"1.0":"JL","2.0":"UM","3.0":"UT"}[site]}{year}{tx}{sex}{i:03}',
            'site':site,'year':year,'tx':tx,'sex':sex,'days':t,'bw':mass}


class Tests(unittest.TestCase):
    def setUp(self):
        rows=[]
        for s,offset in [('1.0',0),('2.0',30),('3.0',12)]:
            for year in (2005,2006,2009):
                for tx in ('0.0','1.0'):
                    for sex in ('0','1'):
                        for n in range(12):
                            # All sites share same 6-g weight bins, effects include sex gap
                            bw=25+(n%3)*6+(n//3)*.25
                            day=760+offset + (80 if sex=='0' else 0)-5*bw
                            rows.append(row(s,year,tx,sex,day,bw,n))
        self.rows=rows

    def test_known_gap(self):
        z=gap(self.rows,years=(2005,2006,2009))
        self.assertAlmostEqual(z['JL']['female_minus_male'],80)
        self.assertAlmostEqual(z['UM']['female_minus_male'],80)
    def test_shared_year_tx_composition(self):
        z=gap(self.rows,years=(2005,2006,2009))
        self.assertAlmostEqual(z['UM']['male']-z['JL']['male'],30)
    def test_swap_sexes_flips_sign(self):
        flip=[{**r,'sex':'1' if r['sex']=='0' else '0'} for r in self.rows]
        a=gap(self.rows, years=(2005,2006,2009)); b=gap(flip,years=(2005,2006,2009))
        self.assertAlmostEqual(a['JL']['female_minus_male'],-b['JL']['female_minus_male'])
    def test_controls_subset_works(self):
        z=gap(self.rows,years=(2005,2006,2009),treatment='0.0')
        self.assertGreater(z['JL']['n'],0)
    def test_wrong_sex_rejected(self):
        fake={**self.rows[0],'sex':'2'}
        with self.assertRaises(ValueError): check_and_convert([{'mouse_id':fake['id'],'sex_code':fake['sex'],'site_code':fake['site'], 'cohort_year':str(fake['year']),'treatment_code':fake['tx'], 'longevity_days':str(fake['days']), 'bw6':'33','bw12':'','bw18':'','bw24':''}])
    def test_wrong_prefix_rejected(self):
        fake={'mouse_id':'BAD1','sex_code':'0','site_code':'2.0','cohort_year':'2005.0','treatment_code':'0.0','longevity_days':'800','bw6':'35','bw12':'','bw18':'','bw24':''}
        with self.assertRaisesRegex(ValueError,'prefix'):check_and_convert([fake])
    def test_duplicate_id_rejected(self):
        src={'mouse_id':'JL01','sex_code':'0','site_code':'1.0','cohort_year':'2005.0','treatment_code':'0.0','longevity_days':'800','bw6':'35','bw12':'','bw18':'','bw24':''}
        with self.assertRaisesRegex(ValueError,'Duplicate'):check_and_convert([src,src])
    def test_nonfinite_rejected(self):
        src={'mouse_id':'JL01','sex_code':'0','site_code':'1.0','cohort_year':'2005.0','treatment_code':'0.0','longevity_days':'nan','bw6':'35','bw12':'','bw18':'','bw24':''}
        with self.assertRaisesRegex(ValueError,'Out-of-range'):check_and_convert([src])
    def test_missing_common_support_raises(self):
        rows=[r for r in self.rows if not(r['site']=='2.0' and r['sex']=='0' and r['year']==2005)]
        with self.assertRaisesRegex(ValueError,'support'):gap(rows,years=(2005,2006,2009))
    def test_weight_overlap_excludes_no_measure(self):
        extra={**self.rows[0],'id':'JL_extra','bw':None}
        self.assertEqual(len(eligible_weight(self.rows+[extra],sex='0')),len(eligible_weight(self.rows,sex='0')))
    def test_weight_matching_recovers_site_gap(self):
        m=coarsened_weight_match(self.rows,width=6,shift=0,min_per_site=3)
        self.assertAlmostEqual(m['UM_minus_JL_after'],30)
        self.assertEqual(m['n'],len(self.rows)//2)
    def test_weight_bin_origin_supported(self):
        result=coarsened_weight_match(self.rows,width=6,shift=3,min_per_site=3)
        self.assertGreater(result['n'],0)
    def test_no_overlap_fails(self):
        scattered=[{**r,'bw':r['bw']+ {'1.0':0,'2.0':80,'3.0':160}[r['site']]} for r in self.rows]
        with self.assertRaisesRegex(ValueError,'support'):
            coarsened_weight_match(scattered,width=5,shift=0,min_per_site=3)
    def test_truncated_gap_not_more_than_full(self):
        allv=gap(self.rows,years=(2005,2006,2009))
        cropped=gap(self.rows,years=(2005,2006,2009),trunc=200)
        self.assertAlmostEqual(cropped['JL']['female_minus_male'],0)
        self.assertAlmostEqual(allv['JL']['female_minus_male'],80)
    def test_filter_below_landmark(self):
        extra={**self.rows[0], 'id':'JL_early','sex':'1','days':170}
        self.assertEqual(len(eligible_weight(self.rows+[extra],'1')),len(eligible_weight(self.rows,'1')))

if __name__=='__main__':unittest.main()