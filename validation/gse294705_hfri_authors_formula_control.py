#!/usr/bin/env python3
"""Reproduce the PUBLIC HfRI R calculator's scoring algebra, not its full preprocessing.

This is a separate, additive audit. The 2026-11-11 approximate replay/report
stay unchanged for traceability. No treatment-response, clinical, or sales claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import urllib.request

import numpy as np
import gse294705_hfri_published_weights_replay as prior

OFFICIAL = Path("research/cretostimogene/hfri_author_fullprecision_weights_2026-11-12.json")
LEGACY = Path("research/cretostimogene/hfri_published_75_gene_weights_hgnc_2026-11-11.json")
SEED = 20261111


def validated_weights(manifest: dict) -> list[dict]:
    w = manifest["weights"]
    assert len(w) == 75 and len({r["gene"] for r in w}) == 75
    assert len({r["ensembl"] for r in w}) == 75
    assert sum(r["group"] == "Positive" for r in w) == 34
    assert sum(r["group"] == "Negative" for r in w) == 41
    assert all(r["group"] in {"Positive", "Negative"} and
               math.isfinite(r["weight"]) and r["weight"] >= 0 for r in w)
    return w


def verify_authors_file(manifest: dict) -> str:
    """Opt-in live check of authors' commit-pinned exact text and Git blob SHA-1."""
    url = manifest["source_url"].replace(
        "https://github.com/", "https://raw.githubusercontent.com/"
    ).replace("/blob/", "/")
    raw = urllib.request.urlopen(url, timeout=40).read()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\\0" + raw).hexdigest()
    assert blob == manifest["source_git_blob_sha"], "authors' public weight file changed"
    records = [line.split("\\t") for line in raw.decode().splitlines()]
    assert records[0] == ["GeneID", "Weights", "Group"]
    assert len(records) == 76
    for source, target in zip(records[1:], validated_weights(manifest)):
        assert source[0] == target["gene"]
        assert float(source[1]) == float(target["weight"])
        assert source[2] == target["group"]
    return blob


def score_models(normalized: np.ndarray, ids: list[str],
                 authors: list[dict], legacy: list[dict]) -> dict:
    index = {gene: pos for pos, gene in enumerate(ids)}
    assert len(index) == len(ids)
    assert all(row["ensembl"] in index for row in authors)
    official = np.stack([normalized[index[row["ensembl"]], :] for row in authors])
    # R's scale() uses sample standard deviation (n-1), not NumPy ddof=0.
    std = np.std(official, axis=1, ddof=1, keepdims=True)
    assert np.all(std > 0)
    z = (official - np.mean(official, axis=1, keepdims=True)) / std
    coeff = np.array([row["weight"] for row in authors])
    plus = np.array([row["group"] == "Positive" for row in authors])
    weighted = z * coeff[:, None]
    # Authors' published HfRI_Calculator.R:
    # positive_mean <- colMeans(weighted_expr[positive_idx, ])
    # negative_mean <- colMeans(weighted_expr[negative_idx, ])
    # HfRI <- positive_mean - negative_mean
    score = weighted[plus].mean(axis=0) - weighted[~plus].mean(axis=0)

    # Historical ASTRA approximation independently recomputed for regression.
    old = np.stack([normalized[index[row["ensembl"]], :] for row in legacy])
    old_std = old.std(axis=1, ddof=0, keepdims=True)
    assert np.all(old_std > 0)
    old_z = (old - old.mean(axis=1, keepdims=True)) / old_std
    historical = np.array([row["weight"] for row in legacy]) @ old_z
    return {"authors_scoring_algebra": score, "historical_astra_approx": historical}


