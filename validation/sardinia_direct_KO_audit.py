"""Sardinia PRJEB25514: fail-closed direct K01442 / recA replication.

Accepts real per-run HUMAnN UniRef90->KO regrouped, unstratified RPK tables
and validated 59-run manifest. Does NOT sequence, profile or claim direct
BSH activity. No source data are provided by this module.
"""
import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

CODES = ("K01442", "K03553", "K03043")  # BSH; recA; rpoB control
GROUPS = {"Centenarian": 19, "Elderly": 23, "Young": 17}


def manifest(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    needed = ("run_accession", "published_sample_id", "group",
              "fastq_1_md5", "fastq_2_md5")
    if len(rows) != 59 or Counter(x["group"] for x in rows) != GROUPS:
        raise ValueError("Expected exactly 59 group-labelled Sardinian runs")
    if any(not all(x.get(c) for c in needed) for x in rows):
        raise ValueError("Run manifest missing required fields")
    if len({x["run_accession"] for x in rows}) != 59:
        raise ValueError("Duplicated run accession")
    if len({x["published_sample_id"] for x in rows}) != 59:
        raise ValueError("Duplicated individual")
    return rows


def read_ko_table(path):
    with open(path, encoding="utf-8", newline="") as f:
        lines = list(csv.reader(f, delimiter="\t"))
    if len(lines) < 2:
        raise ValueError(f"Empty KO table: {path}")
    if len(lines[0]) != 2 or not lines[0][0].startswith("#"):
        raise ValueError(f"Expected HUMAnN gene-family header and single RPK column: {path}")
    features = {}
    for row in lines[1:]:
        if len(row) != 2:
            raise ValueError(f"Invalid HUMAnN table shape: {path}")
        name = row[0].replace("ko:", "", 1)
        if "|" in name or name not in CODES:
            continue  # ignore taxon-stratified features; no double-counting
        if name in features:
            raise ValueError(f"Duplicated unstratified KO {name}: {path}")
        try:
            n = float(row[1])
        except ValueError as exc:
            raise ValueError(f"Not numeric {name}: {path}") from exc
        if not math.isfinite(n) or n < 0:
            raise ValueError(f"Invalid {name} abundance: {path}")
        features[name] = n
    if set(features) != set(CODES):
        raise ValueError(f"Missing K01442/K03553/K03043 in {path}; zero must be explicit")
    if features["K03553"] <= 0:
        raise ValueError(f"Zero recA K03553 in {path}; cannot normalize")
    return features


def auc(positive, negative):
    if not positive or not negative:
        raise ValueError("Two nonempty groups required")
    wins = sum(1 if x > y else 0.5 if x == y else 0
               for x in positive for y in negative)
    return wins/(len(positive)*len(negative))


def stratified_p(records, score_key, n=1999, seed=20261122):
    # Only groups with both cases and controls in the same run prefix
    strata = defaultdict(list)
    for x in records:
        strata[x["run_accession"][:6]].append(x)
    rng = random.Random(seed)
    observed = auc([x[score_key] for x in records if x["group"] == "Centenarian"],
                   [x[score_key] for x in records if x["group"] == "Elderly"])
    exceed = 0
    for _ in range(n):
        permuted = []
        for sample in strata.values():
            labels = [x["group"] for x in sample]
            rng.shuffle(labels)
            permuted.extend([dict(x, group=g) for x, g in zip(sample, labels)])
        trial = auc([x[score_key] for x in permuted if x["group"] == "Centenarian"],
                    [x[score_key] for x in permuted if x["group"] == "Elderly"])
        if abs(trial-0.5) >= abs(observed-0.5)-1e-12:
            exceed += 1
    return (exceed + 1)/(n + 1)


def analyse(manifest_path, tables_dir, epsilon=0.01, repetitions=1999):
    if epsilon <= 0 or not math.isfinite(epsilon):
        raise ValueError("Epsilon must be positive and finite RPK units")
    if repetitions < 99:
        raise ValueError("At least 99 permutations required")
    runs = manifest(manifest_path)
    data = []
    for x in runs:
        path = Path(tables_dir) / (x["run_accession"] + "_ko.tsv")
        if not path.is_file():
            raise ValueError(f"Missing measured KO file: {path}")
        vals = read_ko_table(path)
        rec = dict(x)
        rec["K01442_RPK"] = vals["K01442"]
        rec["K03553_RPK"] = vals["K03553"]
        rec["K03043_RPK"] = vals["K03043"]
        rec["bsh_log_ratio"] = math.log((vals["K01442"] + epsilon) /
                                        (vals["K03553"] + epsilon))
        rec["rpoB_log_ratio"] = math.log((vals["K03043"] + epsilon) /
                                         (vals["K03553"] + epsilon))
        data.append(rec)
    # Important: pre-specified run-prefix batch sensitivity.
    subsets = {
        "all_59_case_vs_elderly": [x for x in data if x["group"] != "Young"],
        "ERR350_batch_only": [x for x in data if x["run_accession"].startswith("ERR350")
                              and x["group"] != "Young"],
    }
    reports = {}
    for label, subset in subsets.items():
        cases = [x for x in subset if x["group"] == "Centenarian"]
        controls = [x for x in subset if x["group"] == "Elderly"]
        if len(cases) < 5 or len(controls) < 5:
            raise ValueError(f"Insufficient within-batch overlap: {label}")
        reports[label] = {
            "centenarians": len(cases), "elderly": len(controls),
            "bsh_auc": auc([x["bsh_log_ratio"] for x in cases],
                           [x["bsh_log_ratio"] for x in controls]),
            "rpoB_negative_control_auc": auc([x["rpoB_log_ratio"] for x in cases],
                                              [x["rpoB_log_ratio"] for x in controls]),
            "bsh_stratified_permutation_p": stratified_p(subset, "bsh_log_ratio", repetitions),
            "rpoB_stratified_permutation_p": stratified_p(subset, "rpoB_log_ratio", repetitions),
        }
    sensitivity = {}
    for pseudo in (0.001, 0.01, 0.1, 1.0):
        cohort = subsets["all_59_case_vs_elderly"]
        def transformed(g):
            return [math.log((x["K01442_RPK"] + pseudo)/(x["K03553_RPK"] + pseudo))
                    for x in cohort if x["group"] == g]
        sensitivity[str(pseudo)] = auc(transformed("Centenarian"), transformed("Elderly"))
    return {
        "status": "PARTIAL_RETROSPECTIVE_ASSOCIATION_ONLY",
        "source": "ENA PRJEB25514, complete individual HUMAnN regrouped KO measurements required",
        "records": len(data), "units": "HUMAnN RPK (not counts)", "pseudocount_RPK": epsilon,
        "batch_stratification": "run accession prefix ERR239/ERR347/ERR350",
        "results": reports, "pseudocount_sensitivity": sensitivity,
        "matched_quantification_to_2026_reference_method": False,
        "biological_enzyme_activity_proven": False,
        "future_metabolic_prediction_proven": False,
        "independent_BSH_gene_association_calculated": True,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--ko-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    try:
        result = analyse(args.manifest, args.ko_dir)
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED_NO_REPLICATION", "reason": str(exc)}, indent=2))
        raise SystemExit(2)
    rendered = json.dumps(result, indent=2)
    if args.out:
        args.out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
