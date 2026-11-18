#!/usr/bin/env python3
"""Offline reproducible quantum-inspired vs classical biomedical *proxy* benchmark.

NOT a quantum-hardware result, biological-age estimator, longevity test, clinical
validation, or reproduction of L. Simons' supersolid polaron physics.
Requires installed numpy/scikit-learn.  No network or payments.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import sklearn
from sklearn.datasets import load_breast_cancer
from sklearn.dummy import DummyClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

DATASET_NAME = "sklearn_breast_cancer_wisconsin_diagnostic"
MODELS = ("dummy_majority", "logistic", "classical_rbf_svm", "simulated_product_state_fidelity_svm")


def embed_angles(x: np.ndarray) -> np.ndarray:
    """Bound 4 selected z-scored real biomarkers to Ry angles; fixed, not learned."""
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or not np.all(np.isfinite(x)):
        raise ValueError("Expected finite 2D data")
    return 0.5 * np.pi * np.tanh(x / 2.0)


def fidelity_kernel(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """|<ψ(x)|ψ(y)>|², ψ(x)=⊗_j Ry(theta_j)|0>.

    Efficient classical simulation: NO quantum speedup/advantage is implied.
    """
    x = embed_angles(x)
    y = embed_angles(y)
    if x.shape[1] != y.shape[1]:
        raise ValueError("Mismatched feature dimensions")
    return np.prod(np.cos((x[:, None, :] - y[None, :, :]) / 2.0) ** 2, axis=2)


def preprocess_fold(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray):
    """Fit selectors and scaler ONLY on the training subset (avoid leakage)."""
    selector = SelectKBest(score_func=f_classif, k=4)
    a = selector.fit_transform(x_train, y_train)
    b = selector.transform(x_test)
    scaler = StandardScaler()
    return scaler.fit_transform(a), scaler.transform(b)


def evaluate_fold(x, y, train, test) -> dict:
    a, b = preprocess_fold(x[train], y[train], x[test])
    yt = y[train]
    yv = y[test]
    models = {
        "dummy_majority": DummyClassifier(strategy="most_frequent"),
        "logistic": LogisticRegression(max_iter=3000, random_state=0),
        "classical_rbf_svm": SVC(kernel="rbf", C=1.0, gamma="scale"),
    }
    scores = {}
    for key, clf in models.items():
        clf.fit(a, yt)
        pred = clf.predict(b)
        if key == "dummy_majority":
            confidences = clf.predict_proba(b)[:, list(clf.classes_).index(1)]
        elif key == "logistic":
            confidences = clf.predict_proba(b)[:, 1]
        else:
            confidences = clf.decision_function(b)
        scores[key] = {"balanced_accuracy": float(balanced_accuracy_score(yv, pred)),
                       "auroc": float(roc_auc_score(yv, confidences))}
    k_train = fidelity_kernel(a, a)
    k_test = fidelity_kernel(b, a)
    qclf = SVC(C=1.0, kernel="precomputed")
    qclf.fit(k_train, yt)
    qp = qclf.predict(k_test)
    qc = qclf.decision_function(k_test)
    scores["simulated_product_state_fidelity_svm"] = {
        "balanced_accuracy": float(balanced_accuracy_score(yv, qp)),
        "auroc": float(roc_auc_score(yv, qc)),
    }
    return scores


def run(seed: int = 20261118, repeats: int = 2, null_permutations: int = 5) -> dict:
    if repeats < 1 or null_permutations < 1:
        raise ValueError("repeats and null_permutations must be at least one")
    d = load_breast_cancer()
    x, y = d.data, d.target
    splits = RepeatedStratifiedKFold(n_splits=5, n_repeats=repeats, random_state=seed)
    folds = [evaluate_fold(x, y, tr, te) for tr, te in splits.split(x, y)]
    results = {model: {
        metric: {"mean": float(np.mean([f[model][metric] for f in folds])),
                 "sample_sd": float(np.std([f[model][metric] for f in folds], ddof=1)) if len(folds)>1 else None}
        for metric in ("balanced_accuracy", "auroc")}
        for model in MODELS}
    deltas = {metric: float(np.mean([f["simulated_product_state_fidelity_svm"][metric] - f["classical_rbf_svm"][metric] for f in folds]))
              for metric in ("balanced_accuracy", "auroc")}
    rng = np.random.default_rng(seed+1)
    null_scores = []
    for rep in range(null_permutations):
        shuffled = rng.permutation(y)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed + 10 + rep)
        for tr, te in cv.split(x, shuffled):
            fold = evaluate_fold(x, shuffled, tr, te)
            null_scores.append({"permutation": rep,
                                "auroc": fold["simulated_product_state_fidelity_svm"]["auroc"],
                                "balanced_accuracy": fold["simulated_product_state_fidelity_svm"]["balanced_accuracy"]})
    return {
        "status": "PASS_OFFLINE_BENCHMARK_ONLY",
        "claims": {"clinical_validation":"UNVERIFIED","longevity_efficacy":"UNVERIFIED",
                   "quantum_hardware_executed":False,"quantum_speedup":"UNVERIFIED",
                   "transfer_to_axolotl_HAND1_HAND2":"UNVERIFIED"},
        "method": {"dataset":DATASET_NAME,"dataset_sha256":hashlib.sha256(x.astype("<f8",copy=False).tobytes()+y.astype("i1").tobytes()).hexdigest(),
                   "numpy_version":np.__version__,"sklearn_version":sklearn.__version__,
                   "samples":int(x.shape[0]),"original_features":int(x.shape[1]),
                   "selected_features_per_fold":4,"selection_and_scaling":"train_fold_only",
                   "splits":"5-fold repeated stratified CV","repeats":repeats,"seed":seed,
                   "null_label_permutations":null_permutations,
                   "quantum_feature_map":"4 independent Ry rotations, product-state fidelity, entirely CPU simulated",
                   "baseline_features":"same 4 selected and scaled features",
                   "population":"breast cytology diagnosis (NOT aging or lifespan)",
                   "variability_caveat":"folds are correlated; sample_sd is descriptive, not a confidence interval"},
        "results":results,
        "quantum_minus_classical_rbf":deltas,
        "null_label_permutation":{
            "mean_auroc":float(np.mean([s["auroc"] for s in null_scores])),
            "mean_balanced_accuracy":float(np.mean([s["balanced_accuracy"] for s in null_scores])),
            "folds":len(null_scores),"details":null_scores},
        "fold_results":folds,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=Path("reports/factory/QUANTUM-BIOMED-FEASIBILITY-20261118.json"))
    p.add_argument("--seed",type=int,default=20261118)
    p.add_argument("--repeats",type=int,default=2)
    p.add_argument("--null-permutations",type=int,default=5)
    args=p.parse_args()
    result=run(seed=args.seed,repeats=args.repeats,null_permutations=args.null_permutations)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({"status":result["status"],"output":str(args.output),
                      "auroc":{k:round(v["auroc"]["mean"],4) for k,v in result["results"].items()},
                      "delta_auc_vs_rbf":round(result["quantum_minus_classical_rbf"]["auroc"],4),
                      "null_mean_auc":round(result["null_label_permutation"]["mean_auroc"],4)},sort_keys=True))

if __name__ == "__main__":
    main()