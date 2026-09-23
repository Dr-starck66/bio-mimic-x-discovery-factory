import sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"factory"))
import human_bridge, control_plane

class TestHumanBridge(unittest.TestCase):
    def test_collect_human_orthologues(self):
        payload={"data":[{"homologies":[
            {"target":{"id":"ENSG00000141510","species":"homo_sapiens","perc_id":81.2}},
            {"target":{"id":"ENSMUSG00000059552","species":"mus_musculus","perc_id":77.0}}
        ]}]}
        got=human_bridge.collect_human_orthologues(payload)
        self.assertEqual([x["ensembl_id"] for x in got],["ENSG00000141510"])

    def test_species_resolution_uses_taxon_proof(self):
        candidate={"name":"Common label","taxon_proofs":[{"canonical_name":"Heterocephalus glaber"}]}
        idx={"heterocephalus glaber":"heterocephalus_glaber"}
        self.assertEqual(human_bridge.resolve_ensembl_species(candidate,idx),"heterocephalus_glaber")

    def test_verified_bridge_changes_gate_status(self):
        claim={"subject":"Heterocephalus glaber"}
        index={"Heterocephalus glaber":[{"human_ensembl_id":"ENSG00000141510","human_symbol":"TP53"}]}
        out=control_plane.human_translation_gate(claim,index)
        self.assertEqual(out["status"],"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED")
        self.assertTrue(out["animal_claim_not_promoted_to_human_efficacy"])

    def test_no_bridge_remains_unverified(self):
        out=control_plane.human_translation_gate({"subject":"Species alpha"},{})
        self.assertEqual(out["status"],"UNVERIFIED_HUMAN_BRIDGE")

    def test_trust_gate_rejects_missing_taxonomy(self):
        b={"portfolio":[
            {"name":"This review","sources":["PMID:1"]},
            {"name":"Ambystoma mexicanum","sources":["PMID:2"],"taxon_verified":True}
        ],"labs":[]}
        out=control_plane.trust_gate(b)
        self.assertEqual(len(out["accepted"]),1)
        self.assertEqual(out["accepted"][0]["name"],"Ambystoma mexicanum")
        self.assertEqual(len(out["rejected"]),1)

if __name__=="__main__":
    unittest.main()
