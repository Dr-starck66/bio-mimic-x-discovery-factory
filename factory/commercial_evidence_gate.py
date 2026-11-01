#!/usr/bin/env python3
"""BIO-MIMIC X commercial gate: never upgrade self-asserted ledger entries
to a verified offer or paid contract.

A SHA of arbitrary bytes, an email ID, or a string saying "PAID_PILOT"
does NOT validate an independent counterparty's identity, consent,
contract, payment, signature, or authority.

The existing local-only GitHub pipeline has NO connected provider verifier.
All local claims remain UNVERIFIED until a separately authenticated,
provider-backed verification adapter is built and audited. No fake PASS.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "factory" / "commercial_evidence_registry.json"

ALLOWED_TYPES = {
    "OUTREACH_SENT", "REPLY_RECEIVED", "LICENSE_DISCUSSION",
    "SIGNED_LOI", "PAID_PILOT", "RESEARCH_CONTRACT",
}
PAYMENT_OR_CONTRACT = {"PAID_PILOT", "RESEARCH_CONTRACT", "SIGNED_LOI"}
SHA_256_PATTERN = re.compile(r"[a-fA-F0-9]{64}\Z")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def validate_entry(entry: Mapping[str, Any]) -> Dict[str, Any]:
    """Preflight LOCAL metadata only. Never verifies counterparty commitments."""
    if not isinstance(entry, Mapping):
        return {"status": "UNVERIFIED", "metadata_complete": False,
                "reason": "invalid local evidence object"}
    required = ("counterparty", "evidence_type", "received_at", "evidence_source")
    missing = [k for k in required if not str(entry.get(k) or "").strip()]
    if missing:
        return {"status": "UNVERIFIED", "metadata_complete": False,
                "reason": f"missing fields: {', '.join(missing)}"}
    if entry["evidence_type"] not in ALLOWED_TYPES:
        return {"status": "UNVERIFIED", "metadata_complete": False,
                "reason": "unsupported evidence type"}
    try:
        date.fromisoformat(str(entry["received_at"]))
    except ValueError:
        return {"status": "UNVERIFIED", "metadata_complete": False,
                "reason": "invalid received_at ISO date"}
    mid = entry.get("source_message_id")
    sha = entry.get("source_file_sha256")
    if not ((isinstance(mid, str) and len(mid.strip()) >= 8) or
            (isinstance(sha, str) and SHA_256_PATTERN.fullmatch(sha))):
        return {"status": "UNVERIFIED", "metadata_complete": False,
                "reason": "missing or malformed source reference"}

    # An untrusted local entry is NOT an authenticated original incoming message,
    # signed contract, bank receipt, payment confirmation or purchase order.
    # 'source_file_sha256' checks format only, not actual bytes or signatures.
    return {
        "status": "UNVERIFIED",
        "metadata_complete": True,
        "reason": "LOCAL_CLAIM_NOT_AUTHENTICATED_BY_COUNTERPARTY_OR_PAYMENT_PROVIDER",
        "note": "The ledger has no authenticated external adapter. A Gmail SENT ID, arbitrary 64-hex SHA or text stating PAID_PILOT never proves sale, interest or payment.",
        "needs_external_verification": True,
    }


def build_report(registry: Mapping[str, Any]) -> Dict[str, Any]:
    entries = registry.get("evidence", [])
    if not isinstance(entries, list):
        raise ValueError("registry.evidence must be an array")
    rows = []
    for entry in entries:
        gate = validate_entry(entry)
        rows.append({**dict(entry) if isinstance(entry, Mapping) else {"raw_type": str(type(entry))},
                     "gate": gate, "sha256": sha256_json(entry)})
    report = {
        "brick": "BIO-MIMIC X COMMERCIAL EVIDENCE GATE",
        # No live provider validation in a source-code repository.
        "status": "UNVERIFIED",
        "verified_entries": 0,
        "metadata_complete_entries": sum(bool(x["gate"].get("metadata_complete")) for x in rows),
        "unverified_local_claims": len(rows),
        "evidence": rows,
        "policy": {
            "unsigned_templates_do_not_count": True,
            "email_sent_is_not_delivered_or_interest": True,
            "document_hash_is_not_signature_or_funds_receipt": True,
            "self_asserted_payment_does_not_count": True,
            "external_counterparty_and_payment_authentication_required_for_pass": True,
            "live_provider_adapter_connected": False,
        },
    }
    report["sha256"] = sha256_json(report)
    return report


def main() -> int:
    registry = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
    report = build_report(registry)
    print(json.dumps({
        "status": report["status"],
        "verified_entries": report["verified_entries"],
        "metadata_complete_entries": report["metadata_complete_entries"],
        "sha256": report["sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
