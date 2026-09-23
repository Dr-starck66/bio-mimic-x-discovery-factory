import json, sys, unittest, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"organization"))
import lab_worker, committee

class TestV6Organization(unittest.TestCase):
    def test_all_labs_configured(self):
        labs=json.loads((ROOT/"organization"/"labs.json").read_text(encoding="utf-8"))
        self.assertEqual(len(labs),7)
        self.assertEqual(len({x["id"] for x in labs}),7)

    def test_evidence_and_skeptic_diverge(self):
        c={"paper_count":1,"citations":0,"mechanisms":[],"genes":[],"annotation_support":False}
        e=lab_worker.evidence_score(c); s=lab_worker.skeptic_score(c)
        self.assertNotEqual(e,s)

    def test_committee_cross_lab_boost(self):
        one=[
            {"lab_id":"a","candidates":[{"name":"Species alpha","sources":["P1"],"mechanisms":["DNA repair"],"genes":[],"arbiter":60,"priority":60,"challenge_flags":[],"annotation_support":True,"taxon_verified":True,"taxon_proof":{"provider":"GBIF","kingdom":"Animalia","match_type":"EXACT"}}]}
        ]
        two=[
            {"lab_id":"a","candidates":[{"name":"Species alpha","sources":["P1"],"mechanisms":["DNA repair"],"genes":[],"arbiter":60,"priority":60,"challenge_flags":[],"annotation_support":True,"taxon_verified":True,"taxon_proof":{"provider":"GBIF","kingdom":"Animalia","match_type":"EXACT"}}]},
            {"lab_id":"b","candidates":[{"name":"Species alpha","sources":["P2"],"mechanisms":["DNA repair"],"genes":[],"arbiter":60,"priority":60,"challenge_flags":[],"annotation_support":True,"taxon_verified":True,"taxon_proof":{"provider":"GBIF","kingdom":"Animalia","match_type":"EXACT"}}]}
        ]
        p1=committee.cross_lab_portfolio(one)
        p2=committee.cross_lab_portfolio(two)
        self.assertEqual(p2[0]["lab_count"],2)
        self.assertGreater(p2[0]["committee_score"],p1[0]["committee_score"])

    def test_credit_allocation_sums_100(self):
        p=[
            {"name":"A","committee_score":80,"labs":["x"]},
            {"name":"B","committee_score":20,"labs":["y"]}
        ]
        a=committee.allocate_credits(p,100)
        self.assertEqual(sum(x["research_credits"] for x in a),100)

    def test_challenge_cycle(self):
        outs=[{"lab_id":"a"},{"lab_id":"b"},{"lab_id":"c"}]
        pairs=committee.challenge_matrix(outs)
        self.assertEqual(len(pairs),3)
        self.assertTrue(all(x["proponent_lab"]!=x["challenger_lab"] for x in pairs))

if __name__=="__main__":unittest.main()
