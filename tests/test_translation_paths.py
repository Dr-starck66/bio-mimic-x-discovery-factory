import sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"factory"))
import translation_paths

class TestTranslationPaths(unittest.TestCase):
    def test_all_fallback_seeds_are_typed_and_sourced(self):
        allowed={
            "LITERATURE_SEQUENCE_HOMOLOGY",
            "CURATED_PROTEIN_HOMOLOGY",
            "FUNCTIONAL_CRYOPRESERVATION_INTERVENTION",
            "FUNCTIONAL_ICE_BINDING_PROTEIN_INTERVENTION"
        }
        self.assertEqual(set(translation_paths.TRANSLATION_SEEDS),{
            "Acomys cahirinus","Cynops pyrrhogaster",
            "Paracentrotus lividus","Caenorhabditis elegans"
        })
        for subject,seed in translation_paths.TRANSLATION_SEEDS.items():
            self.assertIn(seed.get("path_type"),allowed)
            self.assertTrue(seed.get("animal_evidence_pmids"))
            self.assertTrue(seed.get("caveat"))

    def test_functional_paths_are_not_orthology(self):
        for subject in ("Paracentrotus lividus","Caenorhabditis elegans"):
            seed=translation_paths.TRANSLATION_SEEDS[subject]
            self.assertTrue(seed["path_type"].startswith("FUNCTIONAL_"))
            self.assertNotIn("orthology",seed["path_type"].lower())

    def test_strict_and_fallback_metrics_are_separate(self):
        claims=[{"subject":"Danio rerio"},{"subject":"Acomys cahirinus"}]
        strict={"bridges":[{
            "animal_species":"Danio rerio","animal_gene":"VEGF",
            "human_ensembl_id":"ENSG00000112715","human_symbol":"VEGFA"
        }]}
        original=translation_paths.validate_fallback
        try:
            translation_paths.validate_fallback=lambda subject,seed: ({
                "subject":subject,"status":"VERIFIED",
                "path_type":"LITERATURE_SEQUENCE_HOMOLOGY",
                "human_ensembl_id":"ENSG00000136634",
                "clinical_efficacy_claim":False
            },None)
            out=translation_paths.build_translation_paths(claims,strict)
        finally:
            translation_paths.validate_fallback=original
        self.assertEqual(out["strict_orthology_candidates"],1)
        self.assertEqual(out["translation_verified_candidates"],2)
        self.assertEqual(out["strict_orthology_coverage_ratio"],0.5)
        self.assertEqual(out["translation_coverage_ratio"],1.0)
        self.assertEqual(out["status"],"PASS")

    def test_missing_fallback_never_becomes_verified(self):
        claims=[{"subject":"Unknown species"}]
        out=translation_paths.build_translation_paths(claims,{"bridges":[]})
        self.assertEqual(out["translation_verified_candidates"],0)
        self.assertEqual(out["status"],"PARTIAL")
        self.assertTrue(out["errors"])

if __name__=="__main__":
    unittest.main()
