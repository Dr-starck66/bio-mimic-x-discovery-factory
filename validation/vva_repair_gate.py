#!/usr/bin/env python3
"""BIO-MIMIC X: exploratory patient-level structural repair evidence gate.

This is NOT a validated biomarker, treatment recommendation, or clinical efficacy test.
Accepts measured, independently sourced longitudinal data only. Never inserts numbers.
Pure Python standard library; no network, payments, or automation.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
import math
import random
import statistics
from pathlib import Path

SCHEMA = 'ASTRA-BIOMIMICX/VVA-REPAIR-GATE/1'
# Direction +1: increase is prespecified as desirable for the exact assay;
# -1: decrease is prespecified as desirable. ECM quality MUST be blinded,
# calibrated to a normal architectural reference; collagen amount alone fails.
ENDPOINTS = {
    'epithelium': ('epithelial_thickness_um', +1),
    'barrier': ('barrier_teer_ohm_cm2', +1),
    'matrix': ('ecm_architecture_score', +1),
    'hydration_only': ('hydration_index', +1),
    'symptoms_only': ('symptom_score', -1),
}
REQUIRED = ('subject_id', 'arm', 'timepoint') + tuple(x[0] for x in ENDPOINTS.values())


def _mean(xs):
    return statistics.mean(xs)


def validate(rows):
    if not rows:
        raise ValueError('no observations')
    for i, row in enumerate(rows, 1):
        missing = [key for key in REQUIRED if key not in row or str(row[key]).strip() == '']
        if missing:
            raise ValueError(f'row {i}: missing {missing}')
    subjects = {}
    for i, row in enumerate(rows, 1):
        sid = str(row['subject_id']).strip()
        arm = str(row['arm']).strip()
        time = str(row['timepoint']).strip()
        if arm not in ('active', 'vehicle'):
            raise ValueError(f'row {i}: arm must be active or vehicle')
        if time not in ('pre', 'post'):
            raise ValueError(f'row {i}: timepoint must be pre or post')
        numeric = {}
        for field, _ in ENDPOINTS.values():
            try:
                value = float(row[field])
            except (TypeError, ValueError) as exc:
                raise ValueError(f'row {i}: invalid {field}') from exc
            if not math.isfinite(value):
                raise ValueError(f'row {i}: nonfinite {field}')
            numeric[field] = value
        if numeric['epithelial_thickness_um'] <= 0 or numeric['barrier_teer_ohm_cm2'] <= 0:
            raise ValueError(f'row {i}: invalid nonpositive physical quantity')
        if not 0 <= numeric['ecm_architecture_score'] <= 1:
            raise ValueError(f'row {i}: ECM architecture must be a calibrated 0..1 score')
        if not 0 <= numeric['hydration_index'] <= 1:
            raise ValueError(f'row {i}: hydration index must be 0..1')
        if not 0 <= numeric['symptom_score'] <= 10:
            raise ValueError(f'row {i}: symptom score must be 0..10')
        subj = subjects.setdefault(sid, {'arm': arm, 'measurements': {}})
        if subj['arm'] != arm:
            raise ValueError(f'{sid}: a subject cannot belong to both arms')
        if time in subj['measurements']:
            raise ValueError(f'{sid}: duplicate {time} measurement (pseudoreplication)')
        subj['measurements'][time] = numeric
    groups = {'active': [], 'vehicle': []}
    for sid, subj in subjects.items():
        if set(subj['measurements']) != {'pre', 'post'}:
            raise ValueError(f'{sid}: missing matched pre/post measurement')
        groups[subj['arm']].append(subj['measurements'])
    if min(len(groups['active']), len(groups['vehicle'])) < 6:
        raise ValueError('at least 6 distinct subjects per arm required for this exploratory gate')
    return groups


def two_sided_permutation_p(a, b, *, seed=7127, samples=20000):
    observed = abs(_mean(a) - _mean(b))
    values = a + b
    n = len(a)
    combos = math.comb(len(values), n)
    if combos <= 200000:
        indices = range(len(values))
        total = 0
        more_extreme = 0
        for selected in itertools.combinations(indices, n):
            picked = set(selected)
            xa = [values[i] for i in indices if i in picked]
            xb = [values[i] for i in indices if i not in picked]
            extreme = abs(_mean(xa) - _mean(xb)) >= observed - 1e-10
            more_extreme += bool(extreme)
            total += 1
        return more_extreme / total, 'exact'
    rng = random.Random(seed)
    extreme = 0
    for _ in range(samples):
        shuffled = values.copy()
        rng.shuffle(shuffled)
        extreme += abs(_mean(shuffled[:n]) - _mean(shuffled[n:])) >= observed - 1e-10
    return (extreme + 1) / (samples + 1), 'monte_carlo'


def boot_ci(a, b, *, seed=7127, iterations=2500):
    rng = random.Random(seed)
    vals = []
    for _ in range(iterations):
        a_star = [_mean([a[rng.randrange(len(a))] for _ in range(len(a))])]
        b_star = [_mean([b[rng.randrange(len(b))] for _ in range(len(b))])]
        vals.append(a_star[0] - b_star[0])
    vals.sort()
    return [vals[int(0.025 * (iterations - 1))], vals[int(0.975 * (iterations - 1))]]


def holm_adjust(pvalues):
    keys = sorted(pvalues, key=lambda key: pvalues[key])
    m = len(keys)
    adjusted = {}
    running = 0
    for i, key in enumerate(keys):
        running = max(running, (m - i) * pvalues[key])
        adjusted[key] = min(1.0, running)
    return adjusted


def analyze(rows, *, provenance=None):
    groups = validate(rows)
    report = {
        'schema': SCHEMA,
        'status': 'EXPLORATORY_ONLY',
        'biological_repair_proven': False,
        'clinical_efficacy_proven': False,
        'data_provenance': provenance or 'NOT_ATTESTED',
        'independent_subjects': {key: len(value) for key, value in groups.items()},
        'metrics': {},
        'limitations': [
            'Patient-level randomization/blinding and assay validity require independent verification',
            'ECM architecture score requires blinded scoring against physiological reference',
            'Thickness is not proof of epithelial function; TEER is an in-vitro/ex-vivo proxy',
            'Gene expression, collagen abundance, and HAS1 alone are not regeneration',
            'Long-term durability, withdrawal, adverse effects and human clinical benefit not tested',
        ],
    }
    for idx, (name, (field, direction)) in enumerate(ENDPOINTS.items()):
        a = [direction * (x['post'][field] - x['pre'][field]) for x in groups['active']]
        b = [direction * (x['post'][field] - x['pre'][field]) for x in groups['vehicle']]
        delta = _mean(a) - _mean(b)
        p, method = two_sided_permutation_p(a, b, seed=7127 + idx)
        lo, hi = boot_ci(a, b, seed=5511 + idx)
        report['metrics'][name] = {
            'field': field, 'direction_adjusted_difference_in_differences': round(delta, 8),
            'bootstrap_95pct_CI': [round(lo, 8), round(hi, 8)],
            'two_sided_permutation_p': round(p, 8), 'p_method': method,
        }
    core = ('epithelium', 'barrier', 'matrix')
    q = holm_adjust({name: report['metrics'][name]['two_sided_permutation_p'] for name in core})
    for name in core:
        report['metrics'][name]['holm_p_three_core_endpoints'] = round(q[name], 8)
    solid = all(report['metrics'][name]['direction_adjusted_difference_in_differences'] > 0 and
                report['metrics'][name]['bootstrap_95pct_CI'][0] > 0 and
                q[name] < 0.05 for name in core)
    hydration = report['metrics']['hydration_only']['direction_adjusted_difference_in_differences'] > 0
    symptoms = report['metrics']['symptoms_only']['direction_adjusted_difference_in_differences'] > 0
    report['classification'] = (
        'MULTIDOMAIN_STRUCTURAL_SIGNAL_NOT_REGENERATION_PROOF' if solid
        else 'HYDRATION_OR_SYMPTOMS_ONLY_NOT_STRUCTURAL_REPAIR' if hydration or symptoms
        else 'NO_CONCORDANT_STRUCTURAL_SIGNAL'
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', help='Two pre/post rows per independently identified subject')
    parser.add_argument('--source', default='NOT_ATTESTED', help='Source accession or fingerprint (not self-authenticating)')
    args = parser.parse_args()
    source_bytes = Path(args.csv_file).read_bytes()
    with Path(args.csv_file).open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    report = analyze(rows, provenance=args.source)
    report['input_sha256'] = hashlib.sha256(source_bytes).hexdigest()
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
