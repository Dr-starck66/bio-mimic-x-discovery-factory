import csv
from pathlib import Path
import tempfile
import unittest
from validation.parkinson_thrombin_sequence_gate import (
    SEQ, parse_paired_csv, paired_sign_flip, run, sequence_audit,
)

COLUMNS=("experiment_id","assay","sample_id","condition","value","unit")

def make_rows():
    out=[]
    for n in range(3):
        for condition,value in (("intact_1_140",n),("truncated_7_140",n+1)):
            out.append(dict(experiment_id="SYNTHETIC_TEST_FIXTURE",assay="check",
                sample_id=str(n),condition=condition,value=str(value),unit="arb"))
    return out

def save(folder,rows):
    path=Path(folder)/"input.csv"
    with path.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS)
        w.writeheader();w.writerows(rows)
    return path

class ParkinsonGuardTests(unittest.TestCase):
    def test_reference_exact_cut(self):
        r=sequence_audit()
        self.assertEqual(r["status"],"PASS_SEQUENCE_CHECK_ONLY")
        self.assertEqual(len(SEQ),140)
        self.assertEqual(SEQ[5:7],"KG")
        self.assertEqual(r["removed"],"MDVFMK")
        self.assertEqual(r["length_fragment"],134)

    def test_mass_is_theoretical(self):
        r=sequence_audit()
        self.assertAlmostEqual(r["mass_theoretical_unmodified_Da"]["difference"],751.339703,places=5)
        self.assertIn("Theoretical",r["warning"])

    def test_no_real_measurements_is_partial(self):
        r=run()
        self.assertEqual(r["status"],"PARTIAL")
        self.assertEqual(r["published_curve_reproduced"],"UNVERIFIED")
        self.assertEqual(r["clinical_effect"],"UNVERIFIED")
        self.assertEqual(len(r["missing"]),3)

    def test_exact_randomization_two_sided(self):
        self.assertEqual(paired_sign_flip([1,1,1]),0.25)
        self.assertEqual(paired_sign_flip([-1,-1,-1]),0.25)

    def test_synthetic_pairing_cannot_count_as_replication(self):
        with tempfile.TemporaryDirectory() as d:
            p=save(d,make_rows())
            r=run(measurements=str(p))
            self.assertEqual(r["exploratory_stats"][0]["pairs"],3)
            self.assertEqual(r["exploratory_stats"][0]["p_two_sided_exact_sign_flip"],0.25)
            self.assertEqual(r["published_curve_reproduced"],"UNVERIFIED")
            self.assertEqual(r["status"],"PARTIAL")

    def test_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            rows=make_rows();rows.append(rows[0])
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                parse_paired_csv(save(d,rows))

    def test_missing_pair_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"Unmatched"):
                parse_paired_csv(save(d,make_rows()[:-1]))

    def test_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            rows=make_rows();rows[0]["value"]="nan"
            with self.assertRaisesRegex(ValueError,"Nonfinite"):
                parse_paired_csv(save(d,rows))

    def test_fake_condition_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            rows=make_rows();rows[0]["condition"]="placebo"
            with self.assertRaisesRegex(ValueError,"Unapproved"):
                parse_paired_csv(save(d,rows))

    def test_nonexistent_xlsx_rejected(self):
        with self.assertRaises(ValueError):
            run(source_data="/absent/publisher.xlsx")

if __name__=="__main__":unittest.main()
