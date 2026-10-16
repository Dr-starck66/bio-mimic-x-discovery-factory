import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"lab"))
import runner

class TestBioMimic(unittest.TestCase):
    def test_latin_mentions_filters_noise(self):
        t="The axolotl Ambystoma mexicanum and Heterocephalus glaber show unusual traits."
        got=runner.latin_mentions(t)
        self.assertIn("Ambystoma mexicanum",got)
        self.assertIn("Heterocephalus glaber",got)

    def test_latin_mentions_rejects_prose_false_positives(self):
        mentions = runner.latin_mentions(
            "This review compares Wound healing. "
            "Synthetic fixture, Wnt pathways and Observational fibrosis are not species. "
            "Acomys cahirinus is a real comparative biology model."
        )
        self.assertIn("Acomys cahirinus", mentions)
        self.assertNotIn("This review", mentions)
        self.assertNotIn("Wound healing", mentions)
        self.assertNotIn("Synthetic fixture", mentions)
        self.assertNotIn("Observational fibrosis", mentions)
        self.assertNotIn("Wnt pathways", mentions)

    def test_mechanisms(self):
        got=runner.mechanisms("DNA repair and metabolic suppression may protect mitochondria.")
        self.assertIn("DNA repair",got)
        self.assertIn("metabolic suppression",got)

    def test_graph_dedup(self):
        g={"nodes":{},"edges":{}}
        runner.graph_add_node(g,"species:x","species","X")
        runner.graph_add_node(g,"species:x","species","X")
        self.assertEqual(len(g["nodes"]),1)
        runner.graph_add_edge(g,"a","b","r","PMID:1",1)
        runner.graph_add_edge(g,"a","b","r","PMID:1",1)
        self.assertEqual(len(g["edges"]),1)

    def test_duality_penalizes_weak_candidate(self):
        c={"paper_count":1,"citations":0,"mechanisms":[],"genes":[],
           "annotation_support":False,"ensembl_verified":False}
        self.assertLess(runner.evaluator_skeptic(c),60)

    def test_learning_updates(self):
        tracks=json.loads((ROOT/"lab"/"tracks.json").read_text(encoding="utf-8"))
        l=runner.init_learning(tracks)
        t=tracks[0]
        old=l["tracks"][t["id"]]["runs"]
        runner.update_learning(l,t,{"novel_species":2,"verified_species":1,
                                    "mechanism_density":1.5,"source_diversity":5})
        self.assertEqual(l["tracks"][t["id"]]["runs"],old+1)

if __name__=="__main__":
    unittest.main()
