import math
import unittest
from validation.dracosphere_model import calc, report, R_IN_M, R_OUT_M

class TransportTests(unittest.TestCase):
    def test_n0_control(self):
        self.assertAlmostEqual(calc(0,.2)['transport_relative_to_no_membranes'],1)
        self.assertAlmostEqual(calc(0,12)['inside_O2_fraction_of_outside'],.5)
    def test_high_permeability_negative_control(self):
        self.assertGreater(calc(20,1e9)['transport_relative_to_no_membranes'],.9999999)
    def test_bigger_number_of_membranes_reduces_flux(self):
        values=[calc(n,12)['transport_relative_to_no_membranes'] for n in (0,1,5,20,30)]
        self.assertTrue(all(a>b for a,b in zip(values,values[1:])))
    def test_higher_membrane_permeability_increases_flux(self):
        self.assertLess(calc(20,.2)['transport_relative_to_no_membranes'],calc(20,12)['transport_relative_to_no_membranes'])
    def test_da_zero_no_oxygen_sinks(self):
        self.assertAlmostEqual(calc(20,.2,da=0)['inside_O2_fraction_of_outside'],1)
    def test_bacterial_sink_reduce_internal_oxygen(self):
        self.assertLess(calc(20,12,da=2)['inside_O2_fraction_of_outside'], calc(20,12,da=1)['inside_O2_fraction_of_outside'])
    def test_negative_or_invalid_inputs_fail(self):
        for n,p in [(-1,1),(1,0),(1,-.1),(1,float('nan'))]:
            with self.assertRaises(ValueError): calc(n,p)
    def test_geometry_lamellae_fit(self):
        self.assertTrue(calc(20,12)['lamellae_fit_in_506nm_shell'])
        self.assertFalse(calc(200,12)['lamellae_fit_in_506nm_shell'])
    def test_radial_vs_planar_limit(self):
        delta=1e-9
        c=calc(20,12,R_IN_M,R_IN_M+delta)
        r=R_IN_M+delta/2
        D=2e-9; P=0.12
        planar=(delta/D)/(delta/D+20/P)
        self.assertAlmostEqual(c['transport_relative_to_no_membranes'],planar,delta=.0001)
    def test_scale_invariance_reaction(self):
        self.assertTrue(math.isfinite(calc(20,.2)['inside_O2_fraction_of_outside']))
        self.assertGreater(calc(20,.2)['inside_O2_fraction_of_outside'],0)
    def test_invalid_thin_shell_is_not_modelled(self):
        x=report()['shell_width_sensitivity']
        self.assertEqual([z['status'] for z in x if z['shell_width_nm']==77],['GEOMETRY_INVALID']*3)
    def test_report_has_negative_and_high_p_controls(self):
        x=report()
        self.assertTrue(x['not_a_biological_validation'])
        self.assertEqual(len(x['models']),20)
        self.assertEqual(len(x['shell_width_sensitivity']),9)

if __name__=='__main__': unittest.main()
