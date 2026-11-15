#!/usr/bin/env python3
"""ASTRA MEDICAL CLAIM AUDIT Ω — scientific abstract retrieval WITHOUT gold/oracle leakage.

Input: official SciFact (data/corpus.jsonl, data/claims_dev.jsonl).
retrieval input to rank(): claim string ONLY. Gold ids used ONLY by evaluate().
No clinical use, no patients, no paid API.
"""
import argparse
import collections
import hashlib
import json
import math
import pathlib
import re
import statistics

TERM = re.compile(r"[a-z0-9]+")
def tokens(text):
    if not isinstance(text,str): raise TypeError("query must be a string")
    return TERM.findall(text.lower())
def sha(blob): return hashlib.sha256(blob).hexdigest()
def load_jsonl(path):
    raw=pathlib.Path(path).read_bytes()
    return [json.loads(x) for x in raw.decode().splitlines() if x.strip()],sha(raw)

class BM25:
    def __init__(self, corpus, k1=1.2, b=0.75):
        if not corpus: raise ValueError("empty corpus")
        self.docs={}
        self.postings=collections.defaultdict(list)
        self.k1,self.b=k1,b
        lengths=[]
        for item in corpus:
            docid=str(item["doc_id"])
            if docid in self.docs: raise ValueError("duplicate doc_id")
            title=item.get("title","")
            abst=item.get("abstract",[])
            if not isinstance(abst,list): raise ValueError("abstract not list")
            self.docs[docid]={"title":title,"abstract":abst}
            tok=tokens(title+" "+" ".join(abst))
            freq=collections.Counter(tok)
            lengths.append(len(tok))
            for t,tf in freq.items(): self.postings[t].append((docid,tf,len(tok)))
        self.n=len(self.docs)
        self.avg_len=sum(lengths)/len(lengths) or 1
    def rank(self, query, k=5):
        if k<1:raise ValueError("k must be positive")
        terms=set(tokens(query))
        if not terms:return []
        scores=collections.defaultdict(float)
        for t in terms:
            posting=self.postings.get(t,[])
            df=len(posting)
            if not df: continue
            idf=math.log(1+(self.n-df+0.5)/(df+0.5))
            for docid,tf,dl in posting:
                den=tf+self.k1*(1-self.b+self.b*dl/self.avg_len)
                scores[docid]+=idf*(tf*(self.k1+1)/den)
        return [{"doc_id":d,"score":round(s,8)} for d,s in
                sorted(scores.items(),key=lambda x:(-x[1],x[0]))[:k]]
def gold_docs(row):
    return {str(i) for i in row.get("evidence",{})}
def evaluate(index,claims,ks=(1,3,5,10),store_topk=5):
    if len({x["id"] for x in claims})!=len(claims): raise ValueError("duplicate claim ids")
    labeled=0; hits={k:0 for k in ks}; rr=[]; ranks=[]
    out=[]
    for c in claims:
        # Important: NEVER pass labels, citations or gold document IDs to ranking.
        ranking=index.rank(c["claim"], max(max(ks),store_topk))
        gold=gold_docs(c)
        rank=next((j for j,r in enumerate(ranking,1) if r["doc_id"] in gold),None)
        if gold:
            labeled+=1
            for k in ks:hits[k]+=bool(rank is not None and rank<=k)
            rr.append(1/rank if rank else 0)
            ranks.append({"id":c["id"],"rank":rank,"gold_doc_count":len(gold)})
        out.append({"id":c["id"],"claim":c["claim"],"topk":ranking[:store_topk]})
    return {"protocol":"BM25 tokenized lower-case title+abstract, full 5183-doc corpus, no oracle IDs/cited_doc_ids or evidence at retrieval time",
            "n_queries":len(claims),"n_with_gold_evidence":labeled,
            "recall_at_k":{str(k):hits[k]/labeled if labeled else None for k in ks},
            "hit_counts":{str(k):hits[k] for k in ks},
            "mrr_at_10":sum(rr)/len(rr) if rr else None,
            "failed_retrieval_examples": [x for x in ranks if x["rank"] is None][:30],
            "retrieved":out}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--out",default="astra_bm25_scifact_v04.json")
    args=p.parse_args()
    root=pathlib.Path(args.root)
    corpus,csha=load_jsonl(root/"data/corpus.jsonl")
    claims,qsha=load_jsonl(root/"data/claims_dev.jsonl")
    if len(corpus)!=5183 or len(claims)!=300:raise RuntimeError("official SciFact shape mismatch")
    result=evaluate(BM25(corpus),claims)
    result.update({"version":"ASTRA MEDICAL CLAIM AUDIT Ω v0.4","dataset":"Official SciFact development; NO patient data",
                   "source_sha256":{"corpus":csha,"claims_dev":qsha},
                   "disclaimer":"Research-only document ranking. NO factual, scientific or medical decision."})
    pathlib.Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({x:result[x] for x in ("n_queries","n_with_gold_evidence","recall_at_k","hit_counts","mrr_at_10","source_sha256")},indent=2))
if __name__=="__main__":main()
