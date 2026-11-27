#!/usr/bin/env python3
"""Read-only provenance gate. This audits claims, NOT HIV therapeutic efficacy."""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_OUTCOMES = {
    'post_treatment_control', 'reservoir_measurement', 'exceptional_remission',
    'gene_excision_research', 'reservoir_intervention_research'
}

def audit_evidence(data):
    problems = []
    studies = data.get('studies', [])
    if data.get('cure_established_for_general_population') is not False:
        problems.append('No generally applicable HIV cure has been established')
    if not studies:
        problems.append('No studies')
    seen = set()
    for row in studies:
        name = row.get('id')
        if not name or name in seen:
            problems.append(f'Duplicate or missing study id: {name}')
        seen.add(name)
        p = urlparse(row.get('source', ''))
        if p.scheme != 'https' or not p.netloc or p.username or p.password:
            problems.append(f'{name}: invalid source')
        if row.get('outcome_category') not in ALLOWED_OUTCOMES:
            problems.append(f'{name}: missing or invalid outcome category')
        if not row.get('type') or not row.get('limitation'):
            problems.append(f'{name}: missing design or limitations')
        if row.get('eradication_demonstrated') is not False:
            problems.append(f'{name}: unsupported eradication claim')
    safety = data.get('clinical_safety', {})
    if safety.get('art_stop_without_specialist_supervised_trial') != 'PROHIBITED':
        problems.append('Unsafe treatment interruption policy')
    if safety.get('no_self_experimentation') is not True:
        problems.append('Unsafe self-experimentation policy')
    return {
        'status': 'PASS' if not problems else 'FAIL',
        'studies_checked': len(studies),
        'problems': problems,
        'clinical_cure_proven': False,
        'status_scope': 'evidence-schema consistency only, not clinical validation'
    }

def main():
    data = json.loads(Path(__file__).with_name('evidence.json').read_text(encoding='utf-8'))
    result = audit_evidence(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result['status'] != 'PASS')

if __name__ == '__main__':
    raise SystemExit(main())
