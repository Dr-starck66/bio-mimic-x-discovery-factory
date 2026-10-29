import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "factory"))
import astra_discovery_zero_cost as m

FIXTURE = {"species": [
    {"id": "acomys", "latin": "Acomys cahirinus", "traits": ["regeneration"],
     "modules": ["ECM remodeling", "controlled inflammation"],
     "evidence": 4, "humanity": 5, "url": "https://example.org/review"},
    {"id": "control", "latin": "Species control", "traits": ["regeneration"],
     "modules": ["placeholder"], "evidence": 5, "humanity": 5, "url": "not-a-url"},
    {"id": "different", "latin": "Species different", "traits": ["longevity"],
     "modules": ["aging"], "evidence": 4, "humanity": 5, "url": "https://example.org/review"},
]}


class DiscoveryTest(unittest.TestCase):
    def test_plan_reuses_existing_hypothesis_and_experiment_engines(self):
        x = m.run(FIXTURE)
        self.assertEqual(x["candidate_program_count"], 1)
        self.assertEqual(len(x["programs"][0]["hypotheses"]), 3)
        self.assertEqual(len(x["programs"][0]["experiments"]), 2)
        self.assertTrue(all(p["status"] == "PROPOSED_NOT_EXECUTED" for p in x["programs"][0]["experiments"]))
        self.assertTrue(all(h["association_only"] for h in x["programs"][0]["hypotheses"]))
        self.assertEqual(x["biological_validation"], "UNVERIFIED")
        self.assertEqual(x["status"], "PARTIAL")

    def test_reproducible_digest(self):
        self.assertEqual(m.run(FIXTURE), m.run(FIXTURE))
        result = m.run(FIXTURE)
        sha = result.pop("sha256")
        self.assertEqual(sha, m.digest(result))

    def test_negative_control_omitted(self):
        self.assertEqual([p["species"] for p in m.propose(FIXTURE)], ["Acomys cahirinus"])

    def test_fail_closed_empty(self):
        self.assertEqual(m.run({"species": []})["status"], "UNVERIFIED")
        with self.assertRaises(ValueError):
            m.propose({"species": "invalid"})
        with self.assertRaises(ValueError):
            m.propose(FIXTURE, limit=0)

    def test_retrospective_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "design.csv"
            with p.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["uuid", "binder_against", "intended_toxins", "sequence"])
                w.writeheader()
                w.writerows([
                    {"uuid": "a", "binder_against": "Cn2", "intended_toxins": "Cn2", "sequence": "TEST"},
                    {"uuid": "b", "binder_against": "", "intended_toxins": "Cn2", "sequence": "TEST"},
                ])
            audit = m.retrospective_audit_csv(p)
            self.assertEqual(audit["record_count"], 2)
            self.assertEqual(audit["binder_designs"], 1)
            self.assertEqual(audit["binding_outcomes_by_target"], {"Cn2": 1})
            self.assertNotIn('"sequence"', json.dumps(audit))

    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "design.csv"
            p.write_text("uuid,binder_against,intended_toxins\na,Cn2,Cn2\na,,Cn2\n")
            with self.assertRaises(ValueError):
                m.retrospective_audit_csv(p)


if __name__ == "__main__":
    unittest.main()
