import unittest
from validation.hand2_flank_synteny import (
    fasta_url, parse_fasta, reverse_complement, indexed_kmers, compare_flanks, evaluate
)

class Hand2FlankSyntenyTests(unittest.TestCase):
    def test_strand_orientation(self):
        self.assertEqual(reverse_complement("ACGTTN"), "NAACGT")
        self.assertEqual(reverse_complement(reverse_complement("ACGTACG")), "ACGTACG")

    def test_exact_kmers_exclude_N(self):
        self.assertEqual(indexed_kmers("AAANCCC", 3), {"AAA": 0, "CCC": 4})

    def test_ortholog_flank_has_correct_orientation(self):
        old = "ACGTTACGTATAGCTAGCTT"
        reversed_mod = "ACGTTACGTATAGCTAGCTT"
        modern = reverse_complement(reversed_mod)
        self.assertEqual(compare_flanks(old, reverse_complement(modern), 8)["shared_distinct_kmers"],
                         len(indexed_kmers(old, 8)))

    def test_nonmatching_negative_control(self):
        self.assertEqual(compare_flanks("AAAAAAAAAA", "CCCCCCCCCC", 5)["shared_distinct_kmers"], 0)

    def test_bad_fasta_accession_rejected(self):
        with self.assertRaises(ValueError):
            parse_fasta(b">WRONG:1-10\nAAAAAAAAAA\n", "CM010938.2", 1, 10)

    def test_bad_fasta_length_rejected(self):
        with self.assertRaises(ValueError):
            parse_fasta(b">CM010938.2:1-10\nAAAAAAA\n", "CM010938.2", 1, 10)

    def test_source_url_pins_coordinates(self):
        self.assertIn("seq_start=884789726", fasta_url("CM010938.2", 884789726, 884794725))

    def test_missing_window_fail_closed(self):
        with self.assertRaises(ValueError):
            evaluate({"old_left": "A" * 5000})

    def test_incorrect_window_length_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({"old_left": "A" * 20, "old_right": "A" * 5000,
                      "modern_left": "A" * 5000, "modern_right": "A" * 5000})

if __name__ == "__main__":
    unittest.main()
