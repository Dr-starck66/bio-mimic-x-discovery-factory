import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"factory"))
from paracentrotus_aqp_genome_gate import evaluate_aqp3_genome_candidate

class TestParacentrotusAqpGenomeGate(unittest.TestCase):
    def base(self):
        return {"species":"Paracentrotus lividus","taxon_id":7656,"gene":"AQP3","human_symbol":"AQP3","human_ensembl_id":"ENSG00000165272","exact_species_sequence_id":"PLIV:candidate","paralogue_controls_pass":True,"orthology_provider":"OrthoDB v12","orthology_evidence_id":"orthology-record","open_targets_validated":True,"evidence_is_name_only":False,"evidence_is_similarity_only":False}
    def test_complete_chain_promotes(self):
        self.assertTrue(evaluate_aqp3_genome_candidate(self.base())["promotion_ready"])
    def test_incomplete_chains_fail_closed(self):
        for key,value in [("evidence_is_name_only",True),("evidence_is_similarity_only",True),("paralogue_controls_pass",False),("species","Strongylocentrotus purpuratus")]:
            x=self.base(); x[key]=value
            self.assertFalse(evaluate_aqp3_genome_candidate(x)["promotion_ready"])
if __name__=="__main__":
    unittest.main()
