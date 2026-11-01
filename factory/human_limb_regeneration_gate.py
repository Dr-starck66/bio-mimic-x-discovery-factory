#!/usr/bin/env python3
"""Evidence gate for the AXOLOTL -> HUMAN limb-regeneration question.

A successful molecular orthology match is NOT a successful regeneration
experiment. The only automated outcome supported by the currently registered
evidence is UNVERIFIED human whole-limb regeneration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "reports/factory/HUMAN-BRIDGE-LATEST.md"
EXTERNAL = ROOT / "factory/external_validation_registry.json"
GEO = ROOT / "validation/NOTE-INTERPRETATION-GEO-2026-10-27.md"
OUTPUT = ROOT / "reports/factory/HUMAN-LIMB-REGENERATION-GATE-LATEST.json"
MARKDOWN = ROOT / "reports/factory/HUMAN-LIMB-REGENERATION-GATE-LATEST.md"

ANIMAL_EVIDENCE = [
    {
        "pmid": "23690624",
        "species": "Ambystoma mexicanum",
        "endpoint": "Macrophage depletion blocks limb regrowth and promotes fibrosis",
        "level": "ANIMAL_CAUSAL_PERTURBATION",
        "human_efficacy": False,
    },
    {
        "pmid": "40399677",
        "species": "Ambystoma mexicanum",
        "endpoint": "Hand2-Shh positional memory reprogramming in limb regeneration",
        "level": "ANIMAL_CAUSAL_PERTURBATION",
        "human_efficacy": False,
    },
]
HUMAN_CONTEXT = {
    "pmid": "42847253",
    "level": "COMPARATIVE_REVIEW",
    "interpretation": "Mammalian regeneration is largely limited to distal digit tips; "
                      "a review does not demonstrate human whole-limb regrowth.",
    "human_efficacy": False,
}


def _integer(pattern: str, text: str) -> int:
    found = re.search(pattern, text, re.MULTILINE)
    if not found:
        raise ValueError("missing verified human-bridge summary: " + pattern)
    return int(found.group(1))


def build_report(bridge_markdown: str, external_registry: dict, geo_note: str) -> dict:
    total = _integer(r"^Supported claims:\s*(\d+)\s*$", bridge_markdown)
    strict = _integer(r"^Strict orthology:\s*(\d+)/\d+", bridge_markdown)
    translated = _integer(r"^Verified human translation:\s*(\d+)/\d+", bridge_markdown)
    if total < 1 or not (0 <= strict <= translated <= total):
        raise ValueError("incoherent human-bridge coverage")
    if not isinstance(external_registry.get("validations"), list):
        raise ValueError("external validation registry must contain a list")

    # Preserve BOTH original GEO outcomes. A single positive cohort is not
    # independent replication under the preregistered two-cohort rule.
    geo_has_failure = bool(
        re.search(r"^\|\s*GSE74387\s*\|[^\n]*\*\*FAIL\*\*", geo_note, re.MULTILINE)
        and re.search(r"^\|\s*GSE113081\s*\|[^\n]*\*\*PASS individuel\*\*", geo_note, re.MULTILINE)
        and "n'est PAS satisfait" in geo_note
    )
    geo_status = "FAIL_PRE_REGISTERED_REPLICATION" if geo_has_failure else "UNVERIFIED_SOURCE"

    result = {
        "schema": "BIO-MIMIC-X/HUMAN-LIMB-REGENERATION-GATE/1",
        "date": "2026-11-01",
        "scientific_question": "Can known axolotl limb-regeneration mechanisms work in human tissues?",
        "animal_evidence": ANIMAL_EVIDENCE,
        "human_context": HUMAN_CONTEXT,
        "human_bridge": {
            "supported_claims": total,
            "strict_orthology_candidates": strict,
            "translated_candidates": translated,
            "interpretation": "Human target identification only; not functional human regeneration",
        },
        "retro_geo": {
            "GSE74387": "FAIL_ORIGINAL_CI_INCLUDES_ZERO" if geo_has_failure else "UNVERIFIED",
            "GSE113081": "PASS_SINGLE_COHORT_ONLY" if geo_has_failure else "UNVERIFIED",
            "global_replication": geo_status,
            "negative_controls_preserved": geo_has_failure,
            "source": "validation/NOTE-INTERPRETATION-GEO-2026-10-27.md",
        },
        "external_review_registry_entries": len(external_registry["validations"]),
        "human_primary_tissue_functional_perturbation": "UNVERIFIED",
        "human_whole_limb_structural_and_functional_regrowth": "UNVERIFIED",
        "prospective_independent_biological_replication": "UNVERIFIED",
        "human_limb_regeneration_status": "UNVERIFIED",
        "reason": (
            "Animal perturbations and human molecular targets cannot establish "
            "human limb regeneration; no authenticated, independent human-tissue "
            "functional experiment or whole-limb regeneration outcome is "
            "present in the evaluated repository evidence."
        ),
        "negative_claims": [
            "No human whole-limb regenerative efficacy inferred from orthology.",
            "No successful two-cohort GEO replication inferred from one PASS.",
            "No external review, even positive, substitutes for human biological experiments.",
            "Human digit-tip repair or human fibroblast responses do not establish whole-limb regrowth.",
        ],
        "next_falsifiable_test": (
            "Institutionally supervised, preregistered human primary-cell study "
            "testing macrophage/ECM effects on fibrosis with matched negative "
            "controls; evaluate positional signalling separately and never "
            "equate an in-vitro response with limb regrowth."
        ),
    }
    canonical = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    result["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result


def render_markdown(report: dict) -> str:
    b = report["human_bridge"]
    g = report["retro_geo"]
    return "\n".join([
        "# BIO-MIMIC X — Axolotl / humain : contrôle de preuve",
        "",
        "**Régénération complète d'un membre humain : UNVERIFIED**",
        "",
        f"- Cibles humaines liées à des espèces du portefeuille : {b['translated_candidates']}/{b['supported_claims']} ; orthologie stricte : {b['strict_orthology_candidates']}/{b['supported_claims']}.",
        "- Ces comptes ne mesurent ni activité régénératrice humaine ni homologie spécifique axolotl-humain.",
        "- Axolotl : macrophages indispensables, PMID 23690624 ; mémoire Hand2–Shh, PMID 40399677.",
        "- Contexte mammifères : revue PMID 42847253, régénération essentiellement des extrémités de doigts.",
        f"- Réplication rétrospective Acomys/Mus : {g['global_replication']} (GSE74387 FAIL, GSE113081 PASS individuel ; contrôles négatifs préservés).",
        f"- Entrées au registre de revue externe : {report['external_review_registry_entries']} (ne prouvent pas une validation biologique).",
        "- Expérience causale contrôlée sur cellules humaines : UNVERIFIED.",
        "- Repousse anatomique et fonctionnelle de membre humain : UNVERIFIED.",
        "",
        "## Expérience prioritaire falsifiable",
        report["next_falsifiable_test"],
        "",
        "Aucun essai humain, traitement ou intervention biologique n'a été exécuté par ce programme.",
        "Une étude sur fibroblastes humains n'établirait pas à elle seule la repousse d'un membre.",
        "",
        f"SHA-256 du rapport canonique : `{report['sha256']}`",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    report = build_report(
        BRIDGE.read_text(encoding="utf-8"),
        json.loads(EXTERNAL.read_text(encoding="utf-8")),
        GEO.read_text(encoding="utf-8"),
    )
    if not args.no_write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        MARKDOWN.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "software_gate": "PASS",
        "human_limb_regeneration": report["human_limb_regeneration_status"],
        "retro_geo": report["retro_geo"]["global_replication"],
        "verified_human_targets": report["human_bridge"]["translated_candidates"],
        "sha256": report["sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
