import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"factory"))
import program_director, policy_foundry, control_plane

class TestV7Factory(unittest.TestCase):
    def test_no_decorative_active_brick(self):
        reg=json.loads((ROOT/"factory"/"brick_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(reg["active"]),15)
        for b in reg["active"]:
            self.assertTrue(b["purpose"])
            self.assertTrue(b["inputs"])
            self.assertTrue(b["outputs"])
            self.assertTrue(b["metric"])
            self.assertTrue(b["entrypoint"])

    def test_mission_graph_is_ordered(self):
        p={"id":"P1"}
        g=control_plane.compile_mission_graph(p)
        self.assertGreater(len(g["nodes"]),10)
        self.assertEqual(len(g["edges"]),len(g["nodes"])-1)

    def test_policy_foundry_does_not_edit_code(self):
        p={"exploration_rate":0.2,"minimum_sources":2,"morpheus_penalty":0.2,"novelty_weight":0.3}
        vs=policy_foundry.propose_variants(p,{})
        self.assertTrue(vs)
        self.assertTrue(all("_variant" in v for v in vs))

    def test_immune_gate_blocks_high_false_positive(self):
        p={"exploration_rate":0.2,"minimum_sources":2,"morpheus_penalty":0.2,"novelty_weight":0.3}
        vs=policy_foundry.propose_variants(p,{})
        r=policy_foundry.select_safe_variant(p,vs,{"false_positive_rate":0.5,"verified_ratio":0.1,"cross_lab_diversity":0.2,"provider_success_ratio":1})
        self.assertFalse(r["accepted"])

    def test_negative_memory_blocks_exact_subject(self):
        claim={"subject":"Species alpha"}
        r=control_plane.apply_negative_memory(claim,[{"subject":"Species alpha"}])
        self.assertTrue(r["blocked"])

    def test_experiment_has_kill_criteria(self):
        p={"id":"P1"}
        c={"subject":"Species alpha","sources":["PMID:1"]}
        a={"kill_criteria":["stop"]}
        ca={"counterfactual_tests":["negative control"]}
        e=control_plane.forge_experiment(p,c,ca,a)
        self.assertTrue(e["kill_criteria"])
        self.assertEqual(len(e["sha256"]),64)


    def test_single_source_is_scout_not_claim(self):
        trusted={"accepted":[{"name":"Danio rerio","sources":["PMID:1"],"source_count":1,"mechanisms":["regeneration"],"labs":["regeneration"],"genes":["VEGF"],"taxon_verified":True,"taxon_proofs":[{"provider":"GBIF"}]}]}
        claims,scouts=control_plane.build_evidence_ledgers(trusted)
        self.assertEqual(claims,[])
        self.assertEqual(len(scouts),1)
        self.assertEqual(scouts[0]["status"],"SCOUT")

    def test_two_sources_becomes_supported_claim(self):
        trusted={"accepted":[{"name":"Danio rerio","sources":["PMID:1","PMID:2"],"source_count":2,"mechanisms":["regeneration"],"labs":["regeneration"],"genes":["VEGF"],"taxon_verified":True,"taxon_proofs":[{"provider":"GBIF"}]}]}
        claims,scouts=control_plane.build_evidence_ledgers(trusted)
        self.assertEqual(scouts,[])
        self.assertEqual(len(claims),1)
        self.assertEqual(claims[0]["status"],"SUPPORTED")

if __name__=="__main__": unittest.main()
