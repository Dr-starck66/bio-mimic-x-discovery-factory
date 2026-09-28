#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "state" / "microclean-x"
REPORT_DIR = ROOT / "reports" / "microclean-x"
PUBLIC_DIR = ROOT / "public" / "data" / "microclean-x"

USER_AGENT = "BIO-MIMIC-X-MICROCLEAN/1.0 (+https://github.com/Dr-starck66/bio-mimic-x-discovery-factory)"

QUERIES = [
    "microplastic magnetic nanoparticles removal",
    "microplastics magnetite Fe3O4 removal",
    "microplastic MXene magnetic removal",
    "microplastic chitosan magnetic adsorption",
    "microplastic ferrite magnetic separation",
    "microplastic silica magnetic adsorbent",
    "microplastic biochar magnetic removal",
]

MATERIAL_PATTERNS = {
    "Fe3O4": [r"\bFe3O4\b", r"\bmagnetite\b"],
    "gamma-Fe2O3": [r"\bgamma[- ]?Fe2O3\b", r"\bmaghemite\b"],
    "chitosan": [r"\bchitosan\b"],
    "silica": [r"\bsilica\b", r"\bSiO2\b"],
    "MXene": [r"\bMXene(?:s)?\b", r"\bTi3C2T[xₓ]?\b"],
    "biochar": [r"\bbiochar\b"],
    "alginate": [r"\balginate\b"],
    "nanocellulose": [r"\bnanocellulose\b", r"\bcellulose nanofib"],
    "MOF": [r"\bmetal[- ]organic framework", r"\bMOF(?:s)?\b"],
    "graphene oxide": [r"\bgraphene oxide\b", r"\bGO\b"],
    "ferrite": [r"\bferrite\b"],
}

MAGNETIC_TERMS = re.compile(r"\b(magnetic|magnetite|maghemite|ferrite|Fe3O4|Fe2O3)\b", re.I)
MICROPLASTIC_TERMS = re.compile(r"\bmicroplastics?\b|\bnanoplastics?\b", re.I)

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def sha256_obj(obj):
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

def get_json(url, timeout=25, attempts=3):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    last = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            if i + 1 < attempts:
                time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"request failed after {attempts} attempts: {url}: {last}")

def norm_doi(v):
    if not v:
        return None
    v = str(v).strip().lower()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v)
    v = re.sub(r"^doi:\s*", "", v)
    return v or None

