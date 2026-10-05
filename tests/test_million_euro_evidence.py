import unittest
from pathlib import Path

from factory.million_euro_evidence import (
    MEMORY_PATH,
    PROGRAMS_PATH,
    REGISTRY_PATH,
    build_package,
    classify_program,
    clean_genes,
    load_json,
)


class MillionEuroEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.programs = load_json(PROGRAMS_PATH)
        cls.memory = load_json(MEMORY_PATH)
        cls.registry = load_json(REGISTRY_PATH)
        cls.package = build_package(cls.programs, cls.memory, cls.registry)

    def test_text_fragments_are_excluded(self):
        rows = {r["title"]: r for r in self.package["portfolio"]["cleaned_rows"]}
        for title in ("This review", "These findings", "This study", "This narrative"):
            if title in rows:
                self.assertFalse(rows[title]["eligible_for_investor_package"])
                self.assertIn("NON_SPECIES_TEXT_FRAGMENT", rows[title]["quality_flags"])

    def test_known_gene_noise_is_quarantined(self):
        clean, suspect = clean_genes(["VEGF", "NF-", "RT-PCR", "OCTA"])
        self.assertEqual(clean, ["VEGF"])
        self.assertEqual(set(suspect), {"NF-", "RT-PCR", "OCTA"})

    def test_unverified_non_species_programs_cannot_enter_package(self):
        row = classify_program({
            "id": "x",
            "title": "Interesting findings",
            "status": "ACTIVE",
            "committee_score": 99,
            "genes": ["VEGF"],
            "mechanisms": ["regeneration"],
            "sources": ["PMID:1", "PMID:2"],
            "taxon_verified": False,
        })
        self.assertFalse(row["eligible_for_investor_package"])
        self.assertIn("TAXON_NOT_VERIFIED", row["quality_flags"])

    def test_flagship_is_acomys(self):
        self.assertEqual(self.package["flagship"]["title"], "Acomys cahirinus")
        self.assertTrue(self.package["flagship"]["taxon_verified"])
        self.assertGreaterEqual(self.package["flagship"]["source_count"], 3)
        self.assertEqual(self.package["flagship"]["suspect_genes"], [])

    def test_flagship_has_multi_study_external_registry(self):
        ev = self.package["flagship"]["registry"]["literature_evidence"]
        primary = [x for x in ev if x["role"] == "primary"]
        self.assertGreaterEqual(len(primary), 4)
        self.assertTrue(any(int(x["year"]) >= 2025 for x in ev))

    def test_valuation_is_not_falsely_passed(self):
        readiness = self.package["valuation_readiness"]
        self.assertEqual(readiness["status"], "PARTIAL")
        self.assertEqual(
            readiness["valuation_statement"],
            "TECHNOLOGY/COMPANY_VALUATION_CASE_NOT_CASH_EXIT_PROOF",
        )
        gates = {g["gate"]: g["status"] for g in readiness["gates"]}
        self.assertEqual(gates["independent_lab_validation_of_biomimic_output"], "FAIL")
        self.assertEqual(gates["formal_ip_novelty_freedom_to_operate"], "UNVERIFIED")
        self.assertEqual(gates["paying_customers_or_contracts"], "FAIL")

    def test_known_memory_contamination_is_exposed(self):
        h = self.package["memory_hygiene"]
        self.assertGreaterEqual(h["suspicious_subject_count"], 1)
        self.assertIn("Mechanisms and", h["suspicious_subjects"])

    def test_package_has_reproducible_fingerprint(self):
        self.assertEqual(len(self.package["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
