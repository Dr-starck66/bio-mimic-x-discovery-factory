"""Synthetic GTF tests for the HAND2 independent-neighborhood scanner; no biological claim."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from validation.hand2_independent_anchors import evaluate

SCRIPT = Path(__file__).resolve().parents[1] / "validation" / "hand2_independent_anchors.py"

class TestHand2IndependentAnchors(unittest.TestCase):
    def test_real_legacy_chromosome_label_and_bilateral_synteny(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            old, modern, out = root/"old.gtf", root/"modern.gtf", root/"report.json"
            old.write_text('chr6q\tsrc\tgene\t884790000\t884791000\t.\t+\t.\tgene_id "OLD_A"; gene_name "GENEA";\n'
                           'chr6q\tsrc\tgene\t884802000\t884803000\t.\t+\t.\tgene_id "OLD_B"; gene_name "GENEB";\n')
            modern.write_text('NC_090937.1\tsrc\tgene\t910040000\t910041000\t.\t-\t.\tgene_id "NEW_A"; gene_name "GENEA";\n'
                              'NC_090937.1\tsrc\tgene\t910020000\t910021000\t.\t-\t.\tgene_id "NEW_B"; gene_name "GENEB";\n')
            r = subprocess.run([sys.executable, str(SCRIPT), "--old-gtf", str(old), "--modern-gtf", str(modern), "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout+r.stderr)
            report = json.loads(out.read_text())
            self.assertEqual(report["status"], "PARTIAL_ANNOTATION_ANCHORS")
            self.assertEqual(report["consistent_anchors"], 2)
            self.assertEqual(report["chromosome_labels"]["old"], "chr6q")
            self.assertEqual(report["genome_wide_uniqueness"], "UNVERIFIED")

    def test_wrong_alias_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            old, modern, out = root/"old.gtf", root/"modern.gtf", root/"report.json"
            old.write_text('chr6q\tsrc\tgene\t884790000\t884791000\t.\t+\t.\tgene_id "OLD_A"; gene_name "GENEA";\n')
            modern.write_text('NC_090937.1\tsrc\tgene\t910040000\t910041000\t.\t-\t.\tgene_id "NEW_A"; gene_name "GENEA";\n')
            r = subprocess.run([sys.executable, str(SCRIPT), "--old-gtf", str(old), "--modern-gtf", str(modern), "--old-chrom", "CM010938.2", "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            report = json.loads(out.read_text())
            self.assertEqual(report["status"], "UNVERIFIED_EMPTY_CHROMOSOME_ANNOTATION")
            self.assertEqual(report["gene_counts"]["old"], 0)

    def test_paralog_excluded_and_single_flank_rejected(self):
        old = {"HAND1":{"start":1,"end":2,"strand":"+"},"GENEA":{"start":1,"end":2,"strand":"+"}}
        modern = {"HAND1":{"start":11,"end":12,"strand":"-"},"GENEA":{"start":11,"end":12,"strand":"-"}}
        report = evaluate(old, modern, 5, 10)
        self.assertEqual(report["matched_unique_symbols"], 1)
        self.assertEqual(report["status"], "UNVERIFIED_INSUFFICIENT_BILATERAL_ANCHORS")

if __name__ == "__main__":
    unittest.main()
