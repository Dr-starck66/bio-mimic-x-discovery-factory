#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

try:
    from factory.external_validation_gate import build_report as build_external_validation_report
    from factory.commercial_evidence_gate import build_report as build_commercial_evidence_report
except ModuleNotFoundError:
    from external_validation_gate import build_report as build_external_validation_report
    from commercial_evidence_gate import build_report as build_commercial_evidence_report

ROOT = Path(__file__).resolve().parents[1]
PROGRAMS_PATH = ROOT / "state" / "factory" / "programs.json"
MEMORY_PATH = ROOT / "state" / "factory" / "long_term_memory.json"
REGISTRY_PATH = ROOT / "factory" / "million_euro_validation_registry.json"
EXTERNAL_VALIDATION_PATH = ROOT / "factory" / "external_validation_registry.json"
COMMERCIAL_EVIDENCE_PATH = ROOT / "factory" / "commercial_evidence_registry.json"
REPORT_DIR = ROOT / "reports" / "million-euro-evidence"
PUBLIC_DIR = ROOT / "public" / "data" / "million-euro-evidence"

NON_SPECIES_TITLES = {
    "this review",
    "these findings",
    "this study",
    "this narrative",
    "emerging evidence",
    "wound healing",
    "insulin resistance",
    "neurological disorders",
    "pituitary adenylate",
}

SUSPECT_GENE_TOKENS = {
    "NF-", "OCTA", "SD-OCT", "PBD", "PCNA-", "RT-PCR",
    "EIS", "IAV", "ICTV", "RABV", "NIH-", "USDA",
    "AI", "AI-", "AMP-", "BR-", "C-", "CIRI-", "CNS-",
    "COVID-19", "CRISPR-", "DNA-", "MEDLINE", "SARS-",
    "HOMA-IR", "NAFLD", "OGTT", "MASLD", "HDL-C",
}

GENE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9.-]{1,14}$")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_suspect_gene(token: str) -> bool:
    token = (token or "").strip()
    if not token:
        return True
    if token in SUSPECT_GENE_TOKENS:
        return True
    if token.endswith("-"):
        return True
    if not GENE_PATTERN.match(token):
        return True
    return False


def clean_genes(tokens: Iterable[str]) -> Tuple[List[str], List[str]]:
    clean, suspect = [], []
    for token in tokens or []:
        (suspect if is_suspect_gene(token) else clean).append(token)
    return sorted(set(clean)), sorted(set(suspect))


def classify_program(program: Mapping[str, Any]) -> Dict[str, Any]:
    title = str(program.get("title") or "").strip()
    genes, suspect = clean_genes(program.get("genes") or [])
    reasons: List[str] = []

    if title.lower() in NON_SPECIES_TITLES:
        reasons.append("NON_SPECIES_TEXT_FRAGMENT")
    if program.get("taxon_verified") is not True:
        reasons.append("TAXON_NOT_VERIFIED")
    if len(program.get("sources") or []) < 2:
        reasons.append("INSUFFICIENT_INDEPENDENT_SOURCES")
    if not program.get("mechanisms"):
        reasons.append("NO_MECHANISM")
    if suspect:
        reasons.append("SUSPECT_GENE_EXTRACTION")

    eligible = not any(
        r in reasons
        for r in (
            "NON_SPECIES_TEXT_FRAGMENT",
            "TAXON_NOT_VERIFIED",
            "INSUFFICIENT_INDEPENDENT_SOURCES",
            "NO_MECHANISM",
        )
    )
    return {
        "id": program.get("id"),
        "title": title,
        "status": program.get("status"),
        "committee_score": int(program.get("committee_score") or 0),
        "priority_rank": program.get("priority_rank"),
        "taxon_verified": program.get("taxon_verified") is True,
        "sources": list(program.get("sources") or []),
        "source_count": len(program.get("sources") or []),
        "mechanisms": list(program.get("mechanisms") or []),
        "clean_genes": genes,
        "suspect_genes": suspect,
        "eligible_for_investor_package": eligible,
        "quality_flags": reasons,
    }


def external_registry_points(entry: Mapping[str, Any]) -> int:
    sources = entry.get("literature_evidence") or []
    primary = sum(1 for s in sources if s.get("role") == "primary")
    recent = sum(1 for s in sources if int(s.get("year") or 0) >= 2024)
    bridge = 1 if entry.get("human_bridge", {}).get("human_symbol") else 0
    return min(30, primary * 4 + recent * 2 + bridge * 6)


