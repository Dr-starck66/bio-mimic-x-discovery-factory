#!/usr/bin/env python3
"""ASTRA MEDICAL: auditeur agrégé des 7 paires OS NATALEE à six ans.
Les IC arrondis ne permettent qu'un Wald approximatif entre sous-groupes
disjoints ; ne pas assimiler ceci à une interaction validée sur IPD.
Source: https://doi.org/10.1016/j.annonc.2026.10.1288
Aucun dossier individuel, aucune prédiction clinique.
"""
import json
import math

SUBGROUPS = {
 "ganglions":[("N0",.790,.407,1.533),("N1-3",.817,.661,1.009)],
 "stade":[("II",.830,.543,1.269),("III",.798,.635,1.003)],
 "chimiotherapie_precedente":[("oui",.834,.677,1.028),("non",.623,.294,1.320)],
 "hormonotherapie_precedente":[("oui",.858,.667,1.105),("non",.767,.549,1.072)],
 "menopause":[("pre",.705,.494,1.006),("post",.884,.692,1.129)],
 "region":[("AmeriqueNord_EuropeOceanie",.859,.657,1.122),("autres_regions",.776,.572,1.053)],
 "Ki67":[("<=20%",.827,.598,1.143),(">20%",.812,.602,1.095)]
}

def log_hr_se(hr, low, high):
    if not all(math.isfinite(v) for v in (hr,low,high)) or not 0<low<hr<high:
        raise ValueError("invalid hazard ratio or CI")
    return math.log(hr), (math.log(high)-math.log(low))/(2*1.959963984540054)

def compare(pair):
    if len(pair)!=2 or pair[0][0]==pair[1][0]:
        raise ValueError("expected two different categories")
    a,sa=log_hr_se(*pair[0][1:])
    b,sb=log_hr_se(*pair[1][1:])
    delta, sd=a-b,math.hypot(sa,sb)
    return {
      "categories":[pair[0][0],pair[1][0]],
      "HR":[pair[0][1],pair[1][1]],
      "ratio_HR":math.exp(delta),
      "CI95_ratio_HR_approx":[math.exp(delta-1.959963984540054*sd),math.exp(delta+1.959963984540054*sd)],
      "p_Wald_approx":math.erfc(abs(delta/sd)/math.sqrt(2))
    }

def holm(values):
    if not values or any(not math.isfinite(p) or not 0<=p<=1 for p in values):
        raise ValueError("invalid p-values")
    ordered=sorted(range(len(values)),key=lambda i:values[i]);out=[0.]*len(values);prev=0.
    for rank,i in enumerate(ordered):
        prev=max(prev,(len(values)-rank)*values[i])
        out[i]=min(1.,prev)
    return out

def audit():
    names=list(SUBGROUPS)
    results=[compare(SUBGROUPS[n]) for n in names]
    adjusted=holm([r["p_Wald_approx"] for r in results])
    for r,p in zip(results,adjusted):r["p_Holm_sept_paires"]=p
    return {
       "source":"https://doi.org/10.1016/j.annonc.2026.10.1288",
       "date":"2026-11-19",
       "endpoint":"overall survival at six years",
       "disclaimer":"Exploratory approximate Wald test on rounded published disjoint subgroup CIs; no IPD, no formal treatment interaction test or causal patient-responder model",
       "subgroups":dict(zip(names,results)),
       "n_raw_p_lt_005":sum(r["p_Wald_approx"]<.05 for r in results),
       "n_holm_p_lt_005":sum(p<.05 for p in adjusted),
       "gene_expression_ASCO_2026":"3022 tumor samples, PAM50 treatment interaction P=0.34; genes CEACAM6 NOD2 GPX3 GATA3 SLC39A6 MAPT exploratory, no validated treatment selection marker",
       "methodology":"Under a no-treatment-by-covariate Cox model, relative HR is identical for all x, although predicted absolute benefits vary with baseline risk. This is a model identity, not a demonstration of biological homogeneity."
    }

if __name__=="__main__":
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
