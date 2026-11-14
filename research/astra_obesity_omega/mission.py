"""ASTRA OBESITY Ω: fail-closed research dossier. Not a diagnostic or therapeutic system.
Reuses BIO-MIMIC X hypothesis, adversarial debate, and experiment-planning engines.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'factory'))
from hypothesis_engine import generate_hypotheses
from debate_engine import debate_hypotheses
from experiment_planner import plan_experiments

SEED_PATH = Path(__file__).with_name('research_seed.json')
ALLOWED_STUDY_DESIGNS = {'observational', 'expert_consensus', 'public_health_guidance', 'clinical_guideline', 'dataset_catalogue'}


def canonical_sha(value: object) -> str:
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def validate_seed(seed: dict) -> list[str]:
    """Fail closed: no unverified reference or invented human-efficacy finding."""
    errors = []
    sources = seed.get('sources', [])
    if not isinstance(sources, list) or not sources:
        return ['sources_missing']
    source_ids = [s.get('id') for s in sources]
    if None in source_ids or len(set(source_ids)) != len(source_ids):
        errors.append('duplicate_or_missing_source_id')
    for s in sources:
        u = urlparse(str(s.get('url', '')))
        if u.scheme != 'https' or not u.netloc:
            errors.append('source_url_not_https:' + str(s.get('id')))
        if s.get('design') not in ALLOWED_STUDY_DESIGNS:
            errors.append('unknown_study_design:' + str(s.get('id')))
        if not s.get('published'):
            errors.append('publication_date_missing:' + str(s.get('id')))
    ids = set(source_ids)
    questions = seed.get('questions', [])
    if not questions:
        errors.append('questions_missing')
    for q in questions:
        qid = str(q.get('id', 'missing'))
        citations = q.get('source_ids', [])
        if not citations or len(set(citations)) != len(citations) or not set(citations).issubset(ids):
            errors.append('invalid_question_provenance:' + qid)
        if q.get('claims_clinical_efficacy') is not False:
            errors.append('clinical_efficacy_claim_forbidden:' + qid)
        if not q.get('falsifier'):
            errors.append('missing_falsifier:' + qid)
        if q.get('stage') != 'RESEARCH_HYPOTHESIS':
            errors.append('invalid_hypothesis_stage:' + qid)
        if q.get('individual_data_present'):
            errors.append('individual_data_not_permitted:' + qid)
        if q.get('diagnostic_basis') == 'BMI_ALONE':
            errors.append('bmi_alone_cannot_diagnose_clinical_obesity:' + qid)
    return sorted(set(errors))


def build_dossier(seed: dict) -> dict:
    errors = validate_seed(seed)
    if errors:
        return {'status': 'FAIL', 'errors': errors, 'clinical_efficacy_demonstrated': False}
    by_id = {s['id']: s for s in seed['sources']}
    items = []
    for q in seed['questions']:
        refs = [by_id[sid] for sid in q['source_ids']]
        designs = sorted(set(s['design'] for s in refs))
        # Deliberately no fake independent-validation count: a guideline can cite an
        # observational study, and publications may share participants.
        claim = {'subject': q['subject'], 'mechanisms': q.get('mechanisms', []),
                 'genes': q.get('candidate_genes', []), 'sources': [s['url'] for s in refs]}
        program = {'id': q['id']}
        counterfactual = {'counterfactual_tests': q['counter_tests']}
        hypotheses = generate_hypotheses(program, claim, causal_plan=counterfactual)
        audit = {'flags': [
            'correlation not causation',
            'human clinical efficacy not established',
            'no independent patient-level replication in this dossier',
            'health equity and long-term safety require separate evaluation',
        ]}
        debate = debate_hypotheses(hypotheses, claim, audit, counterfactual)
        experiments = plan_experiments(program, claim, hypotheses, debate, counterfactual)
        items.append({
            'question_id': q['id'], 'question': q['subject'],
            'source_ids': q['source_ids'], 'source_designs': designs,
            'source_urls': [s['url'] for s in refs],
            'source_status': 'VERIFIED_PUBLIC_METADATA_NOT_RAW_COHORT_REPLICATION',
            'human_data_independently_analyzed': False,
            'hypotheses': hypotheses, 'adversarial_review': debate,
            'experiments': experiments,
            'primary_falsifier': q['falsifier'],
            'clinical_efficacy_demonstrated': False,
            'status': 'PARTIAL',
        })
    dossier = {
        'project': 'ASTRA OBESITY Ω', 'schema': 'astra-obesity-research/0.1',
        'status': 'PARTIAL', 'budget_additional_eur': 0,
        'not_medical_advice': True, 'clinical_efficacy_demonstrated': False,
        'worldwide_solution_demonstrated': False,
        'global_scope': ['mechanism', 'clinical-vs-preclinical', 'long-term-care', 'equity'],
        'reused_executables': [
            'factory/hypothesis_engine.py::generate_hypotheses',
            'factory/debate_engine.py::debate_hypotheses',
            'factory/experiment_planner.py::plan_experiments',
        ],
        'sources': seed['sources'], 'research_questions': items,
        'scientific_gaps': [
            'independent patient-level data with authorized access',
            'predeclared cross-population validation and calibration',
            'non-BMI organ-function clinical outcome definition',
            'longitudinal safety and durability',
            'causal perturbation and independent replication',
        ],
    }
    dossier['sha256'] = canonical_sha(dossier)
    return dossier


def main() -> int:
    seed = json.loads(SEED_PATH.read_text(encoding='utf-8'))
    dossier = build_dossier(seed)
    print(json.dumps(dossier, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if dossier['status'] == 'PARTIAL' else 1


if __name__ == '__main__':
    raise SystemExit(main())
