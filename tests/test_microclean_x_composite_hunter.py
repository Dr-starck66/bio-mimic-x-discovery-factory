import json
import tempfile
import unittest
from pathlib import Path

from factory.microclean_x_composite_hunter import (
    build, evidence_completeness, load_registry, research_priority
)

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"factory"/"microclean_x_composites.json"

class CompositeHunterTests(unittest.TestCase):
    def test_registry_has_five_exact_architectures(self):
        reg=load_registry(REG)
        self.assertEqual(len(reg["candidates"]),5)
        self.assertTrue(all("/" in c["architecture"] or "@" in c["architecture"] or "biochar" in c["architecture"] for c in reg["candidates"]))

    def test_all_have_direct_evidence_and_identifier(self):
        reg=load_registry(REG)
        for c in reg["candidates"]:
            self.assertTrue(c["direct_evidence"])
            self.assertTrue(c.get("doi") or c.get("pmid"))

    def test_no_auto_safety_promotion(self):
        report=build(load_registry(REG))
        self.assertEqual(report["status"],"PASS")
        self.assertEqual(report["promoted_safe_or_field_ready"],[])
        self.assertTrue(report["policy"]["fail_closed"])

    def test_score_semantics_are_explicit(self):
        report=build(load_registry(REG))
        for c in report["ranked_candidates"]:
            self.assertIn("not safety",c["score_semantics"])

    def test_completeness_rewards_real_matrix_and_reuse(self):
        reg=load_registry(REG)
        cb=next(c for c in reg["candidates"] if c["id"]=="fe3o4_carbon_black_fatty_acids")
        pda=next(c for c in reg["candidates"] if c["id"]=="fe3o4_pda")
        checks_cb,score_cb=evidence_completeness(cb)
        checks_pda,score_pda=evidence_completeness(pda)
        self.assertTrue(checks_cb["real_matrix"])
        self.assertTrue(checks_pda["reuse_metric"])
        self.assertGreater(score_cb,0.5)
        self.assertGreater(score_pda,0.5)

    def test_chromium_candidate_is_penalised(self):
        reg=load_registry(REG)
        cr=next(c for c in reg["candidates"] if c["id"]=="fe3o4_mil101cr")
        clone=json.loads(json.dumps(cr))
        clone["architecture"]="Fe3O4/MIL-101(no-Cr)"
        self.assertLess(research_priority(cr),research_priority(clone))

    def test_broken_identifier_fails_closed(self):
        raw=json.loads(REG.read_text(encoding="utf-8"))
        raw["candidates"][0]["doi"]=None
        raw["candidates"][0]["pmid"]=None
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bad.json"
            p.write_text(json.dumps(raw),encoding="utf-8")
            with self.assertRaises(AssertionError):
                load_registry(p)

if __name__=="__main__":
    unittest.main()
