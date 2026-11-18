#!/usr/bin/env python3
"""BIO-MIMIC X: reproducible UM-HET3 descriptive site/sex decomposition.

No survival/hazard modelling or causal mediation is attempted. All results
condition on genetically characterized mice surviving the 42-day entry age.
For BW6 analyses, only mice with BW measured at ~183 days are eligible, and
selection on surviving until measurement is a major uncorrected bias.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from collections import defaultdict, Counter
from pathlib import Path

SITE = {'1.0': 'JL', '2.0': 'UM', '3.0': 'UT'}
SEX = {'0': 'F', '1': 'M'}  # from original authors' Figure1.R; prose n_sex discordant
COMMON = (2004, 2005, 2006, 2007, 2009)
BW_YEARS = (2005, 2006, 2009)
FIELDS = ('mouse_id', 'sex_code', 'site_code', 'cohort_year',
          'treatment_code', 'longevity_days', 'bw6', 'bw12', 'bw18', 'bw24')


def load(path):
    with open(path, encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError('Unexpected columns, use pinned UMHET3_6438_PHENOTYPES.csv')
        return check_and_convert(list(reader))


def check_and_convert(rows):
    seen = set()
    out = []
    for x in rows:
        mouse_id = x['mouse_id']
        site = x['site_code']
        if site not in SITE or not mouse_id.startswith(SITE[site]):
            raise ValueError('Site code / ID prefix mismatch')
        if mouse_id in seen:
            raise ValueError('Duplicate mouse')
        seen.add(mouse_id)
        if x['sex_code'] not in SEX or x['treatment_code'] not in ('0.0', '1.0'):
            raise ValueError('Unrecognized sex or treatment code')
        days = float(x['longevity_days'])
        if not math.isfinite(days) or days < 42:
            raise ValueError('Out-of-range longevity')
        bw = None if x['bw6'] == '' else float(x['bw6'])
        if bw is not None and not math.isfinite(bw):
            raise ValueError('Invalid body mass')
        out.append({'id': mouse_id, 'sex': x['sex_code'], 'site': site,
                    'year': int(float(x['cohort_year'])), 'tx': x['treatment_code'],
                    'days': days, 'bw': bw})
    return out


def avg(values):
    return sum(values) / len(values)


def gap(rows, years=COMMON, treatment=None, trunc=None):
    """Standardize site-specific sex mean to same year×treatment distribution.

    This adjusts composition of observed age and binary treatment category,
    not genotypes, cage, diet or specific compounds. `trunc` is min(T, age),
    only a truncated recorded age, NOT a Kaplan-Meier estimator.
    """
    subset = [r for r in rows if r['year'] in years
              and (treatment is None or r['tx'] == treatment)]
    if not subset:
        raise ValueError('No observations')
    weights = Counter((r['year'], r['tx']) for r in subset)
    cells = defaultdict(list)
    for r in subset:
        cells[(r['site'], r['year'], r['tx'], r['sex'])].append(
            min(r['days'], trunc) if trunc is not None else r['days'])
    total = len(subset)
    result = {}
    for site in SITE:
        cell = {'n': sum(r['site'] == site for r in subset)}
        for sex, label in (('0', 'female'), ('1', 'male')):
            val = 0.0
            for (year, tx), n in weights.items():
                group = cells.get((site, year, tx, sex), [])
                if not group:
                    raise ValueError('No common-support cell')
                val += n / total * avg(group)
            cell[label] = val
        cell['female_minus_male'] = cell['female'] - cell['male']
        result[SITE[site]] = cell
    return result


def eligible_weight(rows, sex='1', treatment=None):
    return [r for r in rows if r['sex'] == sex and r['year'] in BW_YEARS
            and (treatment is None or r['tx'] == treatment)
            and r['bw'] is not None and 12 < r['bw'] < 85 and r['days'] >= 183]


def coarsened_weight_match(rows, width=6, shift=0, min_per_site=3,
                           sex='1', treatment=None):
    """Compare SAME common-support subset before and after 6mo weight binning.

    Each year×treatment×BW6-bin must contain >=min_per_site per centre.
    The raw (before BW) mean is still standardized for year×treatment,
    and the after-BW mean for year×treatment×BW6-bin. Controls-only can
    yield sign reversals. Results are deliberately conditional, noncausal.
    """
    if width <= 0 or min_per_site < 1:
        raise ValueError('Invalid bin configuration')
    eligible = eligible_weight(rows, sex, treatment)
    groups = defaultdict(lambda: defaultdict(list))
    for r in eligible:
        b = math.floor((r['bw'] - shift) / width)
        groups[(r['year'], r['tx'], b)][r['site']].append(r)
    keep = {k: v for k, v in groups.items()
            if all(len(v[s]) >= min_per_site for s in SITE)}
    if not keep:
        raise ValueError('No common body-weight support')
    weights_year = Counter()
    weights_bin = {}
    for k, grp in keep.items():
        n = sum(len(grp[s]) for s in SITE)
        weights_year[k[:2]] += n
        weights_bin[k] = n
    total = sum(weights_bin.values())
    before, after, counts = {}, {}, {}
    for site in SITE:
        raw = 0.0
        for y_tx, w in weights_year.items():
            members = [r['days'] for (y, tx, _), grp in keep.items()
                       if (y, tx) == y_tx for r in grp[site]]
            raw += w / total * avg(members)
        corrected = sum(weights_bin[k] / total * avg([r['days'] for r in g[site]])
                        for k, g in keep.items())
        before[SITE[site]] = raw
        after[SITE[site]] = corrected
        counts[SITE[site]] = sum(len(g[site]) for g in keep.values())
    raw_effect = before['UM'] - before['JL']
    after_effect = after['UM'] - after['JL']
    return {'n': total, 'eligible_n_before_overlap_filter': len(eligible),
            'n_common_bins': len(keep), 'n_site': counts, 'means_before_bw': before,
            'means_after_bw': after, 'UM_minus_JL_before': raw_effect,
            'UM_minus_JL_after': after_effect, 'UM_minus_UT_before': before['UM']-before['UT'],
            'UM_minus_UT_after': after['UM']-after['UT'],
            'attenuation_fraction': 1-after_effect/raw_effect if abs(raw_effect)>1e-12 else None}


def produce(rows):
    if len(rows) != 6438:
        raise ValueError('Expected source cohort of 6,438 individuals')
    base = gap(rows)
    control = gap(rows, treatment='0.0')
    early = gap(rows, years=(2004, 2005, 2006))
    late = gap(rows, years=(2007, 2009))
    each_year = {str(y): gap(rows, years=(y,)) for y in COMMON}
    weights = []
    for sex in ('1', '0'):
        for width in (5, 6, 8, 10):
            for shift in (0, width / 2):
                for treatment in (None, '0.0'):
                    try:
                        z = coarsened_weight_match(rows, width, shift, 3, sex, treatment)
                        weights.append({'sex': SEX[sex], 'width_g': width, 'shift_g': shift,
                                        'treatment': 'all' if treatment is None else 'controls', **z})
                    except ValueError:
                        weights.append({'sex': SEX[sex], 'width_g': width, 'shift_g': shift,
                                        'treatment': 'all' if treatment is None else 'controls',
                                        'status': 'NO_COMMON_SUPPORT'})
    return {'n': len(rows), 'n_overlap_years': sum(r['year'] in COMMON for r in rows),
            'common_years': COMMON, 'all': base, 'controls_only': control,
            'earlier': early, 'held_out_years': late, 'per_year': each_year,
            'male_weight_overlap_sensitivity': weights,
            'negative_evidence': ['Age- and site-dependent sex differences previously known (Cheng 2019)',
                                  'No event/censor status in derived file',
                                  'Weight at 6m measurement selects survivors and may induce collider bias',
                                  'BW bins and common support sample change estimates',
                                  'No causal claims or new therapy.']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('csv', type=Path)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    result = produce(load(a.csv))
    rendered = json.dumps(result, indent=2, ensure_ascii=False)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(rendered, encoding='utf-8')
    else:
        print(rendered)

if __name__ == '__main__':
    main()