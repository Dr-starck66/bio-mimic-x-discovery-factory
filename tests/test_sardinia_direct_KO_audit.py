"""Synthetic-only regression tests for Sardinian direct KO quantification."""
import csv
import tempfile
import unittest
from pathlib import Path
from validation.sardinia_direct_KO_audit import analyse, auc, manifest, read_ko_table


class DirectSardiniaKOTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root / "manifest.tsv"
        self.ko = self.root / "KO"
        self.ko.mkdir()
        fields = ["run_accession", "published_sample_id", "group",
                  "fastq_1_md5", "fastq_2_md5"]
        self.runs = []
        with self.manifest.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
            w.writeheader()
            for group, count, prefix in (("Centenarian", 19, "C"),
                                         ("Elderly", 23, "E"),
                                         ("Young", 17, "Y")):
                for i in range(count):
                    batch = ("ERR350" if
                             (i < 11 if group == "Centenarian" else
                              i < 22 if group == "Elderly" else i < 10)
                             else "ERR239")
                    run = f"{batch}{prefix}{i:03d}"
                    self.runs.append(run)
                    w.writerow({
                        "run_accession": run, "published_sample_id": f"{prefix}_{i}",
                        "group": group, "fastq_1_md5": "a"*32,
                        "fastq_2_md5": "b"*32,
                    })
                    bsh = (40 if group == "Centenarian" else 10) + i
                    (self.ko / (run + "_ko.tsv")).write_text(
                        f"# Gene Family\tsample_RPK\nK01442\t{bsh}\n"
                        f"K03553\t100\nK03043\t30\n"
                        f"K01442|g__foo\t3000\n", encoding="utf-8")

    def test_full_synthetic_run_and_provenance_boundaries(self):
        result = analyse(self.manifest, self.ko, repetitions=99)
        self.assertEqual(result["records"], 59)
        self.assertEqual(result["results"]["all_59_case_vs_elderly"]["bsh_auc"], 1)
        self.assertEqual(result["results"]["ERR350_batch_only"]["bsh_auc"], 1)
        self.assertFalse(result["matched_quantification_to_2026_reference_method"])
        self.assertFalse(result["biological_enzyme_activity_proven"])
        self.assertFalse(result["future_metabolic_prediction_proven"])

    def test_auc_ties(self):
        self.assertEqual(auc([2, 2], [1, 2]), .75)

    def test_missing_subject_file_fails(self):
        (self.ko / (self.runs[0] + "_ko.tsv")).unlink()
        with self.assertRaisesRegex(ValueError, "Missing measured KO file"):
            analyse(self.manifest, self.ko, repetitions=99)

    def test_missing_bsh_fails_closed(self):
        path = self.ko / (self.runs[0] + "_ko.tsv")
        path.write_text(path.read_text().replace("K01442\t40\n", ""), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Missing K01442"):
            read_ko_table(path)

    def test_zero_reference_fails(self):
        path = self.ko / (self.runs[0] + "_ko.tsv")
        path.write_text(path.read_text().replace("K03553\t100", "K03553\t0"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Zero recA"):
            read_ko_table(path)

    def test_nan_fails(self):
        path = self.ko / (self.runs[0] + "_ko.tsv")
        path.write_text(path.read_text().replace("K01442\t40", "K01442\tNaN"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Invalid K01442"):
            read_ko_table(path)

    def test_duplicate_groups_fails(self):
        self.manifest.write_text(
            self.manifest.read_text().replace("Centenarian", "Young", 1),
            encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Expected exactly 59"):
            manifest(self.manifest)

    def test_taxon_stratified_does_not_double_count(self):
        row = read_ko_table(self.ko / (self.runs[0] + "_ko.tsv"))
        self.assertEqual(row["K01442"], 40)

    def test_nonpositive_pseudocount_fails(self):
        with self.assertRaisesRegex(ValueError, "Epsilon"):
            analyse(self.manifest, self.ko, epsilon=0, repetitions=99)


if __name__ == "__main__":
    unittest.main()
