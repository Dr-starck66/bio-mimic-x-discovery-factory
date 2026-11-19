#!/usr/bin/env python3
"""ASTRA MEDICAL Ω: open published-case exploratory evaluation (NOT clinical validation).

Dataset: zou-lab/MedCaseReasoning / default / test (897 published case reports).
No private, MIMIC, or patient EHR records; NO treatment or patient use.
Measures conservative normalized EXACT diagnosis string matches; NOT clinical equivalence.
Two prompt variants probe a Qwen model only; this does NOT evaluate the actual
SDBench sequential ASTRA agent or support clinical efficacy claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

DATASET = "zou-lab/MedCaseReasoning"
CONFIG = "default"
SPLIT = "test"
EXPECTED = 897
DATA_URL = "https://datasets-server.huggingface.co"
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m"
SEED = 20261119
N = 64
ABSTAIN = "ABSTAIN"

def get_json(url: str) -> dict:
    last = None
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ASTRA-Medical-Research/0.1"})
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("Data fetch failed") from last

def read_test_split() -> tuple[list[dict], str]:
    base = get_json(DATA_URL + "/splits?" + urllib.parse.urlencode({"dataset": DATASET}))
    splits = [s for s in base["splits"] if s["config"] == CONFIG and s["split"] == SPLIT]
    assert len(splits) == 1 and splits[0]["num_rows"] == EXPECTED, "Unexpected dataset split; stop"
    all_rows = []
    for off in range(0, EXPECTED, 100):
        url = DATA_URL + "/rows?" + urllib.parse.urlencode({
            "dataset": DATASET, "config": CONFIG, "split": SPLIT,
            "offset": off, "length": min(100, EXPECTED - off)})
        data = get_json(url)
        part = data["rows"]
        assert len(part) == min(100, EXPECTED - off), ("Incomplete test batch", off, len(part))
        assert [r["row_idx"] for r in part] == list(range(off, off + len(part)))
        all_rows.extend([r["row"] for r in part])
    rev = get_json("https://huggingface.co/api/datasets/" + DATASET).get("sha", "UNKNOWN")
    assert len(all_rows) == EXPECTED
    return all_rows, rev

def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))

def wilson95(success: int, n: int) -> list[float]:
    import math
    if not n:
        return [0.0, 1.0]
    z = 1.959963984540054
    p = success / n
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    radius = z / (1 + z*z/n) * math.sqrt((p*(1-p) + z*z/(4*n))/n)
    return [round(max(0,center-radius), 5), round(min(1,center+radius), 5)]

def create_model(model_path: str):
    from llama_cpp import Llama
    return Llama(model_path=model_path, n_ctx=4096, n_batch=512, n_threads=2, verbose=False)

PROMPTS = {
    "direct": (
        "You are evaluating a previously published, de-identified medical case report. "
        "Return ONLY the single most likely specific final diagnosis as a short medical term, "
        "not a list, no rationale, no management advice. This is not for patient care."
    ),
    "evidence_gated_prompt": (
        "You are an experimental, evidence-gated research classifier on a published clinical case. "
        "If the presentation lacks the evidence needed to choose a specific disease, "
        "reply exactly ABSTAIN. Otherwise output ONLY the single most likely final diagnosis "
        "as a short medical term. No rationale, no management advice. "
        "This is not for patient care."
    ),
}

def generate(llm, mode: str, presentation: str) -> tuple[str, int]:
    ans = llm.create_chat_completion(
        messages=[{"role":"system", "content": PROMPTS[mode]},
                  {"role":"user", "content":"Clinical presentation:\n"+presentation}],
        max_tokens=48, temperature=0.0, top_p=1.0)
    content = (ans["choices"][0]["message"].get("content") or "").strip()
    return content, int(ans["usage"]["completion_tokens"])

def run(model_path: str, out: Path, n: int=N, seed: int=SEED):
    assert 2 <= n <= EXPECTED
    assert out.parent.exists()
    cases, rev = read_test_split()
    ids = sorted(random.Random(seed).sample(range(EXPECTED), n))
    selected = [cases[i] for i in ids]
    keys = [(x.get("pmcid",""), x.get("case_prompt",""), x.get("final_diagnosis","")) for x in selected]
    assert all(isinstance(a,str) and isinstance(b,str) and isinstance(c,str) and a and b and c for a,b,c in keys)
    assert len(set(a for a,_,_ in keys)) == n, "Duplicate source article in selected sample"
    model_sha = hashlib.sha256(Path(model_path).read_bytes()).hexdigest()
    pre = {
        "scope":"exploratory, publicly published clinical case reports; not patient-level clinical validity",
        "dataset":DATASET, "dataset_repo_sha":rev, "dataset_config":CONFIG,
        "split":SPLIT, "split_rows":EXPECTED, "selection_seed":seed,
        "selection_row_indices":ids, "sample_n":n,
        "model_id":MODEL_ID, "model_sha256":model_sha,
        "temperature":0.0, "max_tokens":48,
        "modes":list(PROMPTS),
        "scoring":"normalized exact string only, never substitute for physician adjudication",
        "agent_warning":"Prompt-only prototype, NOT existing ASTRA SDBench sequential agent",
        "note":"The source published PMC articles may be present in base model pretraining.",
    }
    (out / "preregistered_manifest.json").write_text(json.dumps(pre,indent=2)+"\n")
    print("PREREGISTERED", json.dumps({"n":n,"seed":seed,"dataset_sha":rev,"model_sha":model_sha}), flush=True)
    llm = create_model(model_path)
    predictions = out / "predictions_research_only.jsonl"
    rows = []
    for position, (i, record) in enumerate(zip(ids, selected)):
        presentation = record["case_prompt"]
        reference = record["final_diagnosis"]
        leakage = len(normalize(reference))>=8 and normalize(reference) in normalize(presentation)
        for mode in PROMPTS:
            started = time.monotonic()
            try:
                prediction, completion_tokens = generate(llm, mode, presentation)
                error = None
            except Exception as exc:
                prediction, completion_tokens = "", 0
                error = type(exc).__name__ + ": " + str(exc)[:120]
            abstained = normalize(prediction) in ("abstain","unable to provide diagnosis")
            exact = (not error and not abstained and normalize(prediction) == normalize(reference))
            row = {
                "position":position, "test_row_index":i,
                "pmcid":record["pmcid"], "mode":mode, "prediction":prediction[:250],
                "reference_diagnosis":reference, "exact_match":bool(exact), "abstained":bool(abstained),
                "possible_label_leakage":bool(leakage), "error":error,
                "completion_tokens":completion_tokens, "seconds":round(time.monotonic()-started,3),
                "case_prompt_sha256":hashlib.sha256(presentation.encode()).hexdigest(),
                "case_prompt_characters":len(presentation)
            }
            with predictions.open("a",encoding="utf8") as f:
                f.write(json.dumps(row,ensure_ascii=False)+"\n")
            rows.append(row)
        print("CASE",position+1,"of",n,"direct_exact",rows[-2]["exact_match"],
              "guard_exact",rows[-1]["exact_match"],"guard_abstain",rows[-1]["abstained"],flush=True)
    result = dict(pre)
    result["status"] = "EXPLORATORY_PUBLIC_CASE_REPORT_DIAGNOSIS_NOT_CLINICAL_VALIDATION"
    result["results"] = {}
    for mode in PROMPTS:
        rr = [x for x in rows if x["mode"]==mode]
        success = sum(x["exact_match"] for x in rr)
        abstain = sum(x["abstained"] for x in rr)
        errors = sum(bool(x["error"]) for x in rr)
        clean = [x for x in rr if not x["possible_label_leakage"]]
        success_clean = sum(x["exact_match"] for x in clean)
        result["results"][mode] = {
            "n":len(rr), "exact_match_count":success,"exact_match_fraction":round(success/len(rr),5),
            "wilson95_exact_match":wilson95(success,len(rr)),
            "abstentions":abstain,"inference_errors":errors,
            "possible_label_leakage_cases":len(rr)-len(clean),
            "non_leak_exact_count":success_clean,"non_leak_n":len(clean),
            "non_leak_wilson95":wilson95(success_clean,len(clean))}
    paired = []
    for idx in ids:
        rr = [x for x in rows if x["test_row_index"] == idx]
        assert len(rr)==2
        paired.append([rr[0]["exact_match"],rr[1]["exact_match"]])
    result["paired"] = {
        "direct_only_exact":sum(a and not b for a,b in paired),
        "guard_only_exact":sum(b and not a for a,b in paired),
        "both_exact":sum(a and b for a,b in paired),
        "both_inexact":sum(not a and not b for a,b in paired)}
    result["negative_controls"] = {
        "always_abstain_baseline_exact":0,
        "shifted_reference_false_matches":sum(
             normalize(r["prediction"]) == normalize(
                cases[ids[(j+1)%n]]["final_diagnosis"])
             for j, r in enumerate(x for x in rows if x["mode"]=="direct")),
        "case_prompt_not_included_in_shared_summary":True}
    result["predictions_file_sha256"] = hashlib.sha256(predictions.read_bytes()).hexdigest()
    (out / "public_medcase_summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("RESULT",json.dumps(result["results"],ensure_ascii=False),flush=True)
    print("STATUS",result["status"],flush=True)
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model",required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--n",type=int,default=N)
    p.add_argument("--seed",type=int,default=SEED)
    args = p.parse_args()
    run(args.model,args.out,args.n,args.seed)

if __name__=="__main__":
    main()
