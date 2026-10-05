#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "factory" / "external_validation_registry.json"
REPORT_DIR = ROOT / "reports" / "external-validation"

ALLOWED_VERDICTS = {
    "SUPPORTS_FURTHER_TESTING",
    "INTERESTING_BUT_WEAK",
    "NOT_NOVEL",
    "SCIENTIFICALLY_FLAWED",
}


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def validate_entry(entry: Mapping[str, Any]) -> Dict[str, Any]:
    required = (
        "validator_name",
        "validator_affiliation",
        "received_at",
        "verdict",
        "rationale",
        "evidence_source",
    )
    missing = [k for k in required if not str(entry.get(k, "")).strip()]
    if missing:
        return {"status": "UNVERIFIED", "reason": f"missing fields: {', '.join(missing)}"}

    if entry["verdict"] not in ALLOWED_VERDICTS:
        return {"status": "UNVERIFIED", "reason": "verdict not in allowed set"}

    if entry.get("self_reported") is not True:
        return {"status": "UNVERIFIED", "reason": "validator statement must be explicitly marked self_reported"}

    if entry.get("source_message_id") is None and entry.get("source_file_sha256") is None:
        return {"status": "UNVERIFIED", "reason": "no immutable source reference"}

    if entry["verdict"] == "SUPPORTS_FURTHER_TESTING":
        return {"status": "PASS", "reason": "independent reviewer supports further testing"}
    if entry["verdict"] == "INTERESTING_BUT_WEAK":
        return {"status": "PARTIAL", "reason": "reviewer sees value but evidence remains weak"}
    return {"status": "FAIL", "reason": "reviewer rejected novelty or scientific framing"}


def build_report(registry: Mapping[str, Any]) -> Dict[str, Any]:
    rows = []
    for entry in registry.get("validations", []):
        result = validate_entry(entry)
        body = dict(entry)
        body["gate"] = result
        body["sha256"] = sha256_json(entry)
        rows.append(body)

    pass_rows = [x for x in rows if x["gate"]["status"] == "PASS"]
    partial_rows = [x for x in rows if x["gate"]["status"] == "PARTIAL"]
    fail_rows = [x for x in rows if x["gate"]["status"] == "FAIL"]

    if pass_rows:
        status = "PASS"
    elif partial_rows:
        status = "PARTIAL"
    elif fail_rows:
        status = "FAIL"
    else:
        status = "UNVERIFIED"

    report = {
        "brick": "BIO-MIMIC X EXTERNAL VALIDATION GATE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "accepted_supporting_validations": len(pass_rows),
        "partial_validations": len(partial_rows),
        "rejected_validations": len(fail_rows),
        "validations": rows,
        "policy": {
            "no_self_authored_validation": True,
            "immutable_source_reference_required": True,
            "verdict_whitelist": sorted(ALLOWED_VERDICTS),
            "one_positive_review_is_not_experimental_validation": True,
        },
    }
    report["sha256"] = sha256_json({k:v for k,v in report.items() if k not in {"generated_at","sha256"}})
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(DEFAULT_INPUT))
    p.add_argument("--no-write", action="store_true")
    args = p.parse_args()

    registry = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = build_report(registry)

    if not args.no_write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        (REPORT_DIR / "latest.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(json.dumps({
        "status": report["status"],
        "accepted_supporting_validations": report["accepted_supporting_validations"],
        "sha256": report["sha256"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
