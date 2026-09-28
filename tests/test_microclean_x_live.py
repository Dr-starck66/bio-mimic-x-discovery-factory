import unittest

from factory.microclean_x_live import build_report, classify, dedupe, material_signals

class MicrocleanXLiveTests(unittest.TestCase):
    def test_classifies_materials_and_context(self):
        r = classify({
            "source": "fixture",
            "doi": "10.1/x",
            "title": "Magnetic Fe3O4 chitosan adsorbent for microplastic removal",
            "abstract": "A magnetite composite captures microplastics.",
            "journal": "",
            "url": "",
            "type": "article",
        })
        self.assertTrue(r["mentions_microplastics"])
        self.assertTrue(r["mentions_magnetic"])
        self.assertIn("Fe3O4", r["materials"])
        self.assertIn("chitosan", r["materials"])

    def test_deduplicates_cross_source_same_doi(self):
        records = [
            {"source":"crossref","doi":"10.1000/a","title":"A","abstract":"","journal":"","url":"","type":""},
            {"source":"europepmc","doi":"10.1000/a","title":"A","abstract":"longer abstract","journal":"","url":"","type":""},
        ]
        out = dedupe(records)
        self.assertEqual(len(out), 1)
        self.assertEqual(set(out[0]["sources_seen"]), {"crossref","europepmc"})
        self.assertEqual(out[0]["abstract"], "longer abstract")

    def test_review_queue_requires_independent_evidence(self):
        base = [
            classify({"source":"fixture","doi":"10.1/a","title":"Fe3O4 magnetic microplastic capture","abstract":"","journal":"","url":"","type":""}),
            classify({"source":"fixture","doi":"10.1/b","title":"Magnetite for microplastics removal","abstract":"","journal":"","url":"","type":""}),
        ]
        sig = next(x for x in material_signals(base) if x["material"] == "Fe3O4")
        self.assertEqual(sig["status"], "REVIEW_QUEUE")
        self.assertEqual(sig["independent_evidence_count"], 2)

    def test_single_record_stays_scout(self):
        rows = [
            classify({"source":"fixture","doi":"10.1/a","title":"Fe3O4 magnetic microplastic capture","abstract":"","journal":"","url":"","type":""})
        ]
        sig = next(x for x in material_signals(rows) if x["material"] == "Fe3O4")
        self.assertEqual(sig["status"], "SCOUT")

    def test_report_never_auto_validates(self):
        rows = [
            {"source":"fixture","doi":"10.1/a","title":"Fe3O4 magnetic microplastic capture","abstract":"","journal":"","url":"","type":""},
            {"source":"fixture","doi":"10.1/b","title":"Magnetite for microplastics removal","abstract":"","journal":"","url":"","type":""},
        ]
        report = build_report(rows, [])
        self.assertFalse(report["policy"]["auto_promote_to_validated"])
        self.assertTrue(report["policy"]["fail_closed"])
        self.assertNotIn("VALIDATED", {x["status"] for x in report["material_signals"]})

if __name__ == "__main__":
    unittest.main()
