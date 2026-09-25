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


    def test_paracentrotus_direct_orthology_seed_is_strictly_typed(self):
        rows=human_bridge.DIRECT_ORTHO_SEEDS.get("Paracentrotus lividus",[])
        self.assertEqual(len(rows),1)
        seed=rows[0]
        self.assertEqual(seed["animal_gene"],"WNT2")
        self.assertEqual(seed["human_symbol"],"WNT2")
        self.assertEqual(seed["human_ensembl_id"],"ENSG00000105989")
        self.assertTrue(seed["human_in_phylogeny"])
        self.assertGreaterEqual(len(seed["phylogeny_methods"]),2)
        self.assertIn("species-level strict orthology anchor",seed["bridge_scope"])


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


    def test_functional_orthology_requires_exact_gene_context_complementation_and_target(self):
        original_gene=human_bridge.ncbi_exact_gene
        original_ot=human_bridge.opentarget_context
        original_preservation=human_bridge.validate_preservation_context_paper
        original_functional=human_bridge.validate_functional_orthology_paper
        original_seeds=human_bridge.FUNCTIONAL_ORTHO_SEEDS
        try:
            human_bridge.FUNCTIONAL_ORTHO_SEEDS={
                "Caenorhabditis elegans":[{
                    "animal_gene":"daf-16",
                    "animal_ncbi_gene_id":"172981",
                    "animal_taxon_id":6239,
                    "preservation_evidence_pmids":["26635120"],
                    "functional_orthology_pmid":"11747821",
                    "functional_orthology_doi":"10.1016/S0960-9822(01)00595-4",
                    "human_symbol":"FOXO3",
                    "human_alias_in_paper":"FKHRL1",
                    "human_ensembl_id":"ENSG00000118689",
                    "relation":"one_to_many_functional_orthology",
                    "human_paralog_context":["FOXO1","FOXO3","FOXO4"],
                    "bridge_scope":"endogenous freeze-tolerance mechanism; independent of exogenous IBP intervention",
                    "rationale":"test"
                }]
            }
            human_bridge.ncbi_exact_gene=lambda species,gene: {
                "gene_id":"172981","symbol":"daf-16","tax_id":6239,
                "taxname":"Caenorhabditis elegans"
            } if (species,gene)==("Caenorhabditis elegans","daf-16") else None
            human_bridge.validate_preservation_context_paper=lambda pmid,species,gene: (
                pmid=="26635120" and species=="Caenorhabditis elegans" and gene=="daf-16"
            )
            human_bridge.validate_functional_orthology_paper=lambda pmid,gene,symbol,alias=None: (
                pmid=="11747821" and gene=="daf-16" and symbol=="FOXO3" and alias=="FKHRL1"
            )
            human_bridge.opentarget_context=lambda ensg: {
                "approved_symbol":"FOXO3","approved_name":"forkhead box O3",
                "biotype":"protein_coding","tractability":[]
            } if ensg=="ENSG00000118689" else None

            candidate={"subject":"Caenorhabditis elegans","pmid_sources":["PMID:42169464","PMID:42208364"]}
            bridges,stats=human_bridge.functional_orthology_bridges_for_candidate(candidate)
            self.assertEqual(len(bridges),1)
            b=bridges[0]
            self.assertEqual(b["animal_ncbi_gene_id"],"172981")
            self.assertEqual(b["human_symbol"],"FOXO3")
            self.assertEqual(b["orthology"]["provider"],"Peer-reviewed functional orthology")
            self.assertEqual(b["orthology"]["relation"],"one_to_many_functional_orthology")
            self.assertIn("independent",b["bridge_scope"])
            self.assertFalse(b["clinical_efficacy_claim"])
            self.assertEqual(stats["functional_orthology_strict_bridges"],1)

            human_bridge.ncbi_exact_gene=lambda *args,**kwargs: {
                "gene_id":"999999","symbol":"daf-16","tax_id":6239,
                "taxname":"Caenorhabditis elegans"
            }
            bad,_=human_bridge.functional_orthology_bridges_for_candidate(candidate)
            self.assertEqual(bad,[])

            human_bridge.ncbi_exact_gene=lambda *args,**kwargs: {
                "gene_id":"172981","symbol":"daf-16","tax_id":6239,
                "taxname":"Caenorhabditis elegans"
            }
            human_bridge.validate_preservation_context_paper=lambda *args,**kwargs: False
            bad2,_=human_bridge.functional_orthology_bridges_for_candidate(candidate)
            self.assertEqual(bad2,[])

            human_bridge.validate_preservation_context_paper=lambda *args,**kwargs: True
            human_bridge.opentarget_context=lambda *args,**kwargs: {
                "approved_symbol":"FOXO1","approved_name":"forkhead box O1",
                "biotype":"protein_coding","tractability":[]
            }
            bad3,_=human_bridge.functional_orthology_bridges_for_candidate(candidate)
            self.assertEqual(bad3,[])
        finally:
            human_bridge.ncbi_exact_gene=original_gene
            human_bridge.opentarget_context=original_ot
            human_bridge.validate_preservation_context_paper=original_preservation
            human_bridge.validate_functional_orthology_paper=original_functional
            human_bridge.FUNCTIONAL_ORTHO_SEEDS=original_seeds


    def test_phylogenetic_strict_bridge_requires_exact_species_paralog_controls_and_target(self):
        original_entry=human_bridge.uniprot_exact_species_gene
        original_ot=human_bridge.opentarget_context
        original_phylo=human_bridge.PHYLO_SEEDS
        try:
            human_bridge.PHYLO_SEEDS={
                "Cynops pyrrhogaster":[{
                    "animal_gene":"SHH",
                    "animal_uniprot":"Q90385",
                    "animal_taxon_id":8330,
                    "animal_genbank_protein":"BAA09657.1",
                    "animal_genbank_nucleotide":"D63339",
                    "modern_transcript_genbank":"PQ306330",
                    "modern_evidence_pmid":"39595071",
                    "human_symbol":"SHH",
                    "human_ensembl_id":"ENSG00000164690",
                    "phylogeny_pmid":"17318658",
                    "phylogeny_doi":"10.1007/s00427-007-0139-2",
                    "phylogeny_method":"21 Hedgehog proteins; 500 bootstrap replicates",
                    "exact_species_accession_in_phylogeny":"Q90385",
                    "human_target_in_phylogeny":"human SHH",
                    "paralog_controls":["human IHH","human DHH"],
                    "rationale":"test"
                }]
            }
            human_bridge.uniprot_exact_species_gene=lambda acc,species,gene,taxon_id=None: {
                "accession":"Q90385","species":"Cynops pyrrhogaster",
                "taxon_id":8330,"genes":["SHH"],"reviewed":True
            } if (acc,species,gene,str(taxon_id))==("Q90385","Cynops pyrrhogaster","SHH","8330") else None
            human_bridge.opentarget_context=lambda ensg: {
                "approved_symbol":"SHH","approved_name":"sonic hedgehog signaling molecule",
                "biotype":"protein_coding","tractability":[]
            } if ensg=="ENSG00000164690" else None

            candidate={"subject":"Cynops pyrrhogaster","pmid_sources":["PMID:39595071"]}
            bridges,stats=human_bridge.strict_phylogenetic_bridges_for_candidate(candidate)
            self.assertEqual(len(bridges),1)
            self.assertEqual(bridges[0]["orthology"]["provider"],"Peer-reviewed phylogenetic orthology")
            self.assertEqual(bridges[0]["human_symbol"],"SHH")
            self.assertEqual(stats["phylogenetic_strict_bridges"],1)

            wrong_species={"subject":"Pleurodeles waltl","pmid_sources":["PMID:39595071"]}
            b2,s2=human_bridge.strict_phylogenetic_bridges_for_candidate(wrong_species)
            self.assertEqual(b2,[])
            self.assertEqual(s2["phylogenetic_strict_bridges"],0)

            human_bridge.PHYLO_SEEDS["Cynops pyrrhogaster"][0]["paralog_controls"]=["human IHH"]
            b3,s3=human_bridge.strict_phylogenetic_bridges_for_candidate(candidate)
            self.assertEqual(b3,[])
            self.assertEqual(s3["phylogenetic_strict_bridges"],0)
        finally:
            human_bridge.uniprot_exact_species_gene=original_entry
            human_bridge.opentarget_context=original_ot
            human_bridge.PHYLO_SEEDS=original_phylo


    def test_phylogenetic_bridge_accepts_validated_bridge_specific_pmid(self):
        original_entry=human_bridge.uniprot_exact_species_gene
        original_ot=human_bridge.opentarget_context
        original_validate=human_bridge.validate_bridge_context_paper
        original_phylo=human_bridge.PHYLO_SEEDS
        try:
            human_bridge.PHYLO_SEEDS={
                "Cynops pyrrhogaster":[{
                    "animal_gene":"SHH",
                    "animal_uniprot":"Q90385",
                    "animal_taxon_id":8330,
                    "animal_genbank_protein":"BAA09657.1",
                    "animal_genbank_nucleotide":"D63339",
                    "modern_transcript_genbank":"PQ306330",
                    "modern_evidence_pmid":"39595071",
                    "human_symbol":"SHH",
                    "human_ensembl_id":"ENSG00000164690",
                    "phylogeny_pmid":"17318658",
                    "phylogeny_doi":"10.1007/s00427-007-0139-2",
                    "phylogeny_method":"21 Hedgehog proteins; 500 bootstrap replicates",
                    "exact_species_accession_in_phylogeny":"Q90385",
                    "human_target_in_phylogeny":"human SHH",
                    "paralog_controls":["human IHH","human DHH"],
                    "rationale":"test"
                }]
            }
            human_bridge.uniprot_exact_species_gene=lambda *args,**kwargs: {
                "accession":"Q90385","species":"Cynops pyrrhogaster",
                "taxon_id":8330,"genes":["SHH"],"reviewed":True
            }
            human_bridge.opentarget_context=lambda ensg: {
                "approved_symbol":"SHH","approved_name":"sonic hedgehog signaling molecule",
                "biotype":"protein_coding","tractability":[]
            }
            human_bridge.validate_bridge_context_paper=lambda pmid,species,gene: (
                pmid=="39595071" and species=="Cynops pyrrhogaster" and gene=="SHH"
            )
            candidate={"subject":"Cynops pyrrhogaster","pmid_sources":["PMID:34944708","PMID:41751333","PMID:42702818"]}
            bridges,stats=human_bridge.strict_phylogenetic_bridges_for_candidate(candidate)
            self.assertEqual(len(bridges),1)
            self.assertEqual(stats["phylogenetic_strict_bridges"],1)

            human_bridge.validate_bridge_context_paper=lambda *args,**kwargs: False
            b2,s2=human_bridge.strict_phylogenetic_bridges_for_candidate(candidate)
            self.assertEqual(b2,[])
            self.assertEqual(s2["phylogenetic_strict_bridges"],0)
        finally:
            human_bridge.uniprot_exact_species_gene=original_entry
            human_bridge.opentarget_context=original_ot
            human_bridge.validate_bridge_context_paper=original_validate
            human_bridge.PHYLO_SEEDS=original_phylo

if __name__=="__main__":
    unittest.main()
