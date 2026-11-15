#!/usr/bin/env python3
"""ASTRA MEDICAL CLAIM AUDIT Ω v0.4 — specialized evidence verifier.

Predeclared evaluation protocol (no tuning on SciFact dev):
- BM25 retrieval is read from retrieval.json (generated from claim text only).
- Feed CLAIM FIRST, then 3 most claim-relevant sentences from the BM25 top-1 abstract (no gold).
- Thresholds fixed in THIS committed source BEFORE test:
      min_top1_bm25=8.0; min_max_softmax=0.90; min_top2_margin=0.20.
- Unsupported NEI always becomes ABSTAIN, never accepted as a medical verdict.
- Metric denominators include abstentions; abstention is not correctness.
- No clinical use. No patient data. No paid inference API.
"""
import argparse
import collections
import datetime
import hashlib
import json
import math
import pathlib
import sys
import time

MODEL_ID="rishhh/verisci-claim-verifier-retrieval-adapted-seed123"
# Explicitly pinned git commit (validated before downloading).
MODEL_REV="5bed61128b128f6f960aa80d1aa8ac3d1bdd9b0f"
MIN_BM25=8.0
MIN_PROB=0.90
MIN_MARGIN=0.20
MAX_TOKENS=512
GOLD=("SUPPORT","CONTRADICT","NEI")
MODEL_LABELS={"SUPPORTS":"SUPPORT","REFUTES":"CONTRADICT","NOT_ENOUGH_INFO":"NEI",
              "SUPPORT":"SUPPORT","CONTRADICT":"CONTRADICT","NEI":"NEI"}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def metrics(rows,pred_key):
    m={g:{p:0 for p in GOLD+("ABSTAIN",)} for g in GOLD}
    for row in rows:
        label=row[pred_key];m[row["gold"]][label]+=1
    n=len(rows); correct=sum(r["gold"]==r[pred_key] for r in rows)
    tp=m["CONTRADICT"]["CONTRADICT"]
    fp=m["SUPPORT"]["CONTRADICT"]+m["NEI"]["CONTRADICT"]
    fn=sum(v for k,v in m["CONTRADICT"].items() if k!="CONTRADICT")
    tn=n-tp-fp-fn
    decisive=[r for r in rows if r[pred_key] in ("SUPPORT","CONTRADICT")]
    return {"n":n,"three_way_accuracy_including_abstentions":correct/n,
            "accepted_decisive":len(decisive),"coverage":len(decisive)/n,
            "decisive_accuracy":sum(r["gold"]==r[pred_key] for r in decisive)/len(decisive) if decisive else None,
            "gold_rows_predictions_columns":m,"binary_contradiction":
             {"TP":tp,"FP":fp,"FN":fn,"TN":tn,
              "precision":tp/(tp+fp) if tp+fp else None,
              "recall":tp/(tp+fn) if tp+fn else None}}

