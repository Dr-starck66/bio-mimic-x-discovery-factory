#!/usr/bin/env python3
"""Reproducible exploratory UM-HET3 site/sex/6-month-body-mass audit.

Input: the provenance-pinned derived 6,438-mouse CSV in BIO-MIMIC X GitHub.
Uses numpy (free). Not a clinical test, a causal mediation analysis, or an
individual-level event-time / censoring analysis. Negative controls included.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

SITE = {"1.0": "JL", "2.0": "UM", "3.0": "UT"}
SEX = {"0": "Female", "1": "Male"}
COMMON = ("2004.0", "2005.0", "2006.0", "2007.0", "2009.0")
BW_COMMON = ("2005.0", "2006.0", "2009.0")
FIELDS = ("mouse_id", "sex_code", "site_code", "cohort_year", "treatment_code", "longevity_days", "bw6", "bw12", "bw18", "bw24")


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        r = csv.DictReader(handle)
        if tuple(r.fieldnames or ()) != FIELDS:
            raise ValueError("Unexpected columns or ordering")
        return list(r)


def validate(rows: list[dict], expected_n: int | None = None) -> dict:
    if expected_n is not None and len(rows) != expected_n:
        raise ValueError(f"Expected {expected_n} mice; got {len(rows)}")
    seen = set()
    for row in rows:
        mid, site = row["mouse_id"], row["site_code"]
        if mid in seen:
            raise ValueError("Duplicate mouse ID")
        seen.add(mid)
        if site not in SITE or not mid.startswith(SITE[site]):
            raise ValueError("Site label not corroborated by mouse ID")
        if row["sex_code"] not in SEX or row["treatment_code"] not in ("0.0", "1.0"):
            raise ValueError("Unrecognized sex/treatment code")
        if not np.isfinite(float(row["longevity_days"])) or float(row["longevity_days"]) < 42:
            raise ValueError("Out-of-range lifespan")
    return {"n": len(rows), "unique_ids": len(seen), "by_site": dict(Counter(r["site_code"] for r in rows)), "by_sex_code": dict(Counter(r["sex_code"] for r in rows))}


def _groups(rows, years=COMMON):
    groups = defaultdict(lambda: {"0": [], "1": []})
    for r in rows:
        if r["cohort_year"] in years:
            groups[(r["site_code"], r["cohort_year"], r["treatment_code"])][r["sex_code"]].append(float(r["longevity_days"]))
    return groups


def standardized_gaps(rows, years=COMMON, treatment=None):
    """Common-cohort, shared cohort-by-treatment weights, not a causal estimate."""
    rows = [r for r in rows if r["cohort_year"] in years and (treatment is None or r["treatment_code"] == treatment)]
    sites = sorted({r["site_code"] for r in rows})
    yr_tx = sorted({(r["cohort_year"], r["treatment_code"]) for r in rows})
    groups = _groups(rows, years=years)
    weights = Counter((r["cohort_year"], r["treatment_code"]) for r in rows)
    count = sum(weights.values())
    out = {}
    for site in sites:
        female = male = 0.0
        for yr, tx in yr_tx:
            sub = groups[(site, yr, tx)]
            if not sub["0"] or not sub["1"]:
                raise ValueError("No shared support (sex/site/cohort/treatment)")
            w = weights[(yr, tx)] / count
            female += w * float(np.mean(sub["0"]))
            male += w * float(np.mean(sub["1"]))
        out[SITE[site]] = {"female": female, "male": male, "female_minus_male_days": female - male}
    return out


def _design(rows, add_bw):
    matrix = []
    for r in rows:
        matrix.append([1., float(r["site_code"] == "2.0"), float(r["site_code"] == "3.0"),
                       float(r["cohort_year"] == "2006.0"), float(r["cohort_year"] == "2009.0"),
                       float(r["treatment_code"] == "1.0")] + ([float(r["bw6"])] if add_bw else []))
    return np.asarray(matrix, dtype=float)


def fit(rows, add_bw):
    if not rows:
        raise ValueError("Empty model sample")
    X = _design(rows, add_bw)
    Y = np.asarray([float(r["longevity_days"]) for r in rows], dtype=float)
    beta, _, rank, _ = np.linalg.lstsq(X, Y, rcond=None)
    if rank != X.shape[1]:
        raise ValueError("Rank deficient design")
    return {"intercept": float(beta[0]), "UM_minus_JL": float(beta[1]), "UT_minus_JL": float(beta[2]),
            "cohort_2006": float(beta[3]), "cohort_2009": float(beta[4]),
            "nominally_ineffective_drug_indicator": float(beta[5]),
            **({"bw6_days_per_gram": float(beta[6])} if add_bw else {})}


def complete_bw(rows, sex="1"):
    return [r for r in rows if r["sex_code"] == sex and r["cohort_year"] in BW_COMMON
            and r["bw6"] != "" and 12 < float(r["bw6"]) < 85
            and float(r["longevity_days"]) >= 183]


def bootstrap_male_models(rows, n_boot=200, seed=20261118):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["site_code"], r["cohort_year"], r["treatment_code"])].append(r)
    rg = np.random.default_rng(seed)
    deltas = {"before": [], "after": [], "slope": [], "attenuation": []}
    for _ in range(n_boot):
        sample = []
        for group in groups.values():
            sample.extend(group[int(i)] for i in rg.integers(len(group), size=len(group)))
        a, b = fit(sample, False), fit(sample, True)
        deltas["before"].append(a["UM_minus_JL"])
        deltas["after"].append(b["UM_minus_JL"])
        deltas["slope"].append(b["bw6_days_per_gram"])
        deltas["attenuation"].append(1 - b["UM_minus_JL"] / a["UM_minus_JL"])
    return {k: np.quantile(v, [0.025, 0.975]).tolist() for k, v in deltas.items()}


def permute_bw_within_strata(rows, n_perm=150, seed=20261118):
    """Negative control for an individual weight-outcome association.
    Preserves site/year/treatment distributions but breaks within-cell pairing.
    DOES NOT test causal mediation or remove unobserved confounding.
    """
    groups = defaultdict(list)
    for r in rows:
        groups[(r["site_code"], r["cohort_year"], r["treatment_code"])].append(r)
    rg = np.random.default_rng(seed)
    slopes = []
    for _ in range(n_perm):
        sample = []
        for group in groups.values():
            bw = np.array([float(r["bw6"]) for r in group]); rg.shuffle(bw)
            sample.extend([{**r, "bw6": str(float(w))} for r, w in zip(group, bw)])
        slopes.append(fit(sample, True)["bw6_days_per_gram"])
    observed = fit(rows, True)["bw6_days_per_gram"]
    return {"observed": observed, "n_perm": n_perm,
            "null_95": np.quantile(slopes, [0.025, 0.975]).tolist(),
            "one_sided_p": (1 + sum(v <= observed for v in slopes)) / (n_perm + 1)}


def run(rows, bootstrap=200, permutations=150):
    validation = validate(rows, expected_n=6438)
    gaps = standardized_gaps(rows)
    controls = standardized_gaps(rows, treatment="0.0")
    males, females = complete_bw(rows, "1"), complete_bw(rows, "0")
    before, after = fit(males, False), fit(males, True)
    early = {}
    for site, code in (("JL", "1.0"), ("UM", "2.0"), ("UT", "3.0")):
        male_controls = [r for r in rows if r["site_code"] == code and r["sex_code"] == "1" and
                         r["treatment_code"] == "0.0" and r["cohort_year"] in COMMON]
        early[site] = {"n": len(male_controls), "deaths_before_365": sum(float(r["longevity_days"]) < 365 for r in male_controls)}
    return {"audit": validation, "shared_years": list(COMMON), "standardized_sex_gap_days": gaps,
            "untreated_controls_sex_gap_days": controls,
            "early_death_before_365_male_controls": early,
            "male_bw6_model": {"n": len(males), "before": before, "after": after,
                               "UM_vs_JL_attenuation_fraction": 1 - after["UM_minus_JL"]/before["UM_minus_JL"],
                               "bootstrap_95": bootstrap_male_models(males, bootstrap),
                               "shuffled_weight_negative_control": permute_bw_within_strata(males, permutations)},
            "female_bw6_model": {"n": len(females), "before": fit(females, False), "after": fit(females, True)},
            "scientific_status": "EXPLORATORY; no censoring metadata or causal mechanism established",
            "limitations": ["Site code independently corroborated by JL/UM/UT mouse ID prefixes.",
                            "2019 article already reported age- and site-specific sex gap.",
                            "6-month weight availability is nonrandom by cohort/site and conditions on surviving to measurement.",
                            "NDE drug code pools different interventions; no per-drug effect inferred.",
                            "No explicit censoring flag. Never use time-to-event Cox/KM assumptions without one.",
                            "Resampling assumes conditional independence within cells; cage/litter dependence is not modeled.",
                            "The 2026 paper's sex-count sentence conflicts with the phenotype sex coding/author's Figure1.R; query authors."]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--bootstrap", type=int, default=600)
    ap.add_argument("--permutations", type=int, default=400)
    ap.add_argument("--out", type=Path)
    args=ap.parse_args()
    result=run(read_csv(args.csv),args.bootstrap,args.permutations)
    doc=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(doc,encoding="utf-8")
    else: print(doc)

if __name__ == "__main__": main()