#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DT=ROOT/"reports"/"microclean-x"/"digital_twin_latest.json"
COMPOSITES=ROOT/"factory"/"microclean_x_composites.json"
LIBRARY=ROOT/"factory"/"microclean_x_experiment_library.json"
REPORT_DIR=ROOT/"reports"/"microclean-x"
PUBLIC_DIR=ROOT/"public"/"data"/"microclean-x"
STATE_DIR=ROOT/"state"/"microclean-x"

def clamp(x,lo=0.0,hi=1.0):
    return max(lo,min(hi,x))

def _sha(obj):
    return hashlib.sha256(
        json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    ).hexdigest()

def load_inputs():
    dt=json.loads(DT.read_text(encoding="utf-8"))
    composites=json.loads(COMPOSITES.read_text(encoding="utf-8"))
    library=json.loads(LIBRARY.read_text(encoding="utf-8"))
    assert dt["campaign_id"]=="MICROCLEAN-X"
    assert dt["phase"]==4
    assert dt["simulation_only"] is True
    assert dt["safe_or_field_ready_promotions"]==[]
    assert composites["campaign_id"]=="MICROCLEAN-X"
    assert library["campaign_id"]=="MICROCLEAN-X"
    assert library["phase"]==5
    assert library["policy"]["proposed_not_executed"] is True
    return dt,composites,library

def candidate_maps(dt,composites):
    shortlist={x["architecture_id"]:x for x in dt["global_shortlist"]}
    comp={x["id"]:x for x in composites["candidates"]}
    assert set(shortlist)==set(comp)
    return shortlist,comp

def std_norm(values,scale):
    if len(values)<2:
        return 0.0
    return clamp(statistics.pstdev(values)/scale)

def features(dt,composites):
    shortlist,comp=candidate_maps(dt,composites)
    rows=list(shortlist.values())
    uncertainties=[x["uncertainty"] for x in rows]
    lower=[x["lower_bound_removal_pct"] for x in rows]
    releases=[x["stress_test"]["release_risk_proxy"] for x in rows]
    recoveries=[x["stress_test"]["recovery_proxy"] for x in rows]
    durability=[x["stress_test"]["cycle10_retention_proxy"] for x in rows]

    real_matrix_gap=sum(1 for c in comp.values() if not c["metrics"].get("real_matrix_tested"))/len(comp)
    reuse_gap=sum(1 for c in comp.values() if not c["metrics"].get("reuse_cycles"))/len(comp)
    polymer_narrow_gap=sum(
        1 for c in comp.values()
        if not all(p in c["target"].lower() for p in ("ps","pet","pe"))
    )/len(comp)

    return {
        "mean_uncertainty":statistics.fmean(uncertainties),
        "removal_disagreement":std_norm(lower,15.0),
        "release_burden":statistics.fmean(releases),
        "recovery_gap":statistics.fmean([1.0-x for x in recoveries]),
        "durability_gap":statistics.fmean([1.0-x for x in durability]),
        "real_matrix_gap":real_matrix_gap,
        "reuse_gap":reuse_gap,
        "polymer_scope_gap":polymer_narrow_gap,
        "release_disagreement":std_norm(releases,0.18),
        "durability_disagreement":std_norm(durability,0.22),
        "recovery_disagreement":std_norm(recoveries,0.08)
    }

def experiment_need(exp,f):
    axis=exp["primary_axis"]
    if axis=="generalization":
        need=0.28*f["mean_uncertainty"]+0.24*f["real_matrix_gap"]+0.24*f["polymer_scope_gap"]+0.24*f["removal_disagreement"]
        discrimination=0.55*f["removal_disagreement"]+0.45*f["real_matrix_gap"]
    elif axis=="containment":
        need=0.34*f["release_burden"]+0.26*f["recovery_gap"]+0.20*f["release_disagreement"]+0.20*f["mean_uncertainty"]
        discrimination=0.65*f["release_disagreement"]+0.35*f["recovery_disagreement"]
    elif axis=="durability":
        need=0.32*f["durability_gap"]+0.28*f["reuse_gap"]+0.22*f["durability_disagreement"]+0.18*f["mean_uncertainty"]
        discrimination=0.70*f["durability_disagreement"]+0.30*f["reuse_gap"]
    elif axis=="safety":
        need=0.45*f["release_burden"]+0.25*f["release_disagreement"]+0.20*f["mean_uncertainty"]+0.10*f["real_matrix_gap"]
        discrimination=0.75*f["release_disagreement"]+0.25*f["release_burden"]
    elif axis=="operating_window":
        need=0.45*f["mean_uncertainty"]+0.25*f["removal_disagreement"]+0.15*f["release_disagreement"]+0.15*f["real_matrix_gap"]
        discrimination=0.60*f["removal_disagreement"]+0.40*f["release_disagreement"]
    elif axis=="reproducibility":
        need=0.58*f["mean_uncertainty"]+0.22*f["removal_disagreement"]+0.20*f["recovery_gap"]
        discrimination=0.50*f["mean_uncertainty"]+0.50*f["removal_disagreement"]
    else:
        raise AssertionError(f"unknown axis {axis}")
    return clamp(need),clamp(discrimination)

def scope_coverage(exp):
    return {"ALL":1.0,"TOP3":0.70,"CHAMPION":0.30}.get(exp["candidate_scope"],0.0)

