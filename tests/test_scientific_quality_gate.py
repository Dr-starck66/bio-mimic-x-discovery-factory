import sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"organization"))
import lab_worker, committee

class TestScientificQualityGate(unittest.TestCase):
    def test_generic_prose_is_not_species(self):
        text="This review summarizes these findings. This study reports emerging evidence. Wound healing is discussed."
        self.assertEqual(lab_worker.latin_mentions(text),[])

    def test_real_binomials_survive_syntax_filter(self):
        got=lab_worker.latin_mentions("Ambystoma mexicanum and Heterocephalus glaber were studied.")
        self.assertIn("Ambystoma mexicanum",got)
        self.assertIn("Heterocephalus glaber",got)

    def test_committee_rejects_unverified_candidate(self):
        outs=[{"lab_id":"x","candidates":[
            {"name":"This review","sources":["P1"],"mechanisms":[],"genes":[],"arbiter":80,"priority":80,"challenge_flags":[],"annotation_support":False,"taxon_verified":False},
            {"name":"Ambystoma mexicanum","sources":["P2"],"mechanisms":["regeneration"],"genes":[],"arbiter":70,"priority":70,"challenge_flags":[],"annotation_support":False,"taxon_verified":True,"taxon_proof":{"provider":"GBIF"}}
        ]}]
        p=committee.cross_lab_portfolio(outs)
        self.assertEqual([x["name"] for x in p],["Ambystoma mexicanum"])
        self.assertTrue(p[0]["taxon_verified"])

    def test_annotation_support_cannot_replace_taxonomy(self):
        outs=[{"lab_id":"x","candidates":[
            {"name":"Insulin resistance","sources":["P1","P2"],"mechanisms":["metabolism"],"genes":[],"arbiter":90,"priority":90,"challenge_flags":[],"annotation_support":True,"taxon_verified":False}
        ]}]
        self.assertEqual(committee.cross_lab_portfolio(outs),[])

if __name__=="__main__":
    unittest.main()
