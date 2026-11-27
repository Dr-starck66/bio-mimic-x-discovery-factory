#!/usr/bin/env python3
"""ASTRA OBESITY Ω — Official NHANES 2021–2023, nonclinical pilot.

Measures association with elevated HbA1c, not a clinical obesity diagnosis.
Raw survey participant records are never exported or committed.
"""
from __future__ import annotations
import hashlib, io, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/"
SPEC = {
    "DEMO_L": ("SEQN", "RIDAGEYR", "RIAGENDR", "RIDEXPRG", "SDMVSTRA", "SDMVPSU"),
    "BMX_L": ("SEQN", "BMXBMI", "BMXWAIST", "BMXHT"),
    "GHB_L": ("SEQN", "LBXGH", "WTPH2YR"),
}
SEED = 20261114

def sha(data):
    return hashlib.sha256(data).hexdigest()

def get(stem):
    import time
    url = BASE + stem + ".xpt"
    error = None
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=(12, 70), headers={"User-Agent": "ASTRA-OBESITY-research-v0.2"})
            r.raise_for_status()
            if r.url.split("/")[2].lower() not in ("wwwn.cdc.gov", "www.cdc.gov"):
                raise ValueError("Unapproved redirect host")
            data = r.content
            if not data.startswith(b"HEADER RECORD*******LIBRARY HEADER RECORD!!!!!!!") or len(data) % 80:
                raise ValueError("Invalid or truncated SAS XPORT file")
            frame = pd.read_sas(io.BytesIO(data), format="xport", encoding="utf-8")
            missing = sorted(set(SPEC[stem]) - set(frame.columns))
            if missing or frame.SEQN.duplicated().any():
                raise ValueError("NHANES schema mismatch: " + str(missing))
            meta = {"url": url, "sha256": sha(data), "bytes": len(data),
                    "records": len(frame), "acquisition": "DIRECT_OFFICIAL_CDC_HTTPS"}
            print("SOURCE_VERIFIED=" + json.dumps({"file": stem, **meta}, sort_keys=True), flush=True)
            return frame[list(SPEC[stem])].copy(), meta
        except Exception as exc:
            error = repr(exc)
            if attempt < 2:
                time.sleep(attempt + 1)
    raise RuntimeError("SOURCE_UNAVAILABLE " + stem + " " + str(error))

def prepare(data):
    demo, bmx, ghb = data
    df = demo.merge(bmx, on="SEQN", how="inner", validate="one_to_one")
    df = df.merge(ghb, on="SEQN", how="inner", validate="one_to_one")
    joined = len(df)
    df = df.loc[(df.RIDAGEYR >= 20) & (df.RIDEXPRG != 1)].copy()
    adults = len(df)
    cols = ["BMXBMI", "BMXWAIST", "BMXHT", "LBXGH", "WTPH2YR", "RIAGENDR", "RIDAGEYR",
            "SDMVSTRA", "SDMVPSU"]
    for key in cols:
        df[key] = pd.to_numeric(df[key], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=cols)
    df = df.loc[(df.BMXBMI > 0) & (df.BMXWAIST > 0) & (df.BMXHT > 0) &
                (df.LBXGH > 0) & (df.WTPH2YR > 0) & (df.RIAGENDR.isin([1, 2]))].copy()
    df["WHtR"] = df.BMXWAIST / df.BMXHT
    df["sex_female"] = (df.RIAGENDR == 2).astype(int)
    df["y"] = (df.LBXGH >= 6.5).astype(int)
    # Masked PSU grouping is a split guard, not independent geographic validation.
    df["cluster"] = df.SDMVSTRA.astype(int).astype(str) + "_" + df.SDMVPSU.astype(int).astype(str)
    n = len(df)
    positives = int(df.y.sum())
    if n < 300 or min(positives, n - positives) < 30 or df.cluster.nunique() < 5:
        raise ValueError("Insufficient complete cases, events or PSU clusters")
    return df.reset_index(drop=True), {"joined": joined, "adults_excluding_pregnant": adults,
        "complete_cases": n, "excluded_for_missingness": adults - n,
        "elevated_hba1c_6_5_n": positives, "masked_psus": int(df.cluster.nunique()),
        "unweighted_elevated_hba1c_fraction": round(float(df.y.mean()), 6)}

def auc(y, pred, w):
    return float(roc_auc_score(y, pred, sample_weight=w))

