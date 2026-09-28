import unittest

from factory.microclean_x_experiment_selector import build, load_inputs, score_experiment, features

class ExperimentSelectorTests(unittest.TestCase):
    def test_inputs_require_simulation_only_phase4(self):
        dt,_,lib=load_inputs()
        self.assertTrue(dt["simulation_only"])
        self.assertTrue(lib["policy"]["proposed_not_executed"])

    def test_selects_exactly_three_distinct_axes(self):
        report=build()
        selected=report["selected_experiments"]
        self.assertEqual(len(selected),3)
        axes=[x["primary_axis"] for x in selected]
        self.assertEqual(len(set(axes)),3)

    def test_no_false_execution_or_measurement_claim(self):
        report=build()
        self.assertEqual(report["physical_experiments_executed"],0)
        self.assertEqual(report["new_measured_results"],0)
        self.assertFalse(report["claims"]["experiments_have_been_run"])
        self.assertFalse(report["claims"]["results_are_known"])
        self.assertFalse(report["claims"]["safety_is_established"])
        self.assertTrue(all(x["status"]=="PROPOSED_NOT_EXECUTED" for x in report["selected_experiments"]))

    def test_selected_experiments_have_controls_and_kill_criteria(self):
        report=build()
        for x in report["selected_experiments"]:
            self.assertTrue(x["controls"])
            self.assertTrue(x["kill_criteria"])
            self.assertTrue(x["readouts"])
            self.assertTrue(x["pre_registration_requirements"])

    def test_eig_is_explicitly_proxy(self):
        report=build()
        for x in report["full_experiment_queue"]:
            self.assertIn("proxy",x["selection_semantics"])
            self.assertGreaterEqual(x["selection_metrics"]["expected_information_gain_proxy"],0)

    def test_cost_penalty_behaves(self):
        dt,composites,library=load_inputs()
        f=features(dt,composites)
        exp=dict(library["experiments"][0])
        low=dict(exp); low["cost_proxy"]=0.1
        high=dict(exp); high["cost_proxy"]=0.9
        self.assertGreater(
            score_experiment(low,f)["expected_information_gain_proxy"],
            score_experiment(high,f)["expected_information_gain_proxy"]
        )

if __name__=="__main__":
    unittest.main()
