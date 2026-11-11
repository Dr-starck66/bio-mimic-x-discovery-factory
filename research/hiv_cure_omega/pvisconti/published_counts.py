#!/usr/bin/env python3
"""Recompute only PUBLISHED pVISCONTI counts. Never claim individual XLSX analysis."""
from math import comb, sqrt
from statistics import NormalDist
import json
from pathlib import Path

def fisher_exact_2sided(a,b,c,d):
    n=a+b+c+d
    row=a+b
    col=a+c
    lo=max(0,row+col-n)
    hi=min(row,col)
    den=comb(n,row)
    def mass(k):
        return comb(col,k)*comb(n-col,row-k)/den
    observed=mass(a)
    return sum(mass(k) for k in range(lo,hi+1) if mass(k)<=observed+1e-12)

def wilson(x,n):
    z=NormalDist().inv_cdf(.975)
    p=x/n
    d=1+z*z/n
    center=(p+z*z/(2*n))/d
    delta=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return center-delta,center+delta

def compare(early_success,early_total,late_success,late_total):
    a=early_success
    b=early_total-a
    c=late_success
    d=late_total-c
    p1=a/early_total
    p2=c/late_total
    l1,u1=wilson(a,early_total)
    l2,u2=wilson(c,late_total)
    risk_difference=p1-p2
    return {
        "early_success": f"{a}/{early_total}",
        "late_success": f"{c}/{late_total}",
        "risk_early": p1,
        "risk_late": p2,
        "risk_difference": risk_difference,
        "risk_difference_newcombe_95_ci": [
            risk_difference-sqrt((p1-l1)**2+(u2-p2)**2),
            risk_difference+sqrt((u1-p1)**2+(p2-l2)**2)
        ],
        "odds_ratio": (a*d)/(b*c) if b*c else None,
        "fisher_exact_p_two_sided": fisher_exact_2sided(a,b,c,d),
        "limitation": "published counts only; no individual source XLSX; no causality or HIV cure claim",
    }

def calculate():
    return {
        "schema": "astra-pvisconti-counts-audit/1",
        "as_of": "2026-11-08",
        "scope": "PUBLISHED_AGGREGATE_COUNTS_ONLY",
        "underlying_siv_cohort_count": 1,
        "raw_source_xlsx_verified": False,
        "reference_cohort_charre": compare(9,11,2,11),
        "overlapping_subset_hua": compare(8,9,2,4),
        "do_not_meta_analyze": True,
        "clinical_hiv_cure_demonstrated": False,
        "primary_sources": [
            "https://www.nature.com/articles/s41467-026-69720-6",
            "https://www.nature.com/articles/s41467-026-69848-5"
        ]
    }

if __name__=="__main__":
    result=calculate()
    dest=Path(__file__).with_name("published_count_results.json")
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