def evaluate(df):
    n = len(df)
    y = df.y.to_numpy()
    w = df.WTPH2YR.to_numpy()
    groups = df.cluster.to_numpy()
    specs = {"BMI_ONLY": ["BMXBMI"], "BMI_PLUS_WHTR": ["BMXBMI", "WHtR"],
             "BMI_AGE_SEX": ["BMXBMI", "RIDAGEYR", "sex_female"],
             "BMI_WHTR_AGE_SEX": ["BMXBMI", "WHtR", "RIDAGEYR", "sex_female"]}
    predictions = {key: np.full(n, np.nan) for key in [*specs, "NEGATIVE_SHUFFLED_WHTR"]}
    folds = []
    for j, (train, test) in enumerate(GroupKFold(n_splits=5).split(np.zeros(n), y, groups)):
        if set(groups[train]) & set(groups[test]):
            raise AssertionError("PSU data leakage")
        if len(set(y[test])) < 2 or len(set(y[train])) < 2:
            raise ValueError("One-class group holdout")
        weight = w[train] * len(train) / w[train].sum()
        for name, features in specs.items():
            model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
            model.fit(df.iloc[train][features], y[train], logisticregression__sample_weight=weight)
            predictions[name][test] = model.predict_proba(df.iloc[test][features])[:, 1]
        rng = np.random.default_rng(SEED + j)
        tr = df.iloc[train][["BMXBMI", "WHtR"]].copy()
        te = df.iloc[test][["BMXBMI", "WHtR"]].copy()
        tr["WHtR"] = rng.permutation(tr.WHtR.to_numpy())
        te["WHtR"] = rng.permutation(te.WHtR.to_numpy())
        negative = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
        negative.fit(tr, y[train], logisticregression__sample_weight=weight)
        predictions["NEGATIVE_SHUFFLED_WHTR"][test] = negative.predict_proba(te)[:, 1]
        folds.append({"fold": j + 1, "heldout_n": len(test), "heldout_positives": int(y[test].sum()),
                      "heldout_psu_n": len(set(groups[test]))})
    if any(not np.isfinite(a).all() for a in predictions.values()):
        raise AssertionError("Incomplete out-of-fold predictions")
    metrics = {k: {"weighted_roc_auc": round(auc(y, a, w), 6),
                   "weighted_brier": round(float(brier_score_loss(y, a, sample_weight=w)), 6)}
               for k, a in predictions.items()}
    delta = auc(y, predictions["BMI_PLUS_WHTR"], w) - auc(y, predictions["BMI_ONLY"], w)
    delta_adjusted = (auc(y, predictions["BMI_WHTR_AGE_SEX"], w)
                      - auc(y, predictions["BMI_AGE_SEX"], w))
    # Resample masked PSUs. This is descriptive; NOT a survey-design CI.
    rng = np.random.default_rng(SEED)
    clusters = np.unique(groups)
    ix = [np.flatnonzero(groups == cl) for cl in clusters]
    draws = []
    for _ in range(200):
        sampled = rng.integers(0, len(ix), len(ix))
        rows = np.concatenate([ix[i] for i in sampled])
        if len(np.unique(y[rows])) != 2:
            continue
        draws.append(auc(y[rows], predictions["BMI_PLUS_WHTR"][rows], w[rows])
                     - auc(y[rows], predictions["BMI_ONLY"][rows], w[rows]))
    if len(draws) < 50:
        raise ValueError("Insufficient resamples")
    return {"folds": folds, "weighted_metrics": metrics,
            "delta_auc_primary": round(delta, 6),
            "delta_auc_adjusted_age_sex": round(delta_adjusted, 6),
            "delta_auc_descriptive_cluster_resample_95": [round(float(np.quantile(draws, .025)), 6),
                                                        round(float(np.quantile(draws, .975)), 6)],
            "bootstrap_accepted": len(draws), "geographically_independent": False,
            "intervention_effect_evaluated": False}

def main():
    sources, frames = {}, []
    for stem in SPEC:
        frame, meta = get(stem)
        sources[stem] = meta
        frames.append(frame)
    sample, sizes = prepare(frames)
    scores = evaluate(sample)
    result = {"schema": "astra-nhanes-2021-2023-v0.2", "status": "PARTIAL_OBSERVATIONAL",
              "inputs": sources, "sample": sizes, "analysis": scores,
              "endpoint": "HbA1c >=6.5% lab marker, NOT diagnosis of clinical obesity",
              "sampling_weight": "WTPH2YR", "grouped_holdout": "SDMVSTRA+SDMVPSU",
              "limitations": ["cross-sectional", "no treatment effect or treatment durability",
                "not a clinical obesity diagnostic algorithm", "not geographic external validation",
                "group bootstrap is not survey-correct interval",
                "HbA1c affected by therapy, anemia, and other clinical factors"],
              "worldwide_cure_proven": False, "additional_cost_eur": 0}
    result["sha256"] = sha(json.dumps(result, ensure_ascii=False,
                        sort_keys=True, separators=(",", ":")).encode())
    out = Path("artifacts/astra_obesity_nhanes_2021_2023.json")
    out.parent.mkdir(exist_ok=True, parents=True)
    out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print("REAL_NHANES_RESULTS=" + json.dumps({"sample": sizes, "analysis": scores,
          "input_sha256": {k: v["sha256"] for k, v in sources.items()},
          "report_sha256": result["sha256"]}, sort_keys=True), flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("REAL_NHANES_RUN_FAIL=" + repr(error), file=sys.stderr, flush=True)
        raise SystemExit(2)
