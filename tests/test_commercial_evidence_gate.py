import unittest

from factory.commercial_evidence_gate import build_report, validate_entry


class CommercialEvidenceGateTests(unittest.TestCase):
    def test_empty_registry_is_unverified(self):
        self.assertEqual(build_report({"evidence": []})["status"], "UNVERIFIED")

    def test_unsigned_template_does_not_count(self):
        e = {"counterparty":"X","evidence_type":"SIGNED_LOI","received_at":"2026-10-05","evidence_source":"template"}
        self.assertEqual(validate_entry(e)["status"], "UNVERIFIED")

    def test_signed_loi_is_partial(self):
        e = {"counterparty":"X","evidence_type":"SIGNED_LOI","received_at":"2026-10-05","evidence_source":"pdf","source_file_sha256":"a"*64}
        self.assertEqual(validate_entry(e)["status"], "PARTIAL")

    def test_paid_pilot_is_pass(self):
        e = {"counterparty":"X","evidence_type":"PAID_PILOT","received_at":"2026-10-05","evidence_source":"contract","source_file_sha256":"b"*64}
        self.assertEqual(validate_entry(e)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