def check_fixture() -> None:
    # The two unequal group sizes in the actual method are why a signed sum
    # is NOT algebraically equivalent to means of positive and negative groups.
    x = np.array([[1., 3., 5.], [3., 4., 8.], [9., 5., 2.]], dtype=float)
    authors = [
        {"gene": "A", "ensembl": "a", "weight": 2.34, "group": "Positive"},
        {"gene": "B", "ensembl": "b", "weight": 1.78, "group": "Positive"},
        {"gene": "C", "ensembl": "c", "weight": 3.15, "group": "Negative"},
    ]
    legacy = [{"ensembl": r["ensembl"], "weight": r["weight"] *
               (1 if r["group"] == "Positive" else -1)} for r in authors]
    result = score_models(x, ["a", "b", "c"], authors, legacy)
    z = (x - x.mean(axis=1, keepdims=True)) / x.std(axis=1, ddof=1, keepdims=True)
    expected = (2.34 * z[0] + 1.78 * z[1]) / 2 - 3.15 * z[2]
    assert np.allclose(result["authors_scoring_algebra"], expected, atol=1e-12)
    assert not np.allclose(result["authors_scoring_algebra"], (np.array([2.34, 1.78, -3.15]) @ z))
    assert np.isclose(z[0].std(ddof=1), 1)
    assert np.isfinite(result["historical_astra_approx"]).all()
    print(json.dumps({"status": "PASS", "tests": 4,
                      "scope": "R-formula algebra, ddof=1 and old-score control on synthetic fixture"}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify-upstream", action="store_true")
    args = parser.parse_args()
    check_fixture()
    if args.self_test:
        return

    manifest = json.loads(OFFICIAL.read_text())
    authors = validated_weights(manifest)
    previous = json.loads(LEGACY.read_text())["weights"]
    source_check = verify_authors_file(manifest) if args.verify_upstream else "not_live_retrieved"

    meta = prior.get_meta(prior.fetch(prior.META, prior.META_SHA))
    ids, matrix, n_genes, lib, exceptions = prior.load_counts(
        prior.fetch(prior.COUNTS, prior.COUNTS_SHA), meta,
        [row["ensembl"] for row in authors]
    )
    labels = np.array([label == "Yes" for label in meta["outcome"]])
    site = np.array([name.split("_")[0] for name in meta["names"]])
    strata = np.array([sex + "/" + stage + "/" + cohort
                       for sex, stage, cohort in zip(meta["sex"], meta["stage"], site)])

    output = {
        "status": "EXPLORATORY_AUTHORS_SCORING_FORMULA_NOT_FULL_PROTOCOL",
        "dataset": "GSE294705",
        "patients": int(len(labels)),
        "events_ge2_recurrence": int(labels.sum()),
        "count_sha256": prior.COUNTS_SHA,
        "metadata_sha256": prior.META_SHA,
        "authors_weights_git_blob_sha": manifest["source_git_blob_sha"],
        "authors_weights_upstream_check": source_check,
        "official_gene_count": len(authors),
        "positive_group": 34, "negative_group": 41,
        "normalized_gene_rows": n_genes,
        "source_filter_exceptions_retained": exceptions,
        "formula": "mean(positive exact authors weights * row-wise z-score(ddof=1)) minus mean(negative exact authors weights * row-wise z-score(ddof=1))",
        "limitations": ["Same GSE294705 94 patients as historical replay, not an independent clinical cohort.",
                        "Authors' input expression preprocessing and model threshold not reproduced exactly.",
                        "FOXI2 below global CPM threshold retained; interpretation remains methodologically PARTIAL.",
                        "No patient treatment outcome from cretostimogene or clinical validation."],
        "results": {}
    }
    for normalization in ["quantile", "logCPM"]:
        normalized = prior.quantile_normalize(matrix) if normalization == "quantile" else matrix
        scores = score_models(normalized, ids, authors, previous)
        key = "quantile_normalized" if normalization == "quantile" else "logCPM_no_quantile"
        output["results"][key] = {}
        for label, s in scores.items():
            prior.rng = np.random.default_rng(SEED)
            output["results"][key][label] = {
                "auc_descriptive": round(prior.auc(s, labels), 8),
                "mean_event_minus_other": round(float(s[labels].mean() - s[~labels].mean()), 8),
                "permutation_p_sex_stage_site": round(prior.perm_p(s, labels, strata, 10000), 8),
            }
    # Historical report should reproduce within rounding from same sources.
    archived = json.loads(Path(
        "reports/cretostimogene/gse294705_hfri_75_gene_published_model_replay_2026-11-11.json"
    ).read_text())
    for new_key, old_key in [("quantile_normalized", "quantile_normalized"),
                             ("logCPM_no_quantile", "logCPM_without_quantile_sensitivity")]:
        current = output["results"][new_key]["historical_astra_approx"]["auc_descriptive"]
        assert current == archived["results"][old_key]["auc_in_sample"], (
            "Old ASTRA AUC mismatch: stop rather than overwrite archived evidence"
        )
    print("ASTRA_HFRI_AUTHORS_FORMULA_REPORT_START")
    print(json.dumps(output, sort_keys=True))
    print("ASTRA_HFRI_AUTHORS_FORMULA_REPORT_END")


if __name__ == "__main__":
    main()
