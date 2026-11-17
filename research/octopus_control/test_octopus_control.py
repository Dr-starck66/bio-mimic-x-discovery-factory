import unittest
from octopus_control import Scenario, decide, scenarios, required_force, run, MIN_ENVELOPE

class TestOctopusControl(unittest.TestCase):
    def test_grid_size(self): self.assertEqual(len(scenarios()), 400)
    def test_determinism(self): self.assertEqual(run(), run())
    def test_invalid_mode(self):
        with self.assertRaises(ValueError): decide(Scenario(7,0,0), "unknown")
    def test_invalid_negative_aperture(self):
        with self.assertRaises(ValueError): decide(Scenario(-1,0,0), "staged")
    def test_invalid_negative_grip(self):
        with self.assertRaises(ValueError): decide(Scenario(8,0,-0.1), "staged")
    def test_invalid_offset(self):
        with self.assertRaises(ValueError): decide(Scenario(8,0,0,5), "staged")
    def test_geometry_no_magic(self):
        for mode in ("direct", "staged"):
            result = decide(Scenario(MIN_ENVELOPE-.1, 0, 1.5), mode)
            self.assertFalse(result.success)
            self.assertEqual(result.reason, "geometric_exclusion")
    def test_equal_force_when_no_anchor(self):
        s = Scenario(9, 0.5, 0)
        self.assertEqual(decide(s, "direct").available_force, decide(s, "staged").available_force)
    def test_no_grip_never_improves_success(self):
        for s in scenarios():
            if s.anchor_quality == 0:
                self.assertEqual(decide(s, "direct").success, decide(s, "staged").success)
    def test_steps_three_vs_four(self):
        self.assertEqual(decide(Scenario(8,0,1), "staged").steps, 3)
        self.assertEqual(decide(Scenario(7.9,0,1), "staged").steps, 4)
    def test_baseline_is_faster_on_wide_easy_case(self):
        s = Scenario(12,0,0)
        self.assertTrue(decide(s, "direct").success)
        self.assertLess(decide(s, "direct").time_units, decide(s,"staged").time_units)
    def test_staging_can_rescue_synthetic_case(self):
        s = Scenario(6,0.5,1.5,1)
        self.assertFalse(decide(s,"direct").success)
        self.assertTrue(decide(s,"staged").success)
    def test_strain_monotonicity(self):
        self.assertLessEqual(required_force(Scenario(9,0,0)),required_force(Scenario(5,0,0)))
    def test_anchoring_monotonicity(self):
        a=decide(Scenario(6,1,0),"staged")
        b=decide(Scenario(6,1,1),"staged")
        self.assertLessEqual(a.available_force,b.available_force)
    def test_all_pass_results_have_metrics(self):
        for s in scenarios():
            for mode in ("direct","staged"):
                result=decide(s,mode)
                if result.success:
                    self.assertIsNotNone(result.time_units)
                    self.assertGreater(result.effort_units,0)
                else:
                    self.assertIsNone(result.time_units)
    def test_summary_accounting(self):
        r,_=run()
        self.assertEqual(r["both_fail"]+r["both_success"]+r["direct_only_success"]+r["staged_only_success"],400)

if __name__ == "__main__": unittest.main()
