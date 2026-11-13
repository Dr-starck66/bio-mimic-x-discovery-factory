"""BIO-MIMIC X: pre-specified mouse OMC1 PSSC reanalysis, no third-party dependencies.

Reads real, explicitly documented per-oocyte observations only. No imputation or
fabricated observations. Animal is the independent experimental unit.
"""
import argparse
import csv
import hashlib
import itertools
import json
import random
from collections import defaultdict
from pathlib import Path

REQUIRED = {'oocyte_id', 'animal_id', 'experiment_id', 'age_weeks', 'genotype', 'pssc'}


def _mean(values):
    return sum(values) / len(values)


def _difference(animal_rates, group_labels):
    ko = [r for r, label in zip(animal_rates, group_labels) if label == 'KO']
    wt = [r for r, label in zip(animal_rates, group_labels) if label == 'WT']
    return _mean(ko) - _mean(wt)


def analyze(path, bootstrap_iterations=2000):
    path = Path(path)
    raw = path.read_bytes()
    with path.open(newline='', encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError('Missing required columns: ' + ', '.join(sorted(REQUIRED - set(reader.fieldnames or []))))
        entries = list(reader)
    if not entries:
        raise ValueError('Empty input')
    clusters = defaultdict(list)
    seen = set()
    batch_groups = defaultdict(set)
    for line, row in enumerate(entries, 2):
        if any(not row.get(k, '').strip() for k in REQUIRED):
            raise ValueError(f'Incomplete observation at CSV line {line}')
        if row['genotype'] not in ('KO', 'WT'):
            raise ValueError(f'Invalid genotype at line {line}')
        if row['pssc'] not in ('0', '1'):
            raise ValueError(f'Invalid PSSC binary value at line {line}')
        try:
            age = float(row['age_weeks'])
        except ValueError as exc:
            raise ValueError(f'Invalid age at line {line}') from exc
        if age != 8:
            continue
        key = (row['experiment_id'], row['animal_id'], row['oocyte_id'])
        if key in seen:
            raise ValueError(f'Duplicate oocyte at line {line}')
        seen.add(key)
        # Same animal identifier must never appear under both genotypes in a batch.
        clusters[(row['experiment_id'], row['animal_id'], row['genotype'])].append(int(row['pssc']))
        batch_groups[row['experiment_id']].add(row['genotype'])
    if not clusters:
        raise ValueError('No age-8-week observations')
    # Prevent analysis of a severely confounded experiment where genotype and batch coincide.
    if any(g != {'KO', 'WT'} for g in batch_groups.values()):
        raise ValueError('At least one experiment lacks a WT or KO comparator')
    animal_genotypes = defaultdict(set)
    for batch, animal, genotype in clusters:
        animal_genotypes[(batch, animal)].add(genotype)
    if any(len(s) > 1 for s in animal_genotypes.values()):
        raise ValueError('Animal has inconsistent genotype')
    cluster_items = sorted(clusters)
    rates = [_mean(clusters[k]) for k in cluster_items]
    labels = [k[2] for k in cluster_items]
    ko_n = labels.count('KO')
    wt_n = labels.count('WT')
    if ko_n < 2 or wt_n < 2:
        raise ValueError('At least two independent animals per genotype are required')
    observed = _difference(rates, labels)
    # Exact cluster-level permutation, respecting the original WT/KO count PER experiment.
    batch_positions = defaultdict(list)
    for idx, (batch, animal, genotype) in enumerate(cluster_items):
        batch_positions[batch].append(idx)
    assignments = []
    for positions in batch_positions.values():
        n_ko = sum(labels[i] == 'KO' for i in positions)
        assignments.append(list(itertools.combinations(positions, n_ko)))
    num_permutations = 1
    for opts in assignments:
        num_permutations *= len(opts)
    if num_permutations > 100000:
        raise ValueError('Exact permutation space too large; method requires revision before analysis')
    extreme = 0
    for batch_options in itertools.product(*assignments):
        selected = set().union(*batch_options)
        perm_labels = ['KO' if i in selected else 'WT' for i in range(len(labels))]
        if abs(_difference(rates, perm_labels)) >= abs(observed) - 1e-12:
            extreme += 1
    p_value = extreme / num_permutations
    # Cluster bootstrap confidence intervals, stratified by genotype. Descriptive only.
    rng = random.Random(20261113)
    ko_rates = [r for r, l in zip(rates, labels) if l == 'KO']
    wt_rates = [r for r, l in zip(rates, labels) if l == 'WT']
    boot = sorted(_mean([rng.choice(ko_rates) for _ in ko_rates]) -
                  _mean([rng.choice(wt_rates) for _ in wt_rates])
                  for _ in range(bootstrap_iterations))
    return {
        'status': 'EXPLORATORY_REANALYSIS_NOT_EXPERIMENTAL_REPLICATION',
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'input_file': path.name,
        'endpoint': 'PSSC per oocyte at age 8 weeks',
        'independent_unit': 'animal within experiment',
        'experiment_count': len(batch_positions),
        'n_animals': {'KO': ko_n, 'WT': wt_n},
        'n_oocytes': {g: sum(len(clusters[k]) for k in cluster_items if k[2] == g) for g in ('KO', 'WT')},
        'animal_mean_PSSC_rate': {'KO': _mean(ko_rates), 'WT': _mean(wt_rates)},
        'difference_KO_minus_WT': observed,
        'exact_stratified_permutation_p_two_sided': p_value,
        'number_of_permutations': num_permutations,
        'animal_cluster_bootstrap_95pct_CI': [boot[int(.025 * len(boot))], boot[min(len(boot)-1, int(.975 * len(boot)))]],
        'cautions': ['This is a secondary reanalysis of supplied observations.',
                     'Animal IDs and experimental batches must be confirmed against source metadata.',
                     'A statistical result cannot establish efficacy in humans.'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', help='observed per-oocyte CSV, never synthetic for a real scientific claim')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    report = analyze(args.csv_file)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"PASS: {args.output} (analysis of supplied observations only)")


if __name__ == '__main__':
    main()
