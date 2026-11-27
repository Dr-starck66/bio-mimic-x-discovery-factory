#!/usr/bin/env python3
"""ASTRA MEDICAL CLAIM AUDIT Ω v0.1: offline, deterministic research-only guard.

Not a clinical decision support system. No medical truth is inferred from references.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

VERSION = "ASTRA-MEDICAL-CLAIM-AUDIT-0.1.0"
CLAIM_KINDS = {"treatment", "diagnosis", "prognosis", "drug_interaction", "other"}
STANCES = {"supports", "contradicts", "context"}
SENSITIVE_KEYS = {"patient", "patient_data", "patient_id", "full_name", "date_of_birth", "dob", "email", "phone", "medical_record", "medical_record_number"}
VERBS = r"(?:arretez|arreter|suspendez|suspendre|remplacez|remplacer|augmentez|augmenter|diminuez|diminuer|stop|stop taking|switch|discontinue|increase|reduce|replace)"
THERAPIES = r"(?:traitement|medicament|chimiotherapie|radiotherapie|immunotherapie|therapy|treatment|medication|chemotherapy|radiotherapy|immunotherapy|dose|dosage)"
ACTION = re.compile(r"\b" + VERBS + r"\b.{0,100}?\b" + THERAPIES + r"\b", re.I | re.S)
NEGATION = re.compile(r"\b(?:ne\s+pas|ne\s+jamais|do\s+not|don't|never)\s+$", re.I)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)


def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(obj: object) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def normalized(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(char))


def validate_source(url: str) -> bool:
    try:
        u = urlsplit(url)
        if u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment:
            return False
        host = u.hostname.lower()
        if host == "localhost" or host.endswith((".local", ".internal")) or "." not in host:
            return False
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            if not address.is_global:
                return False
        return u.port in (None, 443)
    except (ValueError, TypeError):
        return False


def validate(payload: object) -> dict:
    if not isinstance(payload, dict) or set(payload) != {"case_id", "claims"}:
        raise ValueError("expected only case_id and claims; patient data is prohibited")
    case_id = payload["case_id"]
    if not isinstance(case_id, str) or not re.fullmatch(r"synthetic-[a-z0-9-]{3,48}", case_id):
        raise ValueError("only synthetic-... case IDs are permitted")
    claims = payload["claims"]
    if not isinstance(claims, list) or not (1 <= len(claims) <= 100):
        raise ValueError("claims must contain 1 to 100 entries")
    ids = set()
    for c in claims:
        if not isinstance(c, dict) or set(c) != {"id", "text", "kind", "references"}:
            raise ValueError("claim must have id, text, kind, references only")
        if not isinstance(c["id"], str) or not re.fullmatch(r"C[0-9]{1,4}", c["id"]) or c["id"] in ids:
            raise ValueError("claim IDs must be unique C-number labels")
        ids.add(c["id"])
        if not isinstance(c["text"], str) or not (3 <= len(c["text"]) <= 2000) or EMAIL.search(c["text"]):
            raise ValueError("invalid or potentially identifying claim text")
        if c["kind"] not in CLAIM_KINDS:
            raise ValueError("invalid claim kind")
        refs = c["references"]
        if not isinstance(refs, list) or len(refs) > 20:
            raise ValueError("references must be a list of at most 20")
        for ref in refs:
            if not isinstance(ref, dict) or set(ref) != {"url", "title", "locator", "stance"}:
                raise ValueError("reference must have url, title, locator, stance only")
            if any(not isinstance(ref[k], str) for k in ref):
                raise ValueError("reference values must be strings")
            if not (1 <= len(ref["title"]) <= 200 and 1 <= len(ref["locator"]) <= 120 and len(ref["url"]) <= 512):
                raise ValueError("invalid reference fields")
            if ref["stance"] not in STANCES:
                raise ValueError("invalid reference stance")
    return payload


def actionable_phrase(text: str) -> bool:
    norm = normalized(text)
    for m in ACTION.finditer(norm):
        prefix = norm[max(0, m.start() - 18): m.start()]
        if not NEGATION.search(prefix):
            return True
    return False


def audit(payload: object) -> dict:
    case = validate(payload)
    rows = []
    for c in case["claims"]:
        refs = c["references"]
        issues = []
        if not refs:
            issues.append("NO_REFERENCES")
        if any(not validate_source(r["url"]) for r in refs):
            issues.append("INVALID_SOURCE_URL")
        if len({r["stance"] for r in refs} & {"supports", "contradicts"}) == 2:
            issues.append("DECLARED_CONFLICT_UNVALIDATED")
        if refs:
            issues.append("REFERENCES_NOT_INDEPENDENTLY_RETRIEVED")
        flagged = actionable_phrase(c["text"])  # user-declared kind must never bypass the safety screen
        if flagged:
            issues.append("POSSIBLE_TREATMENT_DIRECTIVE")
        rows.append({
            "id": c["id"], "kind": c["kind"], "claim_sha256": hashlib.sha256(c["text"].encode()).hexdigest(),
            "reference_checks": [{"url": r["url"] if validate_source(r["url"]) else None,
                                  "title": r["title"], "locator": r["locator"], "stance": r["stance"],
                                  "url_shape": "PASS" if validate_source(r["url"]) else "FAIL",
                                  "content_retrieval": "UNVERIFIED", "scientific_relevance": "UNVERIFIED"} for r in refs],
            "citation_status": "PARTIAL" if refs and all(validate_source(r["url"]) for r in refs) else "UNVERIFIED",
            "scientific_status": "UNVERIFIED",
            "safety_screen": "FAIL" if flagged else "PARTIAL",
            "issues": sorted(issues),
        })
    overall = "FAIL" if any(r["safety_screen"] == "FAIL" for r in rows) else (
        "PARTIAL" if any(r["citation_status"] == "PARTIAL" for r in rows) else "UNVERIFIED")
    report = {
        "protocol": VERSION,
        "input_sha256": sha256(case),
        "case_id": case["case_id"],
        "schema_validation": "PASS",
        "overall_audit_status": overall,
        "scientific_validity": "UNVERIFIED",
        "rules_are_not_exhaustive": True,
        "requires_clinician_review": True,
        "external_network_requests": 0,
        "claims": rows,
        "counts": {"claims": len(rows), "possible_directives": sum(r["safety_screen"] == "FAIL" for r in rows),
                   "unverified_science": len(rows)},
    }
    report["report_sha256"] = sha256(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline synthetic-only evidence audit; not a medical device")
    parser.add_argument("input", type=Path, help="synthetic input JSON")
    parser.add_argument("--out", type=Path, required=True, help="output report JSON")
    args = parser.parse_args()
    try:
        case = json.loads(args.input.read_text(encoding="utf-8"))
        result = audit(case)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(2, "FAIL (no report written): " + str(error) + "\n")
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{result['overall_audit_status']} | {len(result['claims'])} claims | SHA-256 {result['report_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())