import json
import tempfile
import unittest
from pathlib import Path

from factory.microclean_x import build_report, gate, load_seed, research_priority_score

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "factory" / "microclean_x_candidates.json"

class MicrocleanXTests(unittest.TestCase):
    def test_seed_is_valid(self):
        seed = load_seed(SEED)
        self.assertEqual(seed["campaign"]["id"], "MICROCLEAN-X")
        self.assertGreaterEqual(len(seed["candidates"]), 5)

    def test_reference_is_not_deployable(self):
        seed = load_seed(SEED)
        ref = next(c for c in seed["candidates"] if c["role"] == "REFERENCE")
        self.assertEqual(gate(ref), "REFERENCE_NOT_DEPLOYABLE")
        self.assertTrue(ref["contains_nickel"])

    def test_hypotheses_fail_closed_without_direct_microplastic_evidence(self):
        seed = load_seed(SEED)
        for c in seed["candidates"]:
            if c["role"] == "HYPOTHESIS":
                self.assertFalse(c["microplastic_direct_evidence"])
                self.assertEqual(gate(c), "SCOUT_NEEDS_DIRECT_VALIDATION")

    def test_no_false_promotion(self):
        report = build_report(load_seed(SEED))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["promoted_candidates"], [])
        self.assertTrue(report["evidence_policy"]["fail_closed"])

    def test_priority_score_is_not_safety_score(self):
        seed = load_seed(SEED)
        scores = [research_priority_score(c) for c in seed["candidates"]]
        self.assertTrue(all(isinstance(x, int) for x in scores))
        report = build_report(seed)
        for row in report["candidates"]:
            self.assertIn("not efficacy or safety", row["score_semantics"])

    def test_provenance_breakage_fails(self):
        raw = json.loads(SEED.read_text(encoding="utf-8"))
        raw["candidates"][1]["sources"] = ["does_not_exist"]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.json"
            p.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(AssertionError):
                load_seed(p)

if __name__ == "__main__":
    unittest.main()
