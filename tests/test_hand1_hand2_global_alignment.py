import unittest
from validation.hand1_hand2_global_alignment import (
    align_window,check_input_bases,cigar_counts,global_window,summarize,calculate
)


class CigarTests(unittest.TestCase):
    def test_extended_cigar_operation_counts(self):
        self.assertEqual(cigar_counts("3=1X2I1D"),{"=":3,"X":1,"I":2,"D":1})

    def test_reject_invalid_extended_cigar(self):
        for bad in ("", "5M", "3=2Z", "2=BAD", None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):cigar_counts(bad)

    def test_reject_sequence_not_matching_source_sha(self):
        with self.assertRaisesRegex(ValueError,"sequence hash mismatch"):
            check_input_bases("hand1","A"*28850)

    def test_truncated_seq_rejected(self):
        with self.assertRaisesRegex(ValueError,"unexpected sequence length"):
            check_input_bases("historic","ACGT")


class ScientificBoundaryTests(unittest.TestCase):
    def test_local_candidate_is_never_promoted_to_exact_identity(self):
        case={"hand1":{"local":{"best":{"fraction_matching_in_alignment":0.981}}},
              "hand2":{"local":{"best":{"fraction_matching_in_alignment":0.356}}}}
        x=summarize(case)
        self.assertEqual(x["stronger_local_alignment"],"HAND1")
        self.assertEqual(x["old_locus_to_new_gene_exact_identity"],"UNVERIFIED")
        self.assertEqual(x["independent_curator_confirmation"],"UNVERIFIED")
        self.assertEqual(x["status"],"PARTIAL_LOCUS_CANDIDATE_COMPARISON")

    def test_failed_ncbi_fetch_never_becomes_proof(self):
        def offline(*args):
            raise ConnectionError("NCBI unavailable")
        out=calculate(fetcher=offline)
        self.assertEqual(out["status"],"PARTIAL_SOURCE_FAILURE")
        self.assertEqual(len(out["failed_sources"]),3)
        self.assertEqual(out["old_locus_to_new_gene_exact_identity"],"UNVERIFIED")

    def test_real_edlib_handles_both_strands_and_globally(self):
        try:import edlib
        except ImportError:self.skipTest("edlib installed for live alignment step")
        target="TTTACCGGACAGATTT"
        align=align_window("ACCGGACA",target,edlib)
        self.assertEqual(align["best"]["edit_distance"],0)
        self.assertEqual(align["best"]["counts"]["="],8)
        self.assertEqual(align["best"]["strand"],"+")
        global_hit=global_window("ACCGGACA","ACCGGACA",edlib)
        self.assertEqual(global_hit["edit_distance"],0)
        self.assertEqual(global_hit["matching_bases"],8)

    def test_reverse_complement_wins(self):
        try:import edlib
        except ImportError:self.skipTest("edlib installed for live alignment step")
        target="TTTACCGGACAGATTT"
        from validation.hand2_assembly_sequence_probe import reverse_complement
        q=reverse_complement("ACCGGACA")
        align=align_window(q,target,edlib)
        self.assertEqual(align["best"]["edit_distance"],0)
        self.assertEqual(align["best"]["strand"],"-")

if __name__=="__main__":
    unittest.main()