def candidate_score(row: Mapping[str, Any], registry_entry: Mapping[str, Any]) -> int:
    score = int(row.get("committee_score") or 0)
    score += 12 if row.get("status") == "ACTIVE" else 0
    score += 12 if row.get("taxon_verified") else 0
    score += min(12, 3 * int(row.get("source_count") or 0))
    score += min(16, 4 * len(row.get("mechanisms") or []))
    score += external_registry_points(registry_entry)
    score -= min(20, 5 * len(row.get("suspect_genes") or []))
    return score


def select_flagship(rows: List[Dict[str, Any]], registry: Mapping[str, Any]) -> Dict[str, Any]:
    ranked = []
    candidates = registry.get("candidates") or {}
    for row in rows:
        if not row["eligible_for_investor_package"]:
            continue
        reg = candidates.get(row["title"], {})
        if not reg:
            continue
        ranked.append({
            **row,
            "registry": reg,
            "investor_evidence_score": candidate_score(row, reg),
        })
    if not ranked:
        raise RuntimeError("No investor-eligible candidate has a curated evidence registry entry")
    ranked.sort(key=lambda x: (-x["investor_evidence_score"], x["title"]))
    return ranked[0]


def memory_hygiene(memory: Mapping[str, Any]) -> Dict[str, Any]:
    subjects = list((memory.get("claims") or {}).keys())
    suspicious = []
    for s in subjects:
        low = s.strip().lower()
        if low in NON_SPECIES_TITLES or low in {"its neuroprotection", "mechanisms and", "mesenchymal stem"}:
            suspicious.append(s)
    return {
        "claim_count": len(subjects),
        "suspicious_subjects": sorted(suspicious),
        "suspicious_subject_count": len(suspicious),
    }


def readiness(flagship: Mapping[str, Any], hygiene: Mapping[str, Any], external_validation: Mapping[str, Any], commercial_evidence: Mapping[str, Any]) -> Dict[str, Any]:
    reg = flagship["registry"]
    literature = reg.get("literature_evidence") or []
    primary_count = sum(1 for s in literature if s.get("role") == "primary")
    recent_count = sum(1 for s in literature if int(s.get("year") or 0) >= 2024)

    external_report = build_external_validation_report(external_validation)
    external_status = external_report["status"]
    external_evidence = f"{external_report['accepted_supporting_validations']} supporting validation(s); report {external_report['sha256']}"
    commercial_report = build_commercial_evidence_report(commercial_evidence)
    commercial_status = commercial_report["status"]
    commercial_evidence_text = f"{commercial_report['verified_entries']} verified commercial evidence entrie(s); report {commercial_report['sha256']}"

    gates = [
        {"gate": "working_product", "status": "PASS", "evidence": "BIO-MIMIC X V4 interface + automated research pipeline"},
        {"gate": "reproducible_provenance", "status": "PASS", "evidence": "source IDs, claim ledger and SHA-256 replay artifacts"},
        {"gate": "replicated_flagship_literature", "status": "PASS" if primary_count >= 3 else "PARTIAL", "evidence": f"{primary_count} primary studies in curated registry"},
        {"gate": "recent_independent_support", "status": "PASS" if recent_count >= 1 else "PARTIAL", "evidence": f"{recent_count} registry studies from 2024+"},
        {"gate": "portfolio_data_hygiene", "status": "PARTIAL" if hygiene["suspicious_subject_count"] else "PASS", "evidence": f"{hygiene['suspicious_subject_count']} known suspicious memory subjects isolated from investor package"},
        {"gate": "provider_backed_human_bridge", "status": "PARTIAL" if reg.get("human_bridge") else "UNVERIFIED", "evidence": reg.get("human_bridge", {}).get("status", "not available")},
        {"gate": "independent_lab_validation_of_biomimic_output", "status": external_status, "evidence": external_evidence},
        {"gate": "formal_ip_novelty_freedom_to_operate", "status": "UNVERIFIED", "evidence": "requires professional prior-art/FTO review"},
        {"gate": "paying_customers_or_contracts", "status": commercial_status, "evidence": commercial_evidence_text},
    ]
    weights = {
        "working_product": 15,
        "reproducible_provenance": 15,
        "replicated_flagship_literature": 15,
        "recent_independent_support": 10,
        "portfolio_data_hygiene": 10,
        "provider_backed_human_bridge": 10,
        "independent_lab_validation_of_biomimic_output": 10,
        "formal_ip_novelty_freedom_to_operate": 10,
        "paying_customers_or_contracts": 5,
    }
    factor = {"PASS": 1.0, "PARTIAL": 0.5, "UNVERIFIED": 0.0, "FAIL": 0.0}
    score = round(sum(weights[g["gate"]] * factor[g["status"]] for g in gates))
    return {
        "status": "PASS" if score >= 85 and all(g["status"] != "FAIL" for g in gates) else "PARTIAL",
        "score_100": score,
        "valuation_statement": "TECHNOLOGY/COMPANY_VALUATION_CASE_NOT_CASH_EXIT_PROOF",
        "gates": gates,
    }