def score_experiment(exp,f):
    need,discrimination=experiment_need(exp,f)
    coverage=scope_coverage(exp)
    cost=float(exp["cost_proxy"])
    raw=100.0*(0.50*need+0.30*discrimination+0.20*coverage)-12.0*cost
    return {
        "need_proxy":round(need,4),
        "discrimination_proxy":round(discrimination,4),
        "coverage_proxy":round(coverage,4),
        "cost_proxy":round(cost,4),
        "expected_information_gain_proxy":round(max(0.0,raw),3)
    }

def select_diverse(scored,n=3):
    ordered=sorted(scored,key=lambda x:(-x["selection_metrics"]["expected_information_gain_proxy"],x["id"]))
    selected=[]
    axes=set()
    for x in ordered:
        if x["primary_axis"] in axes:
            continue
        selected.append(x)
        axes.add(x["primary_axis"])
        if len(selected)>=n:
            break
    assert len(selected)==n
    return selected,ordered

def material_scope(exp,dt):
    shortlist=dt["global_shortlist"]
    if exp["candidate_scope"]=="ALL":
        return [{"id":x["architecture_id"],"architecture":x["architecture"],"doi":x["doi"]} for x in shortlist]
    if exp["candidate_scope"]=="TOP3":
        return [{"id":x["architecture_id"],"architecture":x["architecture"],"doi":x["doi"]} for x in shortlist[:3]]
    if exp["candidate_scope"]=="CHAMPION":
        x=shortlist[0]
        return [{"id":x["architecture_id"],"architecture":x["architecture"],"doi":x["doi"]}]
    raise AssertionError("unknown candidate scope")

def experiment_record(exp,metrics,dt,rank=None):
    return {
        "rank":rank,
        "id":exp["id"],
        "primary_axis":exp["primary_axis"],
        "title":exp["title"],
        "status":"PROPOSED_NOT_EXECUTED",
        "objective":exp["objective"],
        "candidate_scope":material_scope(exp,dt),
        "selection_metrics":metrics,
        "selection_semantics":"heuristic expected-information-gain proxy; not measured information gain",
        "readouts":exp["readouts"],
        "controls":exp["controls"],
        "kill_criteria":exp["kill_criteria"],
        "pre_registration_requirements":[
            "define primary endpoint before data collection",
            "define replicate count and exclusion criteria before data collection",
            "define acceptance/kill thresholds before data collection",
            "preserve raw measurements and material mass-balance data",
            "report negative and contradictory results"
        ]
    }

def build():
    dt,composites,library=load_inputs()
    f=features(dt,composites)
    scored=[]
    for exp in library["experiments"]:
        metrics=score_experiment(exp,f)
        scored.append(experiment_record(exp,metrics,dt))
    selected,ordered=select_diverse(scored,3)
    selected=[{**x,"rank":i+1} for i,x in enumerate(selected)]
    report={
        "campaign_id":"MICROCLEAN-X",
        "phase":5,
        "name":"Experiment Selector",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "status":"PASS",
        "source_digital_twin_sha256":dt["sha256"],
        "selection_policy":library["policy"],
        "uncertainty_features":{k:round(v,4) for k,v in f.items()},
        "selected_experiments":selected,
        "full_experiment_queue":ordered,
        "selected_primary_axes":[x["primary_axis"] for x in selected],
        "physical_experiments_executed":0,
        "new_measured_results":0,
        "claims":{
            "experiment_selection_is_simulation_informed":True,
            "experiments_have_been_run":False,
            "results_are_known":False,
            "safety_is_established":False
        },
        "decision_rule":"Run the selected experiments only after pre-registration; use measured outcomes to update or falsify the Digital Twin."
    }
    report["sha256"]=_sha({k:v for k,v in report.items() if k not in {"generated_at","sha256"}})
    return report

def write(report):
    for d in (REPORT_DIR,PUBLIC_DIR,STATE_DIR):
        d.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    for d in (REPORT_DIR,PUBLIC_DIR,STATE_DIR):
        (d/"experiment_selector_latest.json").write_text(payload,encoding="utf-8")

    lines=[
        "# MICROCLEAN-X Phase 5 — Experiment Selector",
        "",
        f"- Status: **{report['status']}**",
        f"- Selected experiments: **{len(report['selected_experiments'])}**",
        f"- Physical experiments executed: **{report['physical_experiments_executed']}**",
        f"- New measured results: **{report['new_measured_results']}**",
        f"- Source Digital Twin: `{report['source_digital_twin_sha256']}`",
        f"- Evidence fingerprint: `{report['sha256']}`",
        "",
        "## Three highest-value experiments",
        ""
    ]
    for x in report["selected_experiments"]:
        lines.append(
            f"{x['rank']}. **{x['title']}** — axis {x['primary_axis']} — "
            f"information-gain proxy {x['selection_metrics']['expected_information_gain_proxy']}/100"
        )
    lines += [
        "",
        "> These experiments are proposed, not executed. Their scores prioritize uncertainty reduction and must not be read as physical results.",
        ""
    ]
    (REPORT_DIR/"EXPERIMENT-SELECTOR-LATEST.md").write_text("\n".join(lines),encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--no-write",action="store_true")
    args=p.parse_args()
    report=build()
    if not args.no_write:
        write(report)
    print(json.dumps({
        "status":report["status"],
        "selected":[
            {
                "rank":x["rank"],
                "id":x["id"],
                "axis":x["primary_axis"],
                "eig_proxy":x["selection_metrics"]["expected_information_gain_proxy"]
            } for x in report["selected_experiments"]
        ],
        "physical_experiments_executed":report["physical_experiments_executed"],
        "sha256":report["sha256"]
    },ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
