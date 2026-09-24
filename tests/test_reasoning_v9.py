import json, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"factory"))

import hypothesis_engine, debate_engine, experiment_planner, reasoning_engine, scientific_memory

PROGRAM={"id":"PRG-test","title":"Danio rerio"}
CLAIM={
    "subject":"Danio rerio",
    "status":"SUPPORTED",
    "pmid_sources":["PMID:1","PMID:2","PMID:2"],
    "sources":["PMID:1","PMID:2"],
    "mechanisms":["regeneration"],
    "genes":["VEGF"]
}
AUDIT={"flags":["correlation not causation"],"kill_criteria":["no reproducible phenotype"]}
CAUSAL={"counterfactual_tests":["compare close negative-control species"]}
BRIDGES=[{"animal_species":"Danio rerio","human_symbol":"VEGFA","human_ensembl_id":"ENSG00000112715"}]

class TestV9ScientificReasoning(unittest.TestCase):
    def test_hypotheses_are_falsifiable_not_facts(self):
        hs=hypothesis_engine.generate_hypotheses(PROGRAM,CLAIM,CAUSAL,BRIDGES)
        self.assertEqual(len(hs),3)
        self.assertEqual({h["status"] for h in hs},{"HYPOTHESIS"})
        self.assertTrue(all(h["prediction"] and h["falsifier"] for h in hs))
        self.assertTrue(all(h["clinical_efficacy_claim"] is False for h in hs))
        self.assertTrue(all(h["association_only"] is True for h in hs))

    def test_debate_is_adversarial_and_non_probabilistic(self):
        hs=hypothesis_engine.generate_hypotheses(PROGRAM,CLAIM,CAUSAL,BRIDGES)
        d=debate_engine.debate_hypotheses(hs,CLAIM,AUDIT,CAUSAL)
        self.assertEqual(len(d["ranked"]),len(hs))
        self.assertIn("correlation not causation",d["adversarial_flags"])
        self.assertTrue(all("not probability" in x["score_semantics"] for x in d["ranked"]))
        primary=next(x for x in d["ranked"] if x["kind"]=="PRIMARY_CAUSAL")
        self.assertEqual(primary["status"],"NEEDS_CAUSAL_EVIDENCE")
        self.assertNotIn(primary["hypothesis_id"],d["surviving_hypothesis_ids"])
        self.assertTrue(d["blocked_or_pending_hypothesis_ids"])

    def test_experiment_plans_are_explicitly_unexecuted(self):
        hs=hypothesis_engine.generate_hypotheses(PROGRAM,CLAIM,CAUSAL,BRIDGES)
        d=debate_engine.debate_hypotheses(hs,CLAIM,AUDIT,CAUSAL)
        plans=experiment_planner.plan_experiments(PROGRAM,CLAIM,hs,d,CAUSAL)
        self.assertTrue(plans)
        for p in plans:
            self.assertEqual(p["status"],"PROPOSED_NOT_EXECUTED")
            self.assertTrue(p["kill_criteria"])
            self.assertEqual(len(p["sha256"]),64)
            self.assertFalse(p["clinical_efficacy_claim"])

    def test_reasoning_dossier_is_reproducible_and_cautious(self):
        a=reasoning_engine.reason_program(PROGRAM,CLAIM,AUDIT,CAUSAL,BRIDGES)
        b=reasoning_engine.reason_program(PROGRAM,CLAIM,AUDIT,CAUSAL,BRIDGES)
        self.assertEqual(a["sha256"],b["sha256"])
        self.assertEqual(len(a["sha256"]),64)
        self.assertFalse(a["claims_established_truth"])
        self.assertFalse(a["experiments_executed"])
        self.assertFalse(a["clinical_efficacy_claim"])

    def test_scientific_memory_preserves_hypothesis_status(self):
        dossier=reasoning_engine.reason_program(PROGRAM,CLAIM,AUDIT,CAUSAL,BRIDGES)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"scientific_reasoning_memory.json"
            r1=scientific_memory.update_scientific_memory(path,[dossier])
            r2=scientific_memory.update_scientific_memory(path,[dossier])
            mem=json.loads(path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(r1["new_hypotheses"],1)
            self.assertEqual(r2["new_hypotheses"],0)
            self.assertTrue(mem["hypotheses"])
            self.assertTrue(all(x["status"]=="HYPOTHESIS" for x in mem["hypotheses"].values()))
            self.assertTrue(all(x["clinical_efficacy_claim"] is False for x in mem["hypotheses"].values()))

    def test_registry_contains_all_v9_bricks(self):
        reg=json.loads((ROOT/"factory"/"brick_registry.json").read_text(encoding="utf-8"))
        ids={x["id"] for x in reg["active"]}
        expected={"scientific-reasoning","hypothesis-engine","debate-engine","experiment-planner","scientific-memory"}
        self.assertTrue(expected.issubset(ids))
        self.assertEqual(len(ids),len(reg["active"]))

if __name__=="__main__":
    unittest.main()
