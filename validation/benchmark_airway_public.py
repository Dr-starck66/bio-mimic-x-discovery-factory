#!/usr/bin/env python3
"""Reproduce BIO-MIMIC X public Airway 3-v-3 pipeline stress test.

Source: public Himes et al. / Bioconductor airway gene counts, mirrored at
https://raw.githubusercontent.com/bioconnector/workshops/master/data/airway_rawcounts.csv

Important: Airway is a donor-paired biological experiment. Subsampling 3 pairs
and ignoring blocking is ONLY an I/O / mathematical stress test, NOT a valid
differential expression inference or benchmark of biological accuracy.

Usage: python benchmark_airway_public.py --input /path/to/airway_rawcounts.csv
       python benchmark_airway_public.py --self-test

No downloads, credentials or installed third-party packages are required.
"""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import median

EXPECTED_HEADER = [
    'ensgene', 'SRR1039508', 'SRR1039509', 'SRR1039512',
    'SRR1039513', 'SRR1039516', 'SRR1039517', 'SRR1039520',
    'SRR1039521'
]
# Three control donors then their three matching treated conditions.
SAMPLE_INDICES = [1, 3, 5, 2, 4, 6]


def read_counts(path):
    with open(path, newline='', encoding='utf-8-sig') as source:
        rows = csv.reader(source)
        header = next(rows)
        if header != EXPECTED_HEADER:
            raise ValueError('Unexpected headers or sample order; audit input file')
        seen = set()
        counts = []
        for lineno, row in enumerate(rows, start=2):
            if len(row) != len(header):
                raise ValueError(f'Malformed line {lineno}')
            gene = row[0]
            if not gene or gene in seen:
                raise ValueError(f'Duplicate or missing gene identifier at line {lineno}')
            try:
                v = [int(row[i]) for i in SAMPLE_INDICES]
            except ValueError as exc:
                raise ValueError(f'Non-integer count at {lineno}') from exc
            if any(x < 0 for x in v):
                raise ValueError(f'Negative count at {lineno}')
            seen.add(gene)
            counts.append((gene, v))
        return counts


def analyze(data):
    if not data:
        raise ValueError('No data')
    ratio_samples = [[] for _ in range(6)]
    for gene, v in data:
        if all(x > 0 for x in v):
            gm = math.exp(sum(math.log(x) for x in v) / 6)
            for j, x in enumerate(v):
                ratio_samples[j].append(x / gm)
    if not ratio_samples[0]:
        raise ValueError('Cannot normalize: no genes expressed in all six samples')
    factors = [median(x) for x in ratio_samples]
    normalized = [[x / factors[i] for i, x in enumerate(v)] for _, v in data]

    outcomes = []
    for case_idx in itertools.combinations(range(6), 3):
        ctrl_idx = [i for i in range(6) if i not in case_idx]
        up = down = 0
        for v in normalized:
            case = [v[i] for i in case_idx]
            ctrl = [v[i] for i in ctrl_idx]
            cm, wm = sum(case) / 3, sum(ctrl) / 3
            if (cm + wm) / 2 < 10:
                continue
            if min(case) > max(ctrl) and cm + 1 >= 2 * (wm + 1):
                up += 1
            if max(case) < min(ctrl) and wm + 1 >= 2 * (cm + 1):
                down += 1
        outcomes.append({'case_samples': [i + 1 for i in case_idx], 'up': up, 'down': down,
                         'total': up + down})
    reference = next(x for x in outcomes if x['case_samples'] == [4, 5, 6])
    other = [x['total'] for x in outcomes if x['case_samples'] not in ([1, 2, 3], [4, 5, 6])]
    return {
        'status': 'PUBLIC_INPUT_STRESS_TEST_ONLY',
        'rows': len(data), 'ratio_reference_genes': len(ratio_samples[0]),
        'sample_selection': [EXPECTED_HEADER[i] for i in SAMPLE_INDICES],
        'size_factors': factors,
        'observed': reference,
        'other_partition_maximum': max(other),
        'exact_label_permutation_p': sum(x['total'] >= reference['total'] for x in outcomes) / 20,
        'limitation': 'Paired donor design ignored by this six-sample stress test. Do not infer biology; no gene-wise FDR.'
    }


def self_test():
    data = [
        ('A', [100, 102, 98, 1000, 990, 1010]),
        ('B', [1000, 1020, 980, 100, 99, 101]),
        ('C', [100, 102, 98, 101, 100, 103]),
        ('D', [0, 0, 0, 0, 0, 0])
    ]
    x = analyze(data)
    assert len(x['size_factors']) == 6
    assert x['rows'] == 4
    assert x['observed']['up'] >= 1 and x['observed']['down'] >= 1
    assert x['exact_label_permutation_p'] >= 0.1
    print('PASS: synthetic positive/negative controls, normalization, 20 permutations')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.input:
        parser.error('--input is required unless --self-test')
    result = analyze(read_counts(args.input))
    result['source_sha256'] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()