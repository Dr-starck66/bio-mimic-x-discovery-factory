"""All fixtures in this file are synthetic and are never biological evidence."""
import gzip
import hashlib
import tempfile
import unittest
from pathlib import Path

from validation.epigenetic_deaging_gate import (
    DATASETS, build_report, candidate_cross_species_gate, check_local_gzip,
)


class EpigeneticEvidenceGateTests(unittest.TestCase):
    def make_gzip(self, data):
        tmp = tempfile.TemporaryDirectory()
        p = Path(tmp.name) / "fixture.gz"
        p.write_bytes(data)
        self.addCleanup(tmp.cleanup)
        return p

    def test_complete_gzip_only_validates_bytes_not_science(self):
        raw = gzip.compress(b"synthetic example only\n" * 300, mtime=0)
        r = check_local_gzip(self.make_gzip(raw), hashlib.sha256(raw).hexdigest(), 8)
        self.assertEqual(r["status"], "PASS_INTEGRITY_ONLY")
        self.assertEqual(r["scientific_reproduction"], "UNVERIFIED")

    def test_truncated_gzip_with_matching_digest_is_still_rejected(self):
        raw = gzip.compress(b"x" * 10000, mtime=0)[:-8]
        with self.assertRaisesRegex(ValueError, "truncated gzip"):
            check_local_gzip(self.make_gzip(raw), hashlib.sha256(raw).hexdigest(), 8)

    def test_wrong_sha_fails_closed(self):
        raw = gzip.compress(b"a" * 5000, mtime=0)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            check_local_gzip(self.make_gzip(raw), "0" * 64, 8)

    def test_missing_digest_fails_closed(self):
        raw = gzip.compress(b"a" * 5000, mtime=0)
        with self.assertRaisesRegex(ValueError, "pinned"):
            check_local_gzip(self.make_gzip(raw), "", 8)

    def test_raw_status_not_mistaken_for_reproduction(self):
        r = build_report({"status": "PASS_INTEGRITY_ONLY"})
        self.assertEqual(r["independent_age_clock_reproduction"], "UNVERIFIED")
        self.assertEqual(r["clinical_anti_aging_efficacy"], "UNVERIFIED")
        self.assertEqual(r["status"], "PARTIAL")

    def test_controlled_db_gap_access_is_explicit(self):
        self.assertEqual(DATASETS["phs004047.v1.p1"]["access"], "AUTHORIZATION_REQUIRED")

    def test_symbol_only_orthology_never_passes(self):
        r = candidate_cross_species_gate({
            "human_study": "human", "axolotl_study": "axolotl",
            "orthology_evidence": "GENE_SYMBOL_MATCH",
            "biological_replicates": 3, "negative_controls": ["matched-control"]})
        self.assertEqual(r["status"], "UNVERIFIED")

    def test_reciprocal_orthology_still_is_not_therapy(self):
        r = candidate_cross_species_gate({
            "human_study": "human", "axolotl_study": "axolotl",
            "orthology_evidence": "RECIPROCAL_SEQUENCE_VERIFIED",
            "biological_replicates": 3, "negative_controls": ["control"]})
        self.assertEqual(r["status"], "PARTIAL")
        self.assertNotIn("validated", r["status"].lower())

    def test_negative_control_preserved(self):
        r = build_report()
        self.assertEqual(r["retained_negative_control"]["legacy_result"], "FAIL")
        self.assertTrue(r["retained_negative_control"]["not_overridden_by_this_report"])


if __name__ == "__main__":
    unittest.main()
