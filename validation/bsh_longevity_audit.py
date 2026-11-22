"""BIO-MIMIC X: retrospective, association-only audit of microbial BSH K01442.

Input is a user-supplied *measured* TSV (not a sample metadata export):
subject_id, group, cbh_K01442, recA, negative_control, sex, batch.
The negative control must be preregistered and unrelated to bile acids.
BSH DNA abundance is a proxy, not directly measured enzymatic activity.
"""
import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path

GROUPS = ("Elderly_control", "Centenarian")
REQUIRED = ("subject_id", "group", "cbh_K01442", "recA", "negative_control", "sex", "batch")


def load_subjects(path):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        missing = set(REQUIRED).difference(reader.fieldnames or ())
        if missing:
            raise ValueError("Missing measured fields: " + ", ".join(sorted(missing)))
        raw = list(reader)
    if not raw:
        raise ValueError("No rows")
    grouped = defaultdict(list)
    for ix, row in enumerate(raw, 2):
        if row["group"] not in GROUPS:
            raise ValueError(f"Unsupported group on line {ix}: {row['group']}")
        if any(not row[k].strip() for k in REQUIRED):
            raise ValueError(f"Blank required field on line {ix}")
        for k in ("cbh_K01442", "recA", "negative_control"):
            try:
                x = float(row[k])
            except ValueError as e:
                raise ValueError(f"Non-numeric {k} on line {ix}") from e
            if not math.isfinite(x) or x < 0:
                raise ValueError(f"Invalid {k} on line {ix}")
            row[k] = x
        if row["recA"] == 0:
            raise ValueError(f"Zero recA reference on line {ix}")
        grouped[row["subject_id"]].append(row)
    subjects = []
    for sid, records in grouped.items():
        for k in ("group", "sex", "batch"):
            if len({x[k] for x in records}) > 1:
                raise ValueError(f"Subject {sid} has contradictory {k}; cannot aggregate")
        bsh = sum(math.log((r["cbh_K01442"] + 0.5)/(r["recA"] + 0.5)) for r in records)/len(records)
        ctrl = sum(math.log((r["negative_control"] + 0.5)/(r["recA"] + 0.5)) for r in records)/len(records)
        subjects.append({"id": sid, "group":records[0]["group"], "sex":records[0]["sex"],
                         "batch":records[0]["batch"],"bsh":bsh,"control":ctrl,"replicates":len(records)})
    return subjects


def auc(positive, negative):
    if not positive or not negative:
        raise ValueError("Both groups are required")
    wins = sum((1 if p > n else (0.5 if p == n else 0)) for p in positive for n in negative)
    return wins/(len(positive)*len(negative))


def group_auc(subjects, key):
    return auc([x[key] for x in subjects if x["group"] == "Centenarian"],
               [x[key] for x in subjects if x["group"] == "Elderly_control"])


def run(path, seed=42, iterations=499):
    subjects = load_subjects(path)
    counts = {g:sum(x["group"] == g for x in subjects) for g in GROUPS}
    if min(counts.values()) < 10:
        raise ValueError("At least 10 distinct subjects per group required")
    rng = random.Random(seed)
    score = group_auc(subjects,"bsh")
    neg_score = group_auc(subjects,"control")
    # Permute within sex x batch to preserve recorded technical/demographic structure.
    strata = defaultdict(list)
    for i, x in enumerate(subjects):
        strata[(x["sex"],x["batch"])].append(i)
    if not any(len({subjects[i]["group"] for i in idx}) == 2 for idx in strata.values()):
        raise ValueError("Sex/batch strata have no overlapping groups; association non-identifiable")
    exceed = 0
    for _ in range(iterations):
        perm = [x.copy() for x in subjects]
        for idx in strata.values():
            labels = [subjects[i]["group"] for i in idx]
            rng.shuffle(labels)
            for j, lab in zip(idx, labels):
                perm[j]["group"] = lab
        trial = group_auc(perm,"bsh")
        if abs(trial-.5) >= abs(score-.5) - 1e-12:
            exceed += 1
    # Subject-level bootstrap within each group: exploratory difference from control.
    pos = [x for x in subjects if x["group"] == "Centenarian"]
    old = [x for x in subjects if x["group"] == "Elderly_control"]
    bootstrap_diff = []
    for _ in range(iterations):
        sample = [rng.choice(pos) for _ in pos] + [rng.choice(old) for _ in old]
        bootstrap_diff.append(group_auc(sample,"bsh")-group_auc(sample,"control"))
    bootstrap_diff.sort()
    lo = bootstrap_diff[int(.025*(iterations-1))]
    hi = bootstrap_diff[int(.975*(iterations-1))]
    return {
        "status":"PARTIAL_ASSOCIATION_ONLY", "source":str(path), "n_subjects":len(subjects),
        "n_records":sum(x["replicates"] for x in subjects),"group_counts":counts,
        "bsh_auc_retrospective":round(score,5),"negative_control_auc_retrospective":round(neg_score,5),
        "paired_auc_gain_ci95_exploratory":[round(lo,5),round(hi,5)],
        "stratified_permutation_p_bsh_vs_random":round((1+exceed)/(1+iterations),5),
        "permutations":iterations,"strata_count":len(strata),"seed":seed,
        "bsh_activity_directly_assayed":False,"metabolic_phenotype_measured":False,
        "independent_cohort_validated":False,"prospective_biomarker_validation":"UNVERIFIED",
        "interpretation":"Cross-sectional gene-abundance association, NOT metabolic prediction or causal effect"
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path)
    p.add_argument("--iterations",type=int,default=499)
    a=p.parse_args()
    if a.iterations < 19: p.error("--iterations must be >=19")
    try:
        data = run(a.input,iterations=a.iterations)
    except (ValueError,OSError) as e:
        data={"status":"FAIL_CLOSED_NO_CLAIM","error":str(e)}
        print(json.dumps(data,indent=2,ensure_ascii=False))
        raise SystemExit(2)
    result=json.dumps(data,indent=2,ensure_ascii=False)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(result+"\n",encoding="utf-8")
    print(result)

if __name__=="__main__": main()
