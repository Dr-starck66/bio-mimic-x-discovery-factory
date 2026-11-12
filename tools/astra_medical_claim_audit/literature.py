#!/usr/bin/env python3
"""ASTRA MEDICAL CLAIM AUDIT Ω v0.2 — bibliographic identity only.

Reads PubMed XML using a fixed, allowlisted official endpoint.  Never assesses
truth, clinical appropriateness, or treatment validity.  Synthetic cases only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET

from audit import audit, canonical, sha256, validate

PMID_URL = re.compile(r"^https://pubmed\.ncbi\.nlm\.nih\.gov/([1-9][0-9]{0,8})/?$")
DOI_LOCATOR = re.compile(r"^doi:\s*(10\.[0-9]{4,9}/\S+)$", re.I)
MAX_RESPONSE_BYTES = 1_000_000
OFFICIAL_HOST = "eutils.ncbi.nlm.nih.gov"


def clean(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.casefold()).strip()


def xml_text(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext()).strip()


def pubmed_metadata(data: bytes) -> dict:
    """Parse an NCBI PubMed XML record, without asserting clinical validity."""
    if len(data) > MAX_RESPONSE_BYTES:
        raise ValueError("source XML exceeds size cap")
    root = ET.fromstring(data)
    article = root.find("./PubmedArticle") if root.tag != "PubmedArticle" else root
    if article is None:
        raise ValueError("missing PubmedArticle element")
    pmid = xml_text(article.find("./MedlineCitation/PMID"))
    title = xml_text(article.find("./MedlineCitation/Article/ArticleTitle"))
    abstract = " ".join(xml_text(x) for x in article.findall("./MedlineCitation/Article/Abstract/AbstractText"))
    dois = [xml_text(x) for x in article.findall("./PubmedData/ArticleIdList/ArticleId")
            if x.get("IdType", "").casefold() == "doi"]
    dois += [xml_text(x) for x in article.findall("./MedlineCitation/Article/ELocationID")
             if x.get("EIdType", "").casefold() == "doi"]
    if not re.fullmatch(r"[1-9][0-9]{0,8}", pmid) or not title:
        raise ValueError("invalid or absent PMID/title")
    return {"pmid": pmid, "title": title, "doi": next((x for x in dois if x), None),
            "abstract_sha256": hashlib.sha256(abstract.encode("utf-8")).hexdigest() if abstract else None,
            "abstract_present": bool(abstract)}


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect not allowed for official-source retrieval")


def official_open(req, timeout=8):
    return build_opener(RejectRedirects()).open(req, timeout=timeout)


def fetch_official_pubmed_xml(pmid: str, opener=None) -> bytes:
    """Fixed-host retrieval; no user-controlled host, URL, or query string."""
    if not re.fullmatch(r"[1-9][0-9]{0,8}", pmid):
        raise ValueError("invalid PMID")
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=" + pmid + "&retmode=xml"
    req = Request(url, headers={"User-Agent": "ASTRA-Medical-Claim-Audit/0.2 (research-only)", "Accept": "application/xml"})
    with (opener or official_open)(req, timeout=8) as response:
        target = urlsplit(response.geturl())
        if target.scheme != "https" or target.hostname != OFFICIAL_HOST or target.username or target.password:
            raise ValueError("non-official redirect blocked")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("source XML exceeds size cap")
    return raw


def verify_reference(ref: dict, source_xml: bytes | None, mode: str) -> dict:
    """Only a real NCBI response can receive retrieval=PASS.

    Fixtures, regardless of content, remain PARTIAL/UNVERIFIED as evidence of
    a live online retrieval.  Scientific validity is always UNVERIFIED.
    """
    entry = {"url": ref["url"], "bibliographic_identity": "UNVERIFIED",
             "live_retrieval": "UNVERIFIED", "abstract_present": "UNVERIFIED",
             "scientific_relevance": "UNVERIFIED", "clinical_validity": "UNVERIFIED",
             "source_xml_sha256": None, "pmid": None, "doi": None,
             "retrieval_mode": mode, "issues": []}
    match = PMID_URL.fullmatch(ref["url"])
    if match is None:
        entry["issues"].append("NOT_A_PINNED_PUBMED_URL")
        return entry
    entry["pmid"] = match.group(1)
    if source_xml is None:
        entry["issues"].append("NO_SOURCE_XML")
        return entry
    entry["source_xml_sha256"] = hashlib.sha256(source_xml).hexdigest()
    try:
        publication = pubmed_metadata(source_xml)
    except (ET.ParseError, ValueError) as error:
        entry["issues"].append("INVALID_PUBMED_XML:" + type(error).__name__)
        return entry
    entry["doi"] = publication["doi"]
    entry["abstract_present"] = "PASS" if publication["abstract_present"] else "PARTIAL"
    if mode == "LIVE_NCBI":
        entry["live_retrieval"] = "PASS"
    if entry["pmid"] != publication["pmid"]:
        entry["bibliographic_identity"] = "FAIL"
        entry["issues"].append("PMID_MISMATCH")
        return entry
    # Strict normalization; no fuzzy title match bypass for conflicting articles.
    if clean(publication["title"]) != clean(ref["title"]):
        entry["bibliographic_identity"] = "FAIL"
        entry["issues"].append("TITLE_MISMATCH")
        return entry
    doi_match = DOI_LOCATOR.fullmatch(ref["locator"])
    if doi_match is not None and (not publication["doi"] or
                                  publication["doi"].lower() != doi_match.group(1).lower()):
        entry["bibliographic_identity"] = "FAIL"
        entry["issues"].append("DOI_MISMATCH")
        return entry
    if doi_match is None:
        entry["issues"].append("DOI_NOT_DECLARED")
        entry["bibliographic_identity"] = "PARTIAL"
    elif mode == "LIVE_NCBI":
        entry["bibliographic_identity"] = "PASS"
    else:
        entry["bibliographic_identity"] = "PARTIAL"
        entry["issues"].append("FIXTURE_NOT_LIVE_PROOF")
    if not publication["abstract_present"]:
        entry["issues"].append("NO_ABSTRACT_IN_SOURCE")
    return entry


def audit_with_literature(payload: dict, allow_network: bool = False,
                          fixture_xml: dict[str, bytes] | None = None,
                          opener=None) -> dict:
    """Augment the existing ASTRA ledger without weakening its safety statuses.

    For a reproducible offline test, provide a {PMID: XML bytes} fixture dict.
    Live calls are opt-in; client input cannot override the PubMed host.
    """
    validate(payload)
    report = audit(payload)
    checks = []
    for claim in payload["claims"]:
        for ref in claim["references"]:
            urlmatch = PMID_URL.fullmatch(ref["url"])
            pmid = urlmatch.group(1) if urlmatch else None
            mode = "NO_NETWORK"
            raw = None
            failure = None
            if pmid and fixture_xml is not None and pmid in fixture_xml:
                raw = fixture_xml[pmid]
                mode = "TEST_FIXTURE"
            elif pmid and allow_network:
                mode = "LIVE_NCBI"
                try:
                    raw = fetch_official_pubmed_xml(pmid, opener=opener)
                except (OSError, ValueError, TimeoutError) as error:
                    failure = "FETCH_FAILED:" + type(error).__name__
            result = verify_reference(ref, raw, mode)
            if failure:
                result["issues"].append(failure)
                result["live_retrieval"] = "FAIL"
                result["bibliographic_identity"] = "UNVERIFIED"
            checks.append({"claim_id": claim["id"], "claim_sha256": hashlib.sha256(claim["text"].encode()).hexdigest(), **result})
    report["literature_bridge"] = {
        "version": "0.2.0", "endpoint": "NCBI PubMed E-utilities efetch; fixed host only",
        "live_network_enabled": allow_network, "publication_checks": checks,
        "live_retrieval_pass_count": sum(x["live_retrieval"] == "PASS" for x in checks),
        "bibliographic_identity_pass_count": sum(x["bibliographic_identity"] == "PASS" for x in checks),
        "scientific_validity": "UNVERIFIED", "clinical_validation": "UNVERIFIED",
        "source_and_model_separation": "A verified PMID/title/DOI cannot validate the medical claim; no entailment model is executed.",
    }
    report["external_network_requests"] = sum(x["retrieval_mode"] == "LIVE_NCBI" for x in checks)
    report.pop("report_sha256", None)
    report["report_sha256"] = sha256(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Bibliographic identity audit, not a medical device")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--allow-network", action="store_true", help="explicitly opt into official NCBI API requests")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        report = audit_with_literature(payload, allow_network=args.allow_network)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        parser.exit(2, f"FAIL: {e}\n")
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    x = report["literature_bridge"]
    print(f"{report['overall_audit_status']} | live IDs {x['bibliographic_identity_pass_count']} | scientific UNVERIFIED | report {report['report_sha256']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

