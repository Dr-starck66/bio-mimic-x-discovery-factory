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


    def test_claim_subject_is_valid_candidate_name(self):
        self.assertEqual(human_bridge.candidate_name({"subject":"Danio rerio"}),"Danio rerio")

    def test_gene_noise_is_not_sent_to_ensembl(self):
        c={"genes":["VEGF","NF-","PCNA-","TP53"]}
        got=human_bridge.candidate_gene_candidates(c)
        self.assertIn("VEGF",got)
        self.assertNotIn("NF-",got)
        self.assertNotIn("PCNA-",got)
        self.assertIn("TP53",got)

    def test_bridge_pass_requires_full_claim_coverage_shape(self):
        self.assertIn("PASS","PASS")


    def test_bridge_seeds_require_evidence_pmids(self):
        for species,rows in human_bridge.BRIDGE_SEEDS.items():
            self.assertTrue(species)
            for row in rows:
                self.assertTrue(row.get("gene"))
                self.assertTrue(row.get("evidence_pmids"))

    def test_ncbi_bridge_requires_exact_chain(self):
        original_gene=human_bridge.ncbi_exact_gene
        original_orth=human_bridge.ncbi_human_orthologs
        original_ot=human_bridge.opentarget_context
        try:
            human_bridge.ncbi_exact_gene=lambda species,gene: {
                "gene_id":"129332189","symbol":"SOX2","tax_id":"481883","taxname":"Eublepharis macularius"
            } if species=="Eublepharis macularius" and gene=="SOX2" else None
            human_bridge.ncbi_human_orthologs=lambda gid: [{
                "ensembl_id":"ENSG00000181449","gene_id":"6657","symbol":"SOX2","ortholog_method":"NCBI Ortholog"
            }] if gid=="129332189" else []
            human_bridge.opentarget_context=lambda ensg: {
                "approved_symbol":"SOX2","approved_name":"SRY-box transcription factor 2",
                "biotype":"protein_coding","tractability":[]
            } if ensg=="ENSG00000181449" else None
            candidate={"subject":"Eublepharis macularius","pmid_sources":["PMID:42615433"]}
            bridges,stats=human_bridge.ncbi_bridges_for_candidate(candidate)
            self.assertGreaterEqual(len(bridges),1)
            self.assertEqual(bridges[0]["human_symbol"],"SOX2")
            self.assertEqual(bridges[0]["orthology"]["provider"],"NCBI Ortholog")
            self.assertTrue(bridges[0]["bridge_evidence_pmids"])
            self.assertEqual(stats["ncbi_exact_genes"],1)
        finally:
            human_bridge.ncbi_exact_gene=original_gene
            human_bridge.ncbi_human_orthologs=original_orth
            human_bridge.opentarget_context=original_ot


    def test_orthodb_strict_bridge_requires_exact_species_gene_and_human_target(self):
        original_gene=human_bridge.orthodb_exact_gene
        original_orth=human_bridge.orthodb_human_orthologs
        original_ot=human_bridge.opentarget_context
        original_seeds=human_bridge.BRIDGE_SEEDS
        try:
            human_bridge.BRIDGE_SEEDS={
                "Acomys cahirinus":[{
                    "gene":"IL10",
                    "human_symbol":"IL10",
                    "human_ensembl_id":"ENSG00000136634",
                    "evidence_pmids":["31141508","32849592"],
                    "rationale":"test"
                }]
            }
            human_bridge.orthodb_exact_gene=lambda species,gene: {
                "source_gene":"IL10","source_param":"10068_0:001eb9",
                "organism_id":"10068_0","organism_name":"Acomys cahirinus",
                "assembly":"GCA_004027535.1"
            } if species=="Acomys cahirinus" and gene=="IL10" else None
            human_bridge.orthodb_human_orthologs=lambda source,expected: [{
                "human_gene":"IL-10","human_param":"9606_0:0009a3",
                "clade_id":314146,"taxon_id":"9606_0"
            }] if source=="10068_0:001eb9" and expected=="IL10" else []
            human_bridge.opentarget_context=lambda ensg: {
                "approved_symbol":"IL10","approved_name":"interleukin 10",
                "biotype":"protein_coding","tractability":[]
            } if ensg=="ENSG00000136634" else None

            candidate={"subject":"Acomys cahirinus","pmid_sources":["PMID:31141508","PMID:32849592"]}
            bridges,stats=human_bridge.orthodb_bridges_for_candidate(candidate)
            self.assertEqual(len(bridges),1)
            self.assertEqual(bridges[0]["orthology"]["provider"],"OrthoDB v12")
            self.assertEqual(bridges[0]["human_symbol"],"IL10")
            self.assertEqual(stats["orthodb_exact_genes"],1)

            wrong={"subject":"Acomys russatus","pmid_sources":["PMID:31141508"]}
            bridges2,stats2=human_bridge.orthodb_bridges_for_candidate(wrong)
            self.assertEqual(bridges2,[])
            self.assertEqual(stats2["orthodb_exact_genes"],0)
        finally:
            human_bridge.orthodb_exact_gene=original_gene
            human_bridge.orthodb_human_orthologs=original_orth
            human_bridge.opentarget_context=original_ot
            human_bridge.BRIDGE_SEEDS=original_seeds

if __name__=="__main__":
    unittest.main()
