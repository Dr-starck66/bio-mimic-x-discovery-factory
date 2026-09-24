import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"factory"))
import orthology_watch

class TestOrthologyWatch(unittest.TestCase):
    def target(self):
        return {
            "species":"Paracentrotus lividus",
            "gene":"AQP3",
            "human_symbol":"AQP3",
            "human_ensembl_id":"ENSG00000165272",
            "genome_assemblies":["GCA_984792215.1"],
            "promotion_rule":"strict only"
        }

    def claim(self):
        return {
            "subject":"Paracentrotus lividus",
            "status":"SUPPORTED",
            "pmid_sources":["PMID:1","PMID:2"]
        }

    def test_no_provider_bridge_stays_watching(self):
        r=orthology_watch.evaluate_target(self.target(),self.claim(),{"bridges":[]})
        self.assertEqual(r["status"],"WATCHING")
        self.assertFalse(r["promotion_ready"])
        self.assertEqual(r["strict_bridge_count"],0)

    def test_only_exact_strict_bridge_promotes(self):
        bridge={
            "animal_species":"Paracentrotus lividus",
            "animal_gene":"AQP3",
            "human_symbol":"AQP3",
            "human_ensembl_id":"ENSG00000165272",
            "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
            "clinical_efficacy_claim":False,
            "orthology":{"provider":"NCBI Ortholog"}
        }
        r=orthology_watch.evaluate_target(self.target(),self.claim(),{"bridges":[bridge]})
        self.assertTrue(r["promotion_ready"])
        self.assertEqual(r["status"],"PROMOTION_READY")
        self.assertEqual(r["strict_providers"],["NCBI Ortholog"])

    def test_near_or_wrong_gene_never_promotes(self):
        wrong=[
            {
                "animal_species":"Strongylocentrotus purpuratus",
                "animal_gene":"AQP3",
                "human_symbol":"AQP3",
                "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
                "clinical_efficacy_claim":False,
                "orthology":{"provider":"NCBI Ortholog"}
            },
            {
                "animal_species":"Paracentrotus lividus",
                "animal_gene":"AQP1",
                "human_symbol":"AQP1",
                "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
                "clinical_efficacy_claim":False,
                "orthology":{"provider":"NCBI Ortholog"}
            }
        ]
        r=orthology_watch.evaluate_target(self.target(),self.claim(),{"bridges":wrong})
        self.assertFalse(r["promotion_ready"])

    def test_celegans_is_explicitly_excluded(self):
        cfg=orthology_watch.load(orthology_watch.TARGETS,{})
        excluded={x["species"] for x in cfg.get("explicitly_not_targets",[])}
        self.assertIn("Caenorhabditis elegans",excluded)

if __name__=="__main__":
    unittest.main()
