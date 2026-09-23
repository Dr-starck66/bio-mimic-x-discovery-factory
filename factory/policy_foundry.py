#!/usr/bin/env python3
from __future__ import annotations
import copy, json, math

def propose_variants(policy,telemetry):
    """Generate policy/config variants only. Never edits source code."""
    base=copy.deepcopy(policy)
    variants=[]
    knobs=[
        ("exploration_rate",[-0.05,0.05]),
        ("minimum_sources",[-1,1]),
        ("morpheus_penalty",[-0.05,0.05]),
        ("novelty_weight",[-0.05,0.05])
    ]
    for knob,deltas in knobs:
        for d in deltas:
            v=copy.deepcopy(base)
            old=float(v.get(knob,0.5 if "weight" in knob or "rate" in knob or "penalty" in knob else 2))
            nv=old+d
            if knob=="minimum_sources": nv=max(1,round(nv))
            else: nv=max(0.0,min(1.0,nv))
            v[knob]=nv
            v["_variant"]=f"{knob}:{d:+}"
            variants.append(v)
    return variants

def score_variant(v,telemetry):
    # Conservative proxy from measured prior metrics; never treated as biological evidence.
    precision=float(telemetry.get("verified_ratio",0))
    diversity=float(telemetry.get("cross_lab_diversity",0))
    falsepos=float(telemetry.get("false_positive_rate",0))
    resilience=float(telemetry.get("provider_success_ratio",1))
    minsrc=float(v.get("minimum_sources",2))
    morp=float(v.get("morpheus_penalty",0.2))
    nov=float(v.get("novelty_weight",0.3))
    explore=float(v.get("exploration_rate",0.2))
    return (
        precision*0.35 + diversity*0.20 + resilience*0.20 +
        min(1,nov+explore)*0.15 - falsepos*(0.25+morp*0.25) +
        min(0.08,minsrc*0.02)
    )

def select_safe_variant(current,variants,telemetry,min_gain=0.01):
    base=score_variant(current,telemetry)
    ranked=sorted([(score_variant(v,telemetry),v) for v in variants],key=lambda x:x[0],reverse=True)
    best_score,best=ranked[0] if ranked else (base,current)
    # Immune gate: block changes when false positives are high or gain is too small.
    if float(telemetry.get("false_positive_rate",0))>0.35:
        return {"accepted":False,"reason":"false_positive_rate_too_high","policy":current,"base_score":base,"best_score":best_score}
    if best_score < base + min_gain:
        return {"accepted":False,"reason":"no_measured_gain","policy":current,"base_score":base,"best_score":best_score}
    return {"accepted":True,"reason":"measured_proxy_gain","policy":best,"base_score":base,"best_score":best_score}