def select_evidence_sentences(claim, sentences, limit=3):
    """No oracle evidence: simple claim-term overlap over retrieved abstract sentences."""
    import re
    terms=set(re.findall(r"[a-z0-9]+",claim.lower()))
    if not sentences:return ""
    if limit<1:raise ValueError("limit must be positive")
    score=[]
    for i,s in enumerate(sentences):
        ts=set(re.findall(r"[a-z0-9]+",str(s).lower()))
        score.append((len(terms & ts),i))
    best=sorted(score,key=lambda x:(-x[0],x[1]))[:limit]
    return " ".join(str(sentences[i]) for i in sorted(j for _,j in best))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--out",default="scifact_specialized_open_v04.json")
    args=ap.parse_args()
    root=pathlib.Path(args.root)
    retrieved=json.loads((root/"retrieval.json").read_text())
    if retrieved["n_queries"]!=300:raise ValueError("Unexpected retrieval size")
    claims=[json.loads(x) for x in (root/"data/claims_dev.jsonl").read_text().splitlines() if x]
    docs={str(x["doc_id"]):x for x in
          (json.loads(line) for line in (root/"data/corpus.jsonl").read_text().splitlines() if line)}
    rank_by_id={q["id"]:q for q in retrieved["retrieved"]}
    if len(rank_by_id)!=300:raise ValueError("Missing retrieval rows")
    # Gold labels only used for evaluation, NEVER used to select evidence docs.
    rows=[]
    for c in claims:
        ranking=rank_by_id[c["id"]]["topk"]
        if not ranking: raise RuntimeError("Empty ranking for claim "+str(c["id"]))
        if rank_by_id[c["id"]]["claim"]!=c["claim"]:raise RuntimeError("Claim mismatch")
        hit=ranking[0];doc=docs[hit["doc_id"]]
        gold_set={label for evidence in c["evidence"].values() for e in evidence for label in [e["label"]]}
        if len(gold_set)>1:raise RuntimeError("Ambiguous gold")
        gold=next(iter(gold_set),"NEI")
        if gold not in GOLD:raise ValueError(gold)
        text=select_evidence_sentences(c["claim"],doc["abstract"],limit=3)
        rows.append({"id":c["id"],"gold":gold,"claim":c["claim"],
                     "retrieved_id":hit["doc_id"],"bm25":hit["score"],
                     "evidence_text":text,"retrieval_hit":hit["doc_id"] in c["evidence"]})
    # Lazy model imports ensure retrieval runner has NO dependency on torch.
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    torch.set_num_threads(1)
    print("LOADING_SCIENCE_SPECIALIST",MODEL_ID,MODEL_REV,flush=True)
    t0=time.monotonic()
    tokenizer=AutoTokenizer.from_pretrained(MODEL_ID,revision=MODEL_REV,trust_remote_code=False)
    model=AutoModelForSequenceClassification.from_pretrained(MODEL_ID,revision=MODEL_REV,
                       trust_remote_code=False,low_cpu_mem_usage=True)
    model.eval()
    raw_mapping={str(k):v for k,v in model.config.id2label.items()}
    mapping={int(k):MODEL_LABELS.get(v) for k,v in raw_mapping.items()}
    if set(mapping.values())!=set(GOLD):raise RuntimeError("Unknown model labels "+str(raw_mapping))
    print("MODEL_READY",time.monotonic()-t0,raw_mapping,flush=True)
    for n,row in enumerate(rows):
        # Evidence is premise, claim is hypothesis. No annotated source ID is given.
        tokenized=tokenizer(row["claim"],row["evidence_text"],return_tensors="pt",
                            truncation=True,max_length=MAX_TOKENS)
        with torch.inference_mode():
            logits=model(**tokenized).logits[0].float()
            probs=torch.softmax(logits,dim=-1).tolist()
        order=sorted(range(len(probs)),key=lambda j:-probs[j])
        label=mapping[order[0]]
        conf=probs[order[0]];margin=probs[order[0]]-probs[order[1]]
        reasons=[]
        if label=="NEI":reasons.append("NO_SUFFICIENT_EVIDENCE_LABEL")
        if row["bm25"]<MIN_BM25:reasons.append("LOW_RETRIEVAL_SCORE")
        if conf<MIN_PROB:reasons.append("LOW_MODEL_CONFIDENCE")
        if margin<MIN_MARGIN:reasons.append("LOW_PROBABILITY_MARGIN")
        row["raw_pred"]=label
        row["selective_pred"]=label if not reasons else "ABSTAIN"
        row["probability"]=round(conf,8)
        row["margin"]=round(margin,8)
        row["abstain_reasons"]=reasons
        del row["evidence_text"],row["claim"] # no text or sensitive data in export
        if (n+1)%50==0:print("INFERENCE_PROGRESS",n+1,"of",len(rows),"seconds",round(time.monotonic()-t0,1),flush=True)
    for row in rows:
        row["correct_raw"]=row["gold"]==row["raw_pred"]
        row["correct_selective"]=row["gold"]==row["selective_pred"]
    retr_hits=sum(r["retrieval_hit"] for r in rows if r["gold"]!="NEI")
    report={
      "project":"ASTRA MEDICAL CLAIM AUDIT Ω v0.4",
      "timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "purpose":"Scientific RESEARCH ONLY; forbidden for treatment/diagnosis. Not clinically validated.",
      "model":{"id":MODEL_ID,"revision":MODEL_REV,"id2label":raw_mapping,
               "engine":"PyTorch CPU / transformers", "torch_version":torch.__version__,
               "transformers_version":__import__("transformers").__version__,
               "evidence_first":False,"max_tokens":MAX_TOKENS,
               "input_protocol":"claim_first_plus_top3_lexical_abstract_sentences; no gold",
               "verified_upstream_order":"https://huggingface.co/spaces/rishhh/verisci-claim-space/blob/main/src/verisci/verification/predict.py",
               "model_train_overlap_risk":"Possible dev evaluation overlap documented by publisher; not an independent hidden-test result",
               "unverified_claim":False},
      "retrieval":{"method":"BM25 tokenized title + abstract, oracle-free",
                   "n_docs":len(docs),"hit_top1_labeled":retr_hits,"n_labeled":sum(r["gold"]!="NEI" for r in rows),
                   "retrieval_source_sha256":sha((root/"retrieval.json").read_bytes()),
                   "gold_used_for_ranking":False},
      "predeclared_abstention":{"min_bm25":MIN_BM25,"min_prob":MIN_PROB,
                  "min_margin":MIN_MARGIN,"accept_nei":False,
                  "note":"Probability uncalibrated; threshold is a conservative rule not tuned on test labels"},
      "results":{"raw":metrics(rows,"raw_pred"),
                 "selective":metrics(rows,"selective_pred")},
      "failure_examples":[{k:r[k] for k in ("id","gold","raw_pred","selective_pred","retrieved_id","probability","abstain_reasons")}
                          for r in rows if not r["correct_raw"]][:35],
      "rows":[{k:r[k] for k in ("id","gold","raw_pred","selective_pred","retrieved_id","retrieval_hit","bm25","probability","margin","abstain_reasons")}
              for r in rows],
      "limitations":["Single public development corpus, potential training overlap","No independent clinical annotation",
       "Only top-1 retrieved abstract; retrieval gold annotations not fed to model",
       "No medical recommendation allowed","Confidence and margin are NOT clinically calibrated",
       "NEI always abstains, never asserts the underlying clinical claim is wrong"] }
    out=root/args.out
    payload=(json.dumps(report,indent=2,ensure_ascii=False)+"\n").encode()
    out.write_bytes(payload)
    print("FINAL_SUMMARY",json.dumps({"raw":report["results"]["raw"],
                      "selective":report["results"]["selective"],
                      "out_sha256":sha(payload),"elapsed_s":round(time.monotonic()-t0,2)},separators=(",",":")),flush=True)

if __name__=="__main__":main()
