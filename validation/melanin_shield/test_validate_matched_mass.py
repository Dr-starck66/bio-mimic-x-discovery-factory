import math, unittest
import model
from validate_matched_mass import compare,record

class MatchedMass(unittest.TestCase):
    def test_pe_wins_all_scenarios_against_hypothetical_composite(self):
        self.assertTrue(all(not r['candidate_beats_pe_at_matched_mass'] for r in compare() if r['candidate']=='PLA_10pct_melanin'))
    def test_perfect_equal_mass(self):
        for r in compare(): self.assertIn(r['areal_mass_kg_m2'],(10.,100.))
    def test_density_invariance(self):
        orig=model.MATERIALS['PLA_10pct_melanin']['rho']
        try:
            at10=model.atten('PLA_10pct_melanin',1.,area_mass_kg_m2=10)
            model.MATERIALS['PLA_10pct_melanin']['rho']=orig*2
            at20=model.atten('PLA_10pct_melanin',1.,area_mass_kg_m2=10)
            self.assertAlmostEqual(at10['transmission_primary_frac'],at20['transmission_primary_frac'],places=14)
            self.assertAlmostEqual(at10['thickness_cm'],2*at20['thickness_cm'],places=14)
        finally: model.MATERIALS['PLA_10pct_melanin']['rho']=orig
    def test_mixed_coefficients_range(self):
        for e in model.NIST:
            lo=min(model.mu_over_rho('PLA',e),model.mu_over_rho('PLA_10pct_melanin',e))
            hi=max(model.mu_over_rho('PLA',e),model.mu_over_rho('PLA_10pct_melanin',e))
            self.assertLessEqual(lo,hi)
    def test_zero_mass(self):
        for mat in model.MATERIALS:
            self.assertAlmostEqual(model.atten(mat,1.,area_mass_kg_m2=0)['transmission_primary_frac'],1.)
    def test_more_mass_less_transmission(self):
        for mat in model.MATERIALS:
            for e in model.NIST:
                self.assertLess(model.atten(mat,e,area_mass_kg_m2=100)['transmission_primary_frac'], model.atten(mat,e,area_mass_kg_m2=10)['transmission_primary_frac'])
    def test_no_dosimetry_claim(self):
        r=record(); self.assertFalse(r['measurements_used']); self.assertFalse(r['dosimetry_or_space_shield_proven']); self.assertEqual(len(r['comparisons']),8)
    def test_source_beta_negative_preserved(self):
        self.assertIn('did not find improved beta shielding',record()['independent_negative_controls']['beta'])

if __name__=='__main__': unittest.main()