def safe_text(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return " ".join(safe_text(x) for x in v)
    return re.sub(r"\s+", " ", str(v)).strip()

def crossref_search(query, rows=20):
    params = {
        "query": query,
        "rows": rows,
        "select": "DOI,title,abstract,published-print,published-online,author,container-title,type,URL",
    }
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = get_json(url)
    out = []
    for item in data.get("message", {}).get("items", []):
        title = safe_text(item.get("title"))
        abstract = re.sub(r"<[^>]+>", " ", safe_text(item.get("abstract")))
        doi = norm_doi(item.get("DOI"))
        out.append({
            "source": "crossref",
            "doi": doi,
            "title": title,
            "abstract": safe_text(abstract),
            "journal": safe_text(item.get("container-title")),
            "url": safe_text(item.get("URL")),
            "type": safe_text(item.get("type")),
        })
    return out

def europepmc_search(query, rows=20):
    params = {
        "query": query,
        "format": "json",
        "pageSize": rows,
        "resultType": "core",
    }
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(params)
    data = get_json(url)
    out = []
    for item in data.get("resultList", {}).get("result", []):
        doi = norm_doi(item.get("doi"))
        out.append({
            "source": "europepmc",
            "doi": doi,
            "pmid": item.get("pmid"),
            "pmcid": item.get("pmcid"),
            "title": safe_text(item.get("title")),
            "abstract": safe_text(item.get("abstractText")),
            "journal": safe_text(item.get("journalTitle")),
            "url": f"https://europepmc.org/article/MED/{item.get('pmid')}" if item.get("pmid") else "",
            "type": safe_text(item.get("pubType")),
        })
    return out

def evidence_key(r):
    if r.get("doi"):
        return "doi:" + r["doi"]
    if r.get("pmid"):
        return "pmid:" + str(r["pmid"])
    return "title:" + re.sub(r"\W+", "", r.get("title", "").lower())[:180]

def classify(record):
    text = f"{record.get('title','')} {record.get('abstract','')}"
    materials = []
    for material, patterns in MATERIAL_PATTERNS.items():
        if any(re.search(p, text, re.I) for p in patterns):
            materials.append(material)
    return {
        **record,
        "mentions_microplastics": bool(MICROPLASTIC_TERMS.search(text)),
        "mentions_magnetic": bool(MAGNETIC_TERMS.search(text)),
        "materials": sorted(set(materials)),
    }

def dedupe(records):
    merged = {}
    for r in records:
        k = evidence_key(r)
        if k in merged:
            old = merged[k]
            if len(r.get("abstract", "")) > len(old.get("abstract", "")):
                old["abstract"] = r.get("abstract", "")
            old["sources_seen"] = sorted(set(old.get("sources_seen", [old["source"]]) + [r["source"]]))
            for key in ("pmid", "pmcid", "doi", "url", "journal"):
                if not old.get(key) and r.get(key):
                    old[key] = r[key]
        else:
            rr = dict(r)
            rr["sources_seen"] = [r["source"]]
            merged[k] = rr
    return list(merged.values())

def material_signals(records):
    material_to_records = defaultdict(list)
    for r in records:
        if not r["mentions_microplastics"]:
            continue
        for m in r["materials"]:
            material_to_records[m].append(r)

    signals = []
    for material, recs in material_to_records.items():
        independent_ids = {
            r.get("doi") or f"pmid:{r.get('pmid')}" or evidence_key(r)
            for r in recs
        }
        magnetic_count = sum(1 for r in recs if r["mentions_magnetic"])
        direct_context_count = len(recs)
        status = "SCOUT"
        if len(independent_ids) >= 2 and magnetic_count >= 1:
            status = "REVIEW_QUEUE"
        signals.append({
            "material": material,
            "status": status,
            "independent_evidence_count": len(independent_ids),
            "microplastic_context_count": direct_context_count,
            "magnetic_context_count": magnetic_count,
            "dois": sorted({r["doi"] for r in recs if r.get("doi")}),
            "pmids": sorted({str(r["pmid"]) for r in recs if r.get("pmid")}),
            "note": "Literature signal only; not proof of MICROCLEAN-X efficacy, safety, or field readiness."
        })
    return sorted(
        signals,
        key=lambda x: (-x["independent_evidence_count"], -x["magnetic_context_count"], x["material"].lower())
    )

def build_report(records, errors):
    records = [classify(r) for r in dedupe(records)]
    relevant = [r for r in records if r["mentions_microplastics"]]
    signals = material_signals(relevant)
    report = {
        "campaign_id": "MICROCLEAN-X",
        "generated_at": utc_now(),
        "status": "PASS" if relevant else "PARTIAL",
        "policy": {
            "autonomous_candidate_discovery": True,
            "auto_promote_to_validated": False,
            "minimum_independent_evidence_for_review_queue": 2,
            "fail_closed": True,
        },
        "queries": QUERIES,
        "source_errors": errors,
        "counts": {
            "records_total": len(records),
            "microplastic_records": len(relevant),
            "material_signals": len(signals),
            "review_queue_signals": sum(1 for x in signals if x["status"] == "REVIEW_QUEUE"),
        },
        "material_signals": signals,
        "records": relevant,
    }
    report["sha256"] = sha256_obj({
        "status": report["status"],
        "counts": report["counts"],
        "material_signals": report["material_signals"],
        "records": report["records"],
    })
    return report

def run(rows_per_query=15):
    all_records = []
    errors = []
    for query in QUERIES:
        for name, fn in (("crossref", crossref_search), ("europepmc", europepmc_search)):
            try:
                all_records.extend(fn(query, rows=rows_per_query))
            except Exception as e:
                errors.append({"source": name, "query": query, "error": str(e)})
    return build_report(all_records, errors)

def write(report):
    for p in (STATE_DIR, REPORT_DIR, PUBLIC_DIR):
        p.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (STATE_DIR / "live_latest.json").write_text(payload, encoding="utf-8")
    (REPORT_DIR / "live_latest.json").write_text(payload, encoding="utf-8")
    (PUBLIC_DIR / "live_latest.json").write_text(payload, encoding="utf-8")

    top = report["material_signals"][:8]
    lines = [
        "# MICROCLEAN-X Live Evidence Radar",
        "",
        f"- Status: **{report['status']}**",
        f"- Microplastic records: **{report['counts']['microplastic_records']}**",
        f"- Material signals: **{report['counts']['material_signals']}**",
        f"- Review queue signals: **{report['counts']['review_queue_signals']}**",
        f"- Source errors: **{len(report['source_errors'])}**",
        f"- Evidence fingerprint: `{report['sha256']}`",
        "",
        "## Highest-evidence material signals",
        "",
    ]
    if top:
        for x in top:
            lines.append(
                f"- **{x['material']}** — {x['status']} — "
                f"{x['independent_evidence_count']} independent records, "
                f"{x['magnetic_context_count']} magnetic-context records"
            )
    else:
        lines.append("- No evidence signal passed the current extraction rules.")
    lines += [
        "",
        "> REVIEW_QUEUE is a literature-review priority only. It is not a claim of efficacy, safety, or deployability.",
        "",
    ]
    (REPORT_DIR / "LIVE-LATEST.md").write_text("\n".join(lines), encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows-per-query", type=int, default=15)
    p.add_argument("--no-write", action="store_true")
    args = p.parse_args()
    report = run(rows_per_query=args.rows_per_query)
    if not args.no_write:
        write(report)
    print(json.dumps({
        "status": report["status"],
        "counts": report["counts"],
        "source_errors": len(report["source_errors"]),
        "sha256": report["sha256"],
    }, ensure_ascii=False))
    return 0 if report["counts"]["microplastic_records"] > 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
