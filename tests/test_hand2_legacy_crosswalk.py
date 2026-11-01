import gzip
import unittest
from validation.hand2_legacy_crosswalk import collect_gtf_proof,compile_receipt,LEGACY

class Hand2LegacyCrosswalkTests(unittest.TestCase):
    def test_unique_symbol_is_not_exact_ncbi_crosswalk(self):
        g=collect_gtf_proof(gzip.compress(
            (f'chr1\tx\tgene\t12\t100\t.\t+\t.\tgene_id "{LEGACY}"; gene_name "HAND2 [hs]";\n').encode()))
        self.assertEqual(g["status"],"UNIQUE_LEGACY_HAND2_SYMBOL_ANNOTATION")
        n={"status":"NCBI_AXOLOTL_TO_HUMAN_ORTHOLOGY_VERIFIED"}
        r=compile_receipt(g,n,"a"*64)
        self.assertEqual(r["decision"],"PARTIAL")
        self.assertEqual(r["legacy_id_to_modern_ncbi_gene_exact_identity"],"UNVERIFIED")
    def test_multiple_same_symbol_loci_fail_closed(self):
        s=(f'chr1\tx\tgene\t12\t100\t.\t+\t.\tgene_id "{LEGACY}"; gene_name "HAND2 [hs]";\n'
           'chr3\tx\tgene\t22\t150\t.\t-\t.\tgene_id "AMEX60DD000123"; gene_name "HAND2 [hs]";\n')
        g=collect_gtf_proof(gzip.compress(s.encode()))
        self.assertEqual(g["status"],"UNVERIFIED_MULTIPLE_OR_MISSING_LEGACY_ANNOTATION")
    def test_mixed_hand1_hand2_annotations_are_conflicting(self):
        g=collect_gtf_proof(gzip.compress(
            (f'chr3q\tx\tgene\t632140538\t632169448\t.\t+\t.\tgene_id "{LEGACY}"; gene_name "HAND1 [nr]|HAND2 [hs]";\n').encode()))
        self.assertEqual(g["status"],"CONFLICTING_HOMOLOGY_LABELS")
        self.assertEqual(g["alternative_homology_symbols"],["HAND1","HAND2"])
        r=compile_receipt(g,{"status":"NCBI_AXOLOTL_TO_HUMAN_ORTHOLOGY_VERIFIED"},"a"*64)
        self.assertEqual(r["legacy_annotation_status"],"UNVERIFIED")
        self.assertEqual(r["decision"],"UNVERIFIED")
        self.assertEqual(r["legacy_id_to_modern_ncbi_gene_exact_identity"],"UNVERIFIED")
    def test_another_gene_not_accepted(self):
        g=collect_gtf_proof(gzip.compress((f'chr1\tx\tgene\t12\t100\t.\t+\t.\tgene_id "{LEGACY}"; gene_name "HND2 [hs]";\n').encode()))
        self.assertNotEqual(g["status"],"UNIQUE_LEGACY_HAND2_SYMBOL_ANNOTATION")
    def test_without_ncbi_orthology_fail_closed(self):
        g=collect_gtf_proof(gzip.compress((f'chr1\tx\tgene\t12\t100\t.\t+\t.\tgene_id "{LEGACY}"; gene_name "HAND2 [hs]";\n').encode()))
        r=compile_receipt(g,{"status":"UNVERIFIED_NCBI_HUMAN_ORTHOLOGY"},"a"*64)
        self.assertEqual(r["decision"],"UNVERIFIED")
if __name__=="__main__":unittest.main()
