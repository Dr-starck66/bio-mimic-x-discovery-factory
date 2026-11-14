#!/usr/bin/env python3
"""Regression controls for exact cloud-run Mk + joint fossil model."""
import contextlib, io, json, runpy
from pathlib import Path

with contextlib.redirect_stdout(io.StringIO()):
    mod=runpy.run_path(str(Path(__file__).parent/"runner_mk_joint_v07.py"))
checks=[]
for source in ("hendrickx","baron_josephwb_edited"):
    names,A,trees,sha=mod["parse"](source)
    assert len(names)==(61 if source=="hendrickx" else 75)
    checks.append(source+":dimensions")
    assert len(A[0])==(71 if source=="hendrickx" else 457)
    checks.append(source+":characters")
    states=list("0123" if source=="hendrickx" else "01234")
    target=next(i for i,row in enumerate(A) if sum(x in states for x in row)>=10 and sum(x in states for j,x in enumerate(row) if j%5==0)>=3)
    j=next(j for j,v in enumerate(A[target]) if j%5!=0 and v in states)
    tr=mod["build"](trees[0])
    base=mod["mk"](tr,A,j,states)[target]
    joint=mod["joint"](A,target,j,base,states)
    B=[row.copy() for row in A]
    B[target][j]=next(v for v in states if v!=A[target][j])
    newbase=mod["mk"](tr,B,j,states)[target]
    newjoint=mod["joint"](B,target,j,newbase,states)
    assert max(abs(a-b) for a,b in zip(base,newbase))<1e-12
    checks.append(source+":mk_no_target_label_leakage")
    assert max(abs(a-b) for a,b in zip(joint,newjoint))<1e-12
    checks.append(source+":joint_no_target_outcome_leakage")
    assert abs(sum(joint)-1)<1e-12 and abs(sum(base)-1)<1e-12
    checks.append(source+":normalized_posteriors")
try:mod["obs"]("BAD")
except ValueError:checks.append("reject_malformed_character")
else:raise AssertionError("BAD_SYMBOL_ACCEPTED")
evidence=json.loads(Path("/tmp/astra_v07/evidence_joint_mk_v07.json").read_text())
assert len(evidence["datasets"])==2
checks.append("two_real_data_benchmarks_present")
assert evidence["datasets"][0]["sha256"]=="70edf9e9ceb5959f0070911e9cf78e44ff44027043f91c89dc088353ef821c82"
checks.append("hendrickx_sha256")
assert evidence["datasets"][1]["sha256"]=="78e5cf6d2402741151950bdcb12373f86d900d27f4ef6b61b6b983987bcca311"
checks.append("baron_sha256")
print(json.dumps({"checks":len(checks),"status":"PASS","checks_executed":checks},indent=2))
