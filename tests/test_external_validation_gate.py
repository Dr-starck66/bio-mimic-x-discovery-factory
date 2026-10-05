import copy
import unittest

from factory.external_validation_gate import build_report, validate_entry


class ExternalValidationGateTests(unittest.TestCase):
    def test_empty_registry_is_unverified(self):
        r = build_report({"validations": []})
        self.assertEqual(r["status"], "UNVERIFIED")
        self.assertEqual(r["accepted_supporting_validations"], 0)

    def test_positive_review_requires_immutable_source(self):
        e = {
            "validator_name": "External Scientist",
            "validator_affiliation": "Independent Lab",
            "received_at": "2026-10-05T00:00:00Z",
            "verdict": "SUPPORTS_FURTHER_TESTING",
            "rationale": "Worth testing.",
            "evidence_source": "email",
            "self_reported": True,
        }
        self.assertEqual(validate_entry(e)["status"], "UNVERIFIED")

    def test_positive_review_can_pass_gate(self):
        e = {
            "validator_name": "External Scientist",
            "validator_affiliation": "Independent Lab",
            "received_at": "2026-10-05T00:00:00Z",
            "verdict": "SUPPORTS_FURTHER_TESTING",
            "rationale": "Worth testing.",
            "evidence_source": "email",
            "source_message_id": "gmail-message-id",
            "self_reported": True,
        }
        self.assertEqual(validate_entry(e)["status"], "PASS")

    def test_invalid_verdict_is_rejected(self):
        e = {
            "validator_name": "External Scientist",
            "validator_affiliation": "Independent Lab",
            "received_at": "2026-10-05T00:00:00Z",
            "verdict": "AMAZING",
            "rationale": "Strong.",
            "evidence_source": "email",
            "source_message_id": "x",
            "self_reported": True,
        }
        self.assertEqual(validate_entry(e)["status"], "UNVERIFIED")

    def test_negative_review_is_not_suppressed(self):
        e = {
            "validator_name": "External Scientist",
            "validator_affiliation": "Independent Lab",
            "received_at": "2026-10-05T00:00:00Z",
            "verdict": "SCIENTIFICALLY_FLAWED",
            "rationale": "Confounded.",
            "evidence_source": "email",
            "source_message_id": "x",
            "self_reported": True,
        }
        r = build_report({"validations": [e]})
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(r["rejected_validations"], 1)


if __name__ == "__main__":
    unittest.main()