def build_package(programs: Mapping[str, Any], memory: Mapping[str, Any], registry: Mapping[str, Any], external_validation: Mapping[str, Any] | None = None, commercial_evidence: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    rows = [classify_program(p) for p in programs.get("programs") or []]
    flagship = select_flagship(rows, registry)
    hygiene = memory_hygiene(memory)
    external_validation = external_validation or {"validations": []}
    commercial_evidence = commercial_evidence or {"evidence": []}
    readiness_result = readiness(flagship, hygiene, external_validation, commercial_evidence)

    package = {
        "package": "BIO-MIMIC X — MILLION-EURO EVIDENCE PACKAGE",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": readiness_result["status"],
        "valuation_readiness": readiness_result,
        "flagship": flagship,
        "portfolio": {
            "total_programs": len(rows),
            "eligible_programs": sum(1 for r in rows if r["eligible_for_investor_package"]),
            "excluded_programs": sum(1 for r in rows if not r["eligible_for_investor_package"]),
            "cleaned_rows": rows,
        },
        "memory_hygiene": hygiene,
        "external_validation": build_external_validation_report(external_validation),
        "commercial_evidence": build_commercial_evidence_report(commercial_evidence),
        "claim_boundaries": [
            "BIO-MIMIC X prioritizes scientific hypotheses; it does not establish clinical efficacy.",
            "Literature support is not independent validation of a BIO-MIMIC X-generated prediction.",
            "A provider-backed orthology/target bridge is not proof of therapeutic efficacy.",
            "No patentability, freedom-to-operate or company valuation is asserted by this package.",
        ],
        "next_value_gates": [
            "obtain written independent expert/lab assessment of the flagship dossier",
            "run or commission the pre-registered causal perturbation experiment",
            "complete professional prior-art and freedom-to-operate review",
            "secure at least one paid pilot, LOI or research collaboration",
        ],
    }
    package["sha256"] = sha256_json({k: v for k, v in package.items() if k not in {"generated_at", "sha256"}})
    return package


def markdown_due_diligence(pkg: Mapping[str, Any]) -> str:
    f = pkg["flagship"]
    r = pkg["valuation_readiness"]
    evidence = f["registry"].get("literature_evidence") or []
    lines = [
        "# BIO-MIMIC X — Million-Euro Evidence Package",
        "",
        f"- Status: **{pkg['status']}**",
        f"- Readiness score: **{r['score_100']}/100**",
        f"- Flagship: **{f['title']}**",
        f"- Investor evidence score: **{f['investor_evidence_score']}**",
        f"- Evidence fingerprint: `{pkg['sha256']}`",
        "",
        "## Flagship thesis",
        "",
        f["registry"]["thesis"],
        "",
        "## Why this candidate survived the hygiene gate",
        "",
        f"- Taxon verified: **{f['taxon_verified']}**",
        f"- Independent platform sources: **{f['source_count']}**",
        f"- Mechanisms: **{', '.join(f['mechanisms'])}**",
        f"- Suspect gene tokens in current program: **{len(f['suspect_genes'])}**",
        "",
        "## Curated literature evidence",
        "",
    ]
    for s in evidence:
        lines.append(f"- {s['year']} — {s['id']} — {s['title']} ({s['role']})")
    hb = f["registry"].get("human_bridge") or {}
    lines += [
        "",
        "## Translation bridge",
        "",
        f"- Animal anchor: **{hb.get('animal_anchor', 'UNVERIFIED')}**",
        f"- Human target: **{hb.get('human_symbol', 'UNVERIFIED')}**",
        f"- Status: **{hb.get('status', 'UNVERIFIED')}**",
        "- Boundary: target/orthology context is not clinical efficacy.",
        "",
        "## Due-diligence gates",
        "",
    ]
    for gate in r["gates"]:
        lines.append(f"- **{gate['gate']}** — {gate['status']} — {gate['evidence']}")
    lines += [
        "",
        "## Excluded contamination",
        "",
        f"- Programs inspected: **{pkg['portfolio']['total_programs']}**",
        f"- Investor-eligible after hard filtering: **{pkg['portfolio']['eligible_programs']}**",
        f"- Excluded: **{pkg['portfolio']['excluded_programs']}**",
        f"- Suspicious long-term-memory subjects isolated: **{pkg['memory_hygiene']['suspicious_subject_count']}**",
        "",
        "## Remaining blockers before a 1 M€ cash-exit claim",
        "",
        "1. Independent external validation of a BIO-MIMIC X-generated output.",
        "2. Causal experimental result, not only literature/orthology support.",
        "3. Professional IP novelty/FTO review.",
        "4. Commercial proof such as a paid pilot, LOI or research contract.",
        "",
        "This file is a diligence artifact, not a valuation, medical claim or patentability opinion.",
        "",
    ]
    return "\n".join(lines)


def markdown_validation_request(pkg: Mapping[str, Any]) -> str:
    f = pkg["flagship"]
    reg = f["registry"]
    return "\n".join([
        "# Independent validation brief — BIO-MIMIC X",
        "",
        f"Candidate: **{f['title']}**",
        "",
        "## Question for an independent expert",
        "",
        reg["external_validation_question"],
        "",
        "## What BIO-MIMIC X is claiming",
        "",
        reg["thesis"],
        "",
        "## What BIO-MIMIC X is NOT claiming",
        "",
        "- No clinical efficacy.",
        "- No proof that the proposed human bridge is causal.",
        "- No patentability claim.",
        "",
        "## Requested review",
        "",
        "Please classify the dossier as one of: SUPPORTS_FURTHER_TESTING / INTERESTING_BUT_WEAK / NOT_NOVEL / SCIENTIFICALLY_FLAWED, and identify the single experiment that would most efficiently falsify the thesis.",
        "",
        f"Package fingerprint: `{pkg['sha256']}`",
        "",
    ])


def markdown_ip_register(pkg: Mapping[str, Any]) -> str:
    f = pkg["flagship"]
    return "\n".join([
        "# BIO-MIMIC X — IP / diligence register",
        "",
        "## Potential protectable layers to review with counsel",
        "",
        "1. The evidence-first cross-species discovery and falsification workflow as an integrated system.",
        "2. Specific ranking, negative-memory and provider-verification combinations where genuinely novel.",
        "3. New experimentally validated compositions, uses or methods arising from a BIO-MIMIC X discovery, if novel and non-obvious.",
        "",
        "## Flagship disclosure",
        "",
        f"- Candidate: **{f['title']}**",
        f"- Thesis: {f['registry']['thesis']}",
        f"- Package SHA-256: `{pkg['sha256']}`",
        "",
        "## Current status",
        "",
        "- Patentability: **UNVERIFIED**",
        "- Freedom to operate: **UNVERIFIED**",
        "- External inventor/lab contribution: **NONE RECORDED IN THIS PACKAGE**",
        "- Repository is private; no public-source-code license was found during the diligence build.",
        "",
        "This register preserves provenance and questions for counsel. It is not legal advice and must not be represented as a patentability opinion.",
        "",
    ])


def write_outputs(pkg: Mapping[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(pkg, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (REPORT_DIR / "latest.json").write_text(payload, encoding="utf-8")
    (PUBLIC_DIR / "latest.json").write_text(payload, encoding="utf-8")

    (REPORT_DIR / "DUE-DILIGENCE.md").write_text(markdown_due_diligence(pkg), encoding="utf-8")
    (REPORT_DIR / "EXTERNAL-VALIDATION-BRIEF.md").write_text(markdown_validation_request(pkg), encoding="utf-8")
    (REPORT_DIR / "IP-RISK-REGISTER.md").write_text(markdown_ip_register(pkg), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--programs", default=str(PROGRAMS_PATH))
    parser.add_argument("--memory", default=str(MEMORY_PATH))
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--external-validation", default=str(EXTERNAL_VALIDATION_PATH))
    parser.add_argument("--commercial-evidence", default=str(COMMERCIAL_EVIDENCE_PATH))
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()

    pkg = build_package(load_json(Path(args.programs)), load_json(Path(args.memory)), load_json(Path(args.registry)), load_json(Path(args.external_validation)), load_json(Path(args.commercial_evidence)))
    if not args.no_write:
        write_outputs(pkg)
    print(json.dumps({
        "status": pkg["status"],
        "readiness_score": pkg["valuation_readiness"]["score_100"],
        "flagship": pkg["flagship"]["title"],
        "eligible_programs": pkg["portfolio"]["eligible_programs"],
        "excluded_programs": pkg["portfolio"]["excluded_programs"],
        "sha256": pkg["sha256"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
