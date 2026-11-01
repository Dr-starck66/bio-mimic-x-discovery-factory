import unittest

from factory.commercial_evidence_gate import build_report, validate_entry


class CommercialEvidenceGateTests(unittest.TestCase):
    """Negative-control cases MUST fail closed in the real local ledger."""

    def test_empty_registry_is_unverified(self):
        r=build_report({"evidence":[]})
        self.assertEqual(r["status"],"UNVERIFIED")
        self.assertEqual(r["verified_entries"],0)

    def test_unsigned_template_does_not_count(self):
        e={"counterparty":"X","evidence_type":"SIGNED_LOI","received_at":"2026-10-05","evidence_source":"template"}
        self.assertEqual(validate_entry(e)["status"],"UNVERIFIED")
        self.assertFalse(validate_entry(e)["metadata_complete"])

    def test_signed_loi_with_fake_hash_never_passes(self):
        e={"counterparty":"X","evidence_type":"SIGNED_LOI","received_at":"2026-10-05",
           "evidence_source":"pdf","source_file_sha256":"a"*64}
        self.assertEqual(validate_entry(e)["status"],"UNVERIFIED")
        self.assertTrue(validate_entry(e)["metadata_complete"])
        self.assertEqual(build_report({"evidence":[e]})["verified_entries"],0)

    def test_fake_paid_pilot_never_passes(self):
        e={"counterparty":"X","evidence_type":"PAID_PILOT","received_at":"2026-10-05",
           "evidence_source":"contract","source_file_sha256":"b"*64,
           "value_eur":1000000,"paid":True}
        x=validate_entry(e)
        self.assertEqual(x["status"],"UNVERIFIED")
        self.assertEqual(build_report({"evidence":[e]})["status"],"UNVERIFIED")

    def test_fake_signed_research_contract_never_passes(self):
        e={"counterparty":"X","evidence_type":"RESEARCH_CONTRACT",
           "received_at":"2026-10-05","evidence_source":"PDF",
           "source_file_sha256":"c"*64,"signature_verified":True,"amount_eur":1000000}
        self.assertEqual(validate_entry(e)["status"],"UNVERIFIED")

    def test_outbound_sent_email_is_not_buyer_interest(self):
        e={"counterparty":"Integra","evidence_type":"OUTREACH_SENT",
           "received_at":"2026-11-01","evidence_source":"Gmail SENT",
           "source_message_id":"1a197c83ad999ee1"}
        out=build_report({"evidence":[e]})
        self.assertEqual(out["status"],"UNVERIFIED")
        self.assertEqual(out["verified_entries"],0)
        self.assertEqual(out["metadata_complete_entries"],1)

    def test_self_declared_inbound_reply_is_not_authenticated(self):
        e={"counterparty":"Buyer","evidence_type":"LICENSE_DISCUSSION",
           "received_at":"2026-11-01","evidence_source":"my note",
           "source_message_id":"12345678","reply_from_buyer":True}
        self.assertEqual(validate_entry(e)["status"],"UNVERIFIED")

    def test_corrupt_hash_is_rejected(self):
        e={"counterparty":"X","evidence_type":"PAID_PILOT",
           "received_at":"2026-10-05","evidence_source":"unknown",
           "source_file_sha256":"not-a-real-hash"}
        self.assertFalse(validate_entry(e)["metadata_complete"])

    def test_invalid_date_is_rejected(self):
        e={"counterparty":"X","evidence_type":"PAID_PILOT",
           "received_at":"2026-14-99","evidence_source":"unknown",
           "source_message_id":"123456789"}
        self.assertEqual(validate_entry(e)["status"],"UNVERIFIED")
        self.assertFalse(validate_entry(e)["metadata_complete"])

    def test_registry_type_must_be_array(self):
        with self.assertRaises(ValueError):
            build_report({"evidence":{"malformed":"object"}})

    def test_generated_fingerprint_is_deterministic(self):
        reg={"evidence":[{"counterparty":"X","evidence_type":"OUTREACH_SENT",
                          "received_at":"2026-11-01","evidence_source":"api",
                          "source_message_id":"12345678"}]}
        x=build_report(reg)
        self.assertEqual(x["sha256"],build_report(reg)["sha256"])


if __name__=="__main__":
    unittest.main()
