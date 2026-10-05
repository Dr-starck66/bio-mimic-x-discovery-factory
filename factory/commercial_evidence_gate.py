#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "factory" / "commercial_evidence_registry.json"

ALLOWED_TYPES = {"SIGNED_LOI", "PAID_PILOT", "RESEARCH_CONTRACT", "LICENSE_DISCUSSION"}


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def validate_entry(entry: Mapping[str, Any]) -> Dict[str, Any]:
    required = ("counterparty", "evidence_type", "received_at", "evidence_source")
    missing = [k for k in required if not str(entry.get(k, "")).strip()]
    if missing:
        return {"status": "UNVERIFIED", "reason": f"missing fields: {', '.join(missing)}"}
    if entry["evidence_type"] not in ALLOWED_TYPES:
        return {"status": "UNVERIFIED", "reason": "unsupported evidence type"}
    if entry.get("source_message_id") is None and entry.get("source_file_sha256") is None:
        return {"status": "UNVERIFIED", "reason": "no immutable source reference"}

    if entry["evidence_type"] in {"PAID_PILOT", "RESEARCH_CONTRACT"}:
        return {"status": "PASS", "reason": "verified commercial commitment"}
    if entry["evidence_type"] == "SIGNED_LOI":
        return {"status": "PARTIAL", "reason": "signed non-binding commercial intent"}
    return {"status": "PARTIAL", "reason": "verified strategic interest without commercial commitment"}


def build_report(registry: Mapping[str, Any]) -> Dict[str, Any]:
    rows = []
    for entry in registry.get("evidence", []):
        gate = validate_entry(entry)
        rows.append({**dict(entry), "gate": gate, "sha256": sha256_json(entry)})
    statuses = [x["gate"]["status"] for x in rows]
    status = "PASS" if "PASS" in statuses else ("PARTIAL" if "PARTIAL" in statuses else "UNVERIFIED")
    report = {
        "brick": "BIO-MIMIC X COMMERCIAL EVIDENCE GATE",
        "status": status,
        "verified_entries": len([x for x in rows if x["gate"]["status"] in {"PASS", "PARTIAL"}]),
        "evidence": rows,
        "policy": {
            "unsigned_templates_do_not_count": True,
            "immutable_source_reference_required": True,
            "paid_or_contractual_commitment_required_for_pass": True,
        },
    }
    report["sha256"] = sha256_json(report)
    return report


def main() -> int:
    registry = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
    report = build_report(registry)
    print(json.dumps({"status": report["status"], "verified_entries": report["verified_entries"], "sha256": report["sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
