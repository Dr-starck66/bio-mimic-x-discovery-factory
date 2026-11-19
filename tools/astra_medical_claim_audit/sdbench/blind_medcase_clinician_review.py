#!/usr/bin/env python3
"""Prepare TWO-stage independent clinician review packets for published MedCaseReasoning cases.

No deployment or patient-care use. Dataset: public published case reports only.
Stage 1 hides reference and model outputs; stage 2 reveals the reference
and shuffled candidate diagnoses but NOT model identities. Send to >=2 independent
licensed clinicians. Private unblinding key remains local; never upload it publicly.
"""
import argparse
import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

VALID_MODES = ("direct", "evidence_gated_prompt")

def digest(text):
    return hashlib.sha256(text.encode("utf8")).hexdigest()

def prepare(selected, predictions, seed=20261119):
    by_id = defaultdict(list)
    for row in predictions:
        by_id[row["test_row_index"]].append(row)
    if not selected or set(selected) != set(by_id):
        raise ValueError("Incomplete or non-matching sample")
    stage1, stage2, private = [], [], []
    rng = random.Random(seed + 7001)
    for pos, idx in enumerate(sorted(selected)):
        item = selected[idx]
        rows = by_id[idx]
        if sorted(r["mode"] for r in rows) != sorted(VALID_MODES):
            raise ValueError("Each case must contain exactly two candidate modes")
        if len(rows)!=2 or any(r.get("case_prompt_sha256") != digest(item["case_prompt"]) for r in rows):
            raise ValueError("Case presentation checksum mismatch")
        case_code = "C-" + digest(str(seed) + ":" + str(idx))[:12].upper()
        prompt = item["case_prompt"]
        reference = item["final_diagnosis"]
        if not prompt.strip() or not reference.strip():
            raise ValueError("Missing essential clinical presentation or reference label")
        stage1.append({
            "case_code":case_code, "case_presentation":prompt,
            "independent_clinician_diagnosis":"", "confidence_1_to_5":"",
            "critical_missing_data":"", "reviewer_id":"", "date_utc":""})
        order = list(VALID_MODES)
        rng.shuffle(order)
        pred = {r["mode"]:r for r in rows}
        stage2.append({
            "case_code":case_code, "reference_diagnosis":reference,
            "candidate_A":pred[order[0]]["prediction"],
            "candidate_B":pred[order[1]]["prediction"],
            "A_equivalence_0_no_1_uncertain_2_yes":"",
            "B_equivalence_0_no_1_uncertain_2_yes":"",
            "A_potential_serious_harm_0_no_1_yes":"",
            "B_potential_serious_harm_0_no_1_yes":"",
            "comments":"", "reviewer_id":"", "date_utc":""})
        private.append({"case_code":case_code, "test_row_index":idx,
                        "dataset_pmcid":item["pmcid"],
                        "candidate_A_mode":order[0],"candidate_B_mode":order[1],
                        "reference_diagnosis":reference,
                        "reference_present_in_presentation":reference.casefold() in prompt.casefold()})
    return stage1, stage2, private

def write_csv(path, rows):
    if not rows: raise ValueError("No rows")
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--predictions",type=Path,required=True)
    p.add_argument("--preregistered",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    from open_medcase_qwen05b_experiment import read_test_split
    manifest=json.loads(args.preregistered.read_text())
    if manifest.get("dataset")!="zou-lab/MedCaseReasoning" or manifest.get("split")!="test":
        raise ValueError("Only the public MedCaseReasoning held-out split is supported")
    ids=manifest["selection_row_indices"]
    allcases,revision=read_test_split()
    if revision!=manifest["dataset_repo_sha"]:raise ValueError("Dataset revision changed; stop")
    preds=[json.loads(x) for x in args.predictions.read_text().splitlines() if x.strip()]
    if len(preds)!=2*len(ids):raise ValueError("Incomplete predictions; cannot prepare review")
    selected={i:allcases[i] for i in ids}
    stage1,stage2,key=prepare(selected,preds,manifest["selection_seed"])
    args.out.mkdir(exist_ok=True,parents=True)
    write_csv(args.out/"stage1_blind_casebook.csv",stage1)
    write_csv(args.out/"stage2_blind_diagnosis_equivalence.csv",stage2)
    # Private key contains ground truth and mappings: keep inside controlled research environment.
    (args.out/"PRIVATE_unblinding_key.json").write_text(json.dumps(key,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":"PREPARED_FOR_HUMAN_REVIEW_NOT_CLINICALLY_VALIDATED","n":len(ids),
          "case_source":"public published reports",
          "stage1_sha256":hashlib.sha256((args.out/"stage1_blind_casebook.csv").read_bytes()).hexdigest(),
          "stage2_sha256":hashlib.sha256((args.out/"stage2_blind_diagnosis_equivalence.csv").read_bytes()).hexdigest(),
          "private_key_not_for_publication":True}))

if __name__=="__main__":main()
