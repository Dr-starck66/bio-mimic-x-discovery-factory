import unittest

from factory.microclean_x_digital_twin import (
    load_inputs, predict, run, pareto_front, dominates
)

class DigitalTwinTests(unittest.TestCase):
    def test_inputs_are_simulation_only(self):
        _,assumptions=load_inputs()
        self.assertTrue(assumptions["simulation_only"])
        self.assertEqual(assumptions["model_class"],"dimensionless heuristic surrogate")

    def test_baseline_is_anchored_to_published_max(self):
        comp,assumptions=load_inputs()
        p={
            "dose_ratio":1.0,
            "contact_time_ratio":1.0,
            "magnetic_fraction_ratio":1.0,
            "surface_affinity_ratio":1.0,
            "pH_offset_from_reference":0.0,
            "matrix_complexity":0.0
        }
        for c in comp["candidates"]:
            v=predict(c,assumptions["architecture_priors"][c["id"]],p)
            self.assertAlmostEqual(v["predicted_removal_pct"],float(c["metrics"]["max_removal_pct"]),places=3)

    def test_extreme_matrix_increases_uncertainty_and_hurts_lower_bound(self):
        comp,assumptions=load_inputs()
        c=comp["candidates"][0]
        prior=assumptions["architecture_priors"][c["id"]]
        base={
            "dose_ratio":1.0,"contact_time_ratio":1.0,"magnetic_fraction_ratio":1.0,
            "surface_affinity_ratio":1.0,"pH_offset_from_reference":0.0
        }
        clean=predict(c,prior,{**base,"matrix_complexity":0.0})
        dirty=predict(c,prior,{**base,"matrix_complexity":1.0})
        self.assertGreater(dirty["uncertainty"],clean["uncertainty"])
        self.assertLess(dirty["lower_bound_removal_pct"],clean["lower_bound_removal_pct"])

    def test_chromium_prior_has_more_release_risk_than_pda_at_baseline(self):
        comp,assumptions=load_inputs()
        by={c["id"]:c for c in comp["candidates"]}
        p={
            "dose_ratio":1.0,"contact_time_ratio":1.0,"magnetic_fraction_ratio":1.0,
            "surface_affinity_ratio":1.0,"pH_offset_from_reference":0.0,"matrix_complexity":0.0
        }
        cr=predict(by["fe3o4_mil101cr"],assumptions["architecture_priors"]["fe3o4_mil101cr"],p)
        pda=predict(by["fe3o4_pda"],assumptions["architecture_priors"]["fe3o4_pda"],p)
        self.assertGreater(cr["release_risk_proxy"],pda["release_risk_proxy"])

    def test_report_simulates_thousands_without_false_promotion(self):
        report=run(600)
        self.assertEqual(report["total_variants_simulated"],3000)
        self.assertTrue(report["simulation_only"])
        self.assertEqual(report["safe_or_field_ready_promotions"],[])
        self.assertFalse(report["claims"]["physical_validation"])
        self.assertFalse(report["claims"]["measured_new_data"])
        self.assertEqual(len(report["global_shortlist"]),5)

    def test_pareto_logic(self):
        def item(rem,recovery,cycle,risk,complexity):
            return {
                "lower_bound_removal_pct":rem,
                "stress_test":{"recovery_proxy":recovery,"cycle10_retention_proxy":cycle,"release_risk_proxy":risk},
                "complexity_proxy":complexity,
                "robust_score":50
            }
        a=item(90,.9,.8,.2,.2)
        b=item(80,.8,.7,.3,.3)
        self.assertTrue(dominates(a,b))
        front=pareto_front([a,b])
        self.assertEqual(len(front),1)
        self.assertIs(front[0],a)

if __name__=="__main__":
    unittest.main()
