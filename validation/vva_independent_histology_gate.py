#!/usr/bin/env python3
"""BIO-MIMIC X: external biopsy evidence and false durability claim gate.

No patient-level reconstruction. No therapeutic efficacy inference from aggregate reports.
"""
from __future__ import annotations
import argparse
import json
from math import comb
from pathlib import Path


def fisher_two_sided(success_t, total_t, success_c, total_c):
    """Exact conditional Fisher test, including all tables no more likely than observed."""
    for x in (success_t, total_t, success_c, total_c):
        if type(x) is not int or x < 0:
            raise ValueError('nonnegative integer counts required')
    if not (0 <= success_t <= total_t and 0 <= success_c <= total_c and total_t and total_c):
        raise ValueError('invalid binomial group counts')
    n = total_t + total_c
    successes = success_t + success_c
    lo, hi = max(0, successes-total_c), min(total_t, successes)
    denom = comb(n, total_t)
    def probability(k):
        return comb(successes, k) * comb(n-successes, total_t-k) / denom
    target = probability(success_t)
    return min(1.0, sum(probability(k) for k in range(lo, hi+1)
                        if probability(k) <= target * (1+1e-12)))


def audit(record):
    if record.get('schema') != 'ASTRA-VVA-STRUCTURAL-INDEPENDENT/1':
        raise ValueError('unknown dataset schema')
    data = record['histology_sham_rct']
    if data['source_kind'] != 'published_aggregate_from_randomized_sham_trial':
        raise ValueError('invalid source provenance')
    if data['histology_time_months_after_first_treatment'] != 6:
        raise ValueError('histology time point not supported by cited paper')
    if data['last_treatment_date_known'] is not False:
        raise ValueError('last treatment date must not be fabricated')
    treated = data['treated']
    sham = data['sham']
    x1,n1 = treated['improved'], treated['paired_biopsies']
    x0,n0 = sham['improved'], sham['paired_biopsies']
    p = fisher_two_sided(x1,n1,x0,n0)
    diff = x1/n1 - x0/n0
    geo = record['transcriptomics_GSE11622']
    if geo['human_paired_subjects_reported'] != 19 or geo['after_estradiol_months'] != 3:
        raise ValueError('GSE11622 metadata mismatch')
    if geo['documented_off_treatment_followup'] is not False:
        raise ValueError('do not invent post-cessation follow-up for GEO')
    # This eligibility test needs all conditions simultaneously. Missing is a negative gate,
    # not evidence of absence of a biological effect.
    gates = {
        'paired_human_histology': n1 > 0 and n0 > 0 and data['histology_paired_before_after'],
        'sham_separated': data['randomized_sham_controlled'],
        'histology_effect_statistically_detected': p < 0.05,
        'off_treatment_at_least_3_months_verified': False,  # last treatment date/interval unavailable
        'quantitative_collagen_elastin_architecture': data['quantitative_ECM_available'],
        'functional_barrier_TEER': data['barrier_TEER_available'],
        'paired_source_raw_data_downloaded': data['individual_patient_data_accessible'],
        'molecular_GSE11622_off_treatment_followup': geo['documented_off_treatment_followup'],
    }
    return {
        'schema': 'ASTRA-VVA-STRUCTURAL-INDEPENDENT-AUDIT/1',
        'origin': 'published human randomized sham histology + public GEO metadata',
        'histology': {'paired_biopsies': n1+n0, 'active': {'improved':x1,'n':n1},
                      'sham': {'improved':x0,'n':n0},
                      'risk_difference_percentage_points':round(100*diff, 4),
                      'fisher_exact_two_sided_p':round(p, 12),
                      'histology_6_months_after_first_treatment':True,
                      'verified_months_after_last_treatment':None,
                      'same_as_12_month_symptom_outcome':False},
        'GSE11622': {'paired_biopsies_reported':19, 'intervention_months':3,
                     'post_cessation_data':False, 'raw_data_reanalysis':'NOT_EXECUTED'},
        'gates':gates,
        'durable_structural_regeneration_proven':all(gates.values()),
        'status':'PARTIAL_OBSERVATIONAL_RECALCULATION_NOT_CLINICAL_VALIDATION',
        'caveats':['No p-value indicates equivalence; a small study may miss effects.',
                   'Histology categorical; quantitative ECM and TEER unavailable.',
                   'Biopsy timing differs from 12-month symptom follow-up.',
                   'Gene expression is not proof of ECM architecture or durability.',
                   'Do not infer post-treatment withdrawal interval from first-treatment date.',
                   'Published aggregate reanalysis only; no patient-level paired data.']
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input_json')
    parser.add_argument('--out')
    args=parser.parse_args()
    result=audit(json.loads(Path(args.input_json).read_text()))
    txt=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if args.out:
        Path(args.out).write_text(txt)
    print(txt,end='')

if __name__=='__main__':main()
