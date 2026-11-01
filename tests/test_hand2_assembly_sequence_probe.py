import json
import unittest
from validation.hand2_assembly_sequence_probe import build_probe,parse_ucsc_window,parse_ncbi_gene_report,parse_assembly_chromosome_report,local_kmer_screen,reverse_complement

class Hand2AssemblyProbeTests(unittest.TestCase):
    def test_no_inference_from_matching_symbols(self):
        x=build_probe({"ncbi_gene_report":(json.dumps({"reports":[{"gene":{
            "gene_id":"138516365","symbol":"HAND2","tax_id":8296
        }}]}).encode(),{})}, {})
        self.assertEqual(x["old_locus_to_modern_gene_exact_sequence_identity"],"UNVERIFIED")
        self.assertEqual(x["resources"]["ncbi_gene_report"]["parsed"]["reported_symbol"],"HAND2")

    def test_obtained_old_dna_alone_not_crosswalk(self):
        res=parse_ucsc_window(json.dumps({"dna":"ACGT"*20}).encode())
        self.assertEqual(res["status"],"OLD_GENOME_WINDOW_FETCHED")
        self.assertEqual(res["base_count"],80)

    def test_invalid_sequence_disallowed(self):
        res=parse_ucsc_window(json.dumps({"error":"hub not found"}).encode())
        self.assertEqual(res["status"],"NO_VALID_SEQUENCE")

    def test_official_assembly_arm_maps_to_genbank_accession(self):
        row="chr3q\tassembled-molecule\t3q\tChromosome\tCM010932.2\t<>\tna\tPrimary Assembly\t1526800552\tna\n"
        x=parse_assembly_chromosome_report(row.encode())
        self.assertEqual(x["status"],"GENBANK_CHR3Q_MAPPING_VERIFIED")
        self.assertEqual(x["genbank_accession"],"CM010932.2")

    def test_wrong_arm_mapping_is_rejected(self):
        row="chr3q\tassembled-molecule\t3q\tChromosome\tCM010938.2\t<>\tna\tPrimary Assembly\t1526800552\tna\n"
        x=parse_assembly_chromosome_report(row.encode())
        self.assertEqual(x["status"],"MISMATCHED_CHR3Q_MAPPING")

    def test_reverse_complement_kmer_screen_is_not_exact_proof(self):
        dna="ACGTACGTACGTACGTTACGTACGTACGTACGTTTGGCCAA"
        x=local_kmer_screen(dna,reverse_complement(dna),k=15)
        self.assertGreater(x["shared_kmers_reverse"],0)
        self.assertTrue(x["not_exact_identity_proof"])

    def test_no_sources_fail_closed(self):
        x=build_probe({},{"ncbi":"timeout"})
        self.assertEqual(x["status"],"UNVERIFIED")
        self.assertEqual(x["old_locus_to_modern_gene_exact_sequence_identity"],"UNVERIFIED")
if __name__=="__main__":unittest.main()
