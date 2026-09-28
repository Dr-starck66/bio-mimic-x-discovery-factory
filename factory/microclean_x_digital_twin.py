#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COMPOSITES=ROOT/"factory"/"microclean_x_composites.json"
ASSUMPTIONS=ROOT/"factory"/"microclean_x_digital_twin_assumptions.json"
REPORT_DIR=ROOT/"reports"/"microclean-x"
PUBLIC_DIR=ROOT/"public"/"data"/"microclean-x"
STATE_DIR=ROOT/"state"/"microclean-x"

BASES=(2,3,5,7,11,13)

def clamp(x,lo=0.0,hi=1.0):
    return max(lo,min(hi,x))

def sha(obj):
    return hashlib.sha256(
        json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    ).hexdigest()

def halton(index, base):
    f=1.0
    r=0.0
    i=index
    while i>0:
        f/=base
        r+=f*(i%base)
        i//=base
    return r

def scale(u, bounds):
    lo,hi=bounds
    return lo+(hi-lo)*u

def load_inputs():
    comp=json.loads(COMPOSITES.read_text(encoding="utf-8"))
    assumptions=json.loads(ASSUMPTIONS.read_text(encoding="utf-8"))
    assert comp["campaign_id"]=="MICROCLEAN-X"
    assert assumptions["campaign_id"]=="MICROCLEAN-X"
    assert assumptions["simulation_only"] is True
    ids={c["id"] for c in comp["candidates"]}
    assert ids==set(assumptions["architecture_priors"])
    return comp,assumptions

def reuse_proxy(c):
    m=c["metrics"]
    base=float(m["max_removal_pct"])
    cycles=m.get("reuse_cycles")
    retained=m.get("retained_removal_pct_after_reuse")
    if cycles and retained is not None and cycles>1:
        ratio=clamp(float(retained)/max(base,1e-9),0.05,1.05)
        exponent=9.0/max(1.0,float(cycles)-1.0)
        return clamp(ratio**exponent,0.0,1.0),0.08
    # Missing durability evidence is not silently treated as good performance.
    return 0.55,0.20

def predict(c,prior,p):
    m=c["metrics"]
    base=float(m["max_removal_pct"])
    dose=p["dose_ratio"]
    contact=p["contact_time_ratio"]
    magnetic=p["magnetic_fraction_ratio"]
    affinity=p["surface_affinity_ratio"]
    ph=abs(p["pH_offset_from_reference"])
    matrix=p["matrix_complexity"]

    # Saturating, dimensionless perturbations around the published baseline.
    dose_factor=1.0+0.10*math.tanh(2.0*(dose-1.0))
    contact_factor=1.0+0.09*math.tanh(2.0*(contact-1.0))
    affinity_factor=1.0+0.14*(affinity-1.0)
    magnetic_surface_tradeoff=1.0-0.07*abs(magnetic-1.0)
    ph_factor=1.0-float(prior["pH_sensitivity"])*0.10*ph

    if m.get("real_matrix_tested"):
        matrix_factor=1.0-0.10*matrix
        matrix_uncertainty=0.04
    else:
        matrix_factor=1.0-0.22*matrix
        matrix_uncertainty=0.10

    predicted=base*dose_factor*contact_factor*affinity_factor*magnetic_surface_tradeoff*ph_factor*matrix_factor
    predicted=clamp(predicted,0.0,100.0)

    mag_baseline=0.88
    if m.get("magnetization_emu_g"):
        mag_baseline=clamp(0.72+float(m["magnetization_emu_g"])/300.0,0.75,0.96)
    recovery=clamp(mag_baseline+0.18*(magnetic-1.0)-0.04*matrix,0.55,0.995)

    cycle10, reuse_uncertainty=reuse_proxy(c)
    cycle10=clamp(cycle10*(1.0-0.08*max(0.0,matrix-0.5))*(1.0-0.05*abs(affinity-1.0)),0.0,1.0)

    release=float(prior["release_risk_prior"])
    release += 0.10*max(0.0,magnetic-1.0)
    release += 0.06*matrix
    release += float(prior["pH_sensitivity"])*0.12*ph
    release += 0.04*max(0.0,affinity-1.0)
    release=clamp(release)

    distance=sum([
        abs(dose-1.0)/0.4,
        abs(contact-1.0)/0.5,
        abs(magnetic-1.0)/0.25,
        abs(affinity-1.0)/0.2,
        ph/2.0,
        matrix,
    ])/6.0

    uncertainty=0.10+matrix_uncertainty+reuse_uncertainty+0.10*distance
    if c["id"]=="fe3o4_mil101cr":
        uncertainty+=0.03
    uncertainty=clamp(uncertainty,0.12,0.45)

    lower_removal=clamp(predicted*(1.0-uncertainty),0.0,100.0)
    stressed_recovery=clamp(recovery-0.08-0.06*matrix,0.0,1.0)
    stressed_cycle10=clamp(cycle10*(1.0-0.12*matrix),0.0,1.0)
    stressed_release=clamp(release+0.12+0.08*matrix,0.0,1.0)

    complexity=float(prior["complexity_prior"])
    robust=(
        0.45*lower_removal
        +25.0*stressed_recovery
        +15.0*stressed_cycle10
        -20.0*stressed_release
        -10.0*complexity
    )
    robust=round(clamp(robust,0.0,100.0),3)

    return {
        **p,
        "predicted_removal_pct":round(predicted,3),
        "lower_bound_removal_pct":round(lower_removal,3),
        "magnetic_recovery_proxy":round(recovery,4),
        "cycle10_retention_proxy":round(cycle10,4),
        "release_risk_proxy":round(release,4),
        "uncertainty":round(uncertainty,4),
        "complexity_proxy":round(complexity,4),
        "stress_test":{
            "recovery_proxy":round(stressed_recovery,4),
            "cycle10_retention_proxy":round(stressed_cycle10,4),
            "release_risk_proxy":round(stressed_release,4)
        },
        "robust_score":robust,
        "status":"SIMULATION_ONLY"
    }

def sample_variants(candidate,prior,space,n):
    keys=list(space)
    out=[]
    for idx in range(1,n+1):
        u=[halton(idx,BASES[i]) for i in range(len(keys))]
        p={k:scale(u[i],space[k]) for i,k in enumerate(keys)}
        out.append(predict(candidate,prior,p))
    return out

def dominates(a,b):
    # Maximise removal/recovery/durability; minimise release/complexity.
    va=(
        a["lower_bound_removal_pct"],
        a["stress_test"]["recovery_proxy"],
        a["stress_test"]["cycle10_retention_proxy"],
        -a["stress_test"]["release_risk_proxy"],
        -a["complexity_proxy"],
    )
    vb=(
        b["lower_bound_removal_pct"],
        b["stress_test"]["recovery_proxy"],
        b["stress_test"]["cycle10_retention_proxy"],
        -b["stress_test"]["release_risk_proxy"],
        -b["complexity_proxy"],
    )
    return all(x>=y for x,y in zip(va,vb)) and any(x>y for x,y in zip(va,vb))

def pareto_front(items):
    front=[]
    for i,a in enumerate(items):
        if not any(i!=j and dominates(b,a) for j,b in enumerate(items)):
            front.append(a)
    return sorted(front,key=lambda x:(-x["robust_score"],-x["lower_bound_removal_pct"]))

def variant_record(candidate,v,rank=None):
    return {
        "architecture_id":candidate["id"],
        "architecture":candidate["architecture"],
        "doi":candidate.get("doi"),
        "rank":rank,
        **v
    }

def baseline_calibration(candidate,prior):
    p={
        "dose_ratio":1.0,
        "contact_time_ratio":1.0,
        "magnetic_fraction_ratio":1.0,
        "surface_affinity_ratio":1.0,
        "pH_offset_from_reference":0.0,
        "matrix_complexity":0.0
    }
    pred=predict(candidate,prior,p)
    observed=float(candidate["metrics"]["max_removal_pct"])
    err=abs(pred["predicted_removal_pct"]-observed)
    return {
        "architecture_id":candidate["id"],
        "observed_anchor_pct":observed,
        "surrogate_baseline_pct":pred["predicted_removal_pct"],
        "absolute_error_pct_points":round(err,3),
        "pass":err<=1.0
    }

def run(n_per_architecture=5000):
    comp,assumptions=load_inputs()
    space=assumptions["parameter_space"]
    all_top=[]
    per_arch=[]
    calibration=[]

    for c in comp["candidates"]:
        prior=assumptions["architecture_priors"][c["id"]]
        calibration.append(baseline_calibration(c,prior))
        variants=sample_variants(c,prior,space,n_per_architecture)
        variants.sort(key=lambda x:(-x["robust_score"],-x["lower_bound_removal_pct"]))
        best=variants[:50]
        per_arch.append({
            "architecture_id":c["id"],
            "architecture":c["architecture"],
            "doi":c.get("doi"),
            "simulated_variants":n_per_architecture,
            "best_virtual_variant":variant_record(c,best[0],1),
            "top5":[variant_record(c,v,i+1) for i,v in enumerate(best[:5])]
        })
        all_top.extend(variant_record(c,v) for v in best)

    # Pareto is computed on the robust prefiltered set (250 variants),
    # while all 25,000 variants are evaluated before that prefilter.
    pareto=pareto_front(all_top)
    global_sorted=sorted(all_top,key=lambda x:(-x["robust_score"],-x["lower_bound_removal_pct"]))
    shortlist=[]
    seen=set()
    for v in global_sorted:
        if v["architecture_id"] in seen:
            continue
        shortlist.append(v)
        seen.add(v["architecture_id"])
        if len(shortlist)>=5:
            break

    report={
        "campaign_id":"MICROCLEAN-X",
        "phase":4,
        "name":"Digital Twin",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "status":"PASS" if all(x["pass"] for x in calibration) else "PARTIAL",
        "model_class":assumptions["model_class"],
        "simulation_only":True,
        "total_variants_simulated":n_per_architecture*len(comp["candidates"]),
        "variants_per_architecture":n_per_architecture,
        "parameter_space":space,
        "baseline_calibration":calibration,
        "per_architecture":per_arch,
        "global_shortlist":shortlist,
        "pareto_frontier_prefiltered":pareto[:25],
        "pareto_method":"non-dominated frontier across the top 50 robust variants per architecture after all variants were simulated",
        "safe_or_field_ready_promotions":[],
        "claims":{
            "physical_validation":False,
            "measured_new_data":False,
            "simulation_can_replace_experiment":False
        },
        "next_gate":{
            "status":"PROPOSED_NOT_EXECUTED",
            "requirement":"Only physical or independently measured evidence can move a virtual variant beyond simulation status.",
            "minimum_tests":[
                "identical-condition head-to-head against published architecture",
                "PS/PET/PE challenge",
                "magnetic mass-balance recovery",
                "particle/metal/coating release",
                "ten-cycle durability",
                "real-water or wastewater matrix",
                "matched ecotoxicity controls"
            ]
        }
    }
    report["sha256"]=sha({k:v for k,v in report.items() if k not in {"generated_at","sha256"}})
    return report

def write(report):
    for d in (REPORT_DIR,PUBLIC_DIR,STATE_DIR):
        d.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    for d in (REPORT_DIR,PUBLIC_DIR,STATE_DIR):
        (d/"digital_twin_latest.json").write_text(payload,encoding="utf-8")

    lines=[
        "# MICROCLEAN-X Phase 4 — Digital Twin",
        "",
        f"- Status: **{report['status']}**",
        f"- Model: **{report['model_class']}**",
        f"- Simulated variants: **{report['total_variants_simulated']:,}**",
        f"- Architectures: **{len(report['per_architecture'])}**",
        f"- Physical validations created: **0**",
        f"- Safe/field-ready promotions: **{len(report['safe_or_field_ready_promotions'])}**",
        f"- Evidence fingerprint: `{report['sha256']}`",
        "",
        "## Best virtual variant per architecture",
        ""
    ]
    for i,v in enumerate(report["global_shortlist"],1):
        lines.append(
            f"{i}. **{v['architecture']}** — robust {v['robust_score']}/100 — "
            f"lower-bound removal {v['lower_bound_removal_pct']}% — "
            f"stress recovery {v['stress_test']['recovery_proxy']:.3f} — "
            f"stress release-risk {v['stress_test']['release_risk_proxy']:.3f}"
        )
    lines += [
        "",
        f"Pareto frontier (prefiltered): **{len(report['pareto_frontier_prefiltered'])} variants shown**.",
        "",
        "> These are simulation-only research candidates. The surrogate is anchored to published results but does not create new empirical evidence.",
        ""
    ]
    (REPORT_DIR/"DIGITAL-TWIN-LATEST.md").write_text("\n".join(lines),encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--variants-per-architecture",type=int,default=5000)
    p.add_argument("--no-write",action="store_true")
    args=p.parse_args()
    if args.variants_per_architecture<100:
        raise SystemExit("variants-per-architecture must be >=100")
    report=run(args.variants_per_architecture)
    if not args.no_write:
        write(report)
    print(json.dumps({
        "status":report["status"],
        "total_variants_simulated":report["total_variants_simulated"],
        "shortlist":[{"architecture":x["architecture"],"robust_score":x["robust_score"]} for x in report["global_shortlist"]],
        "pareto_count":len(report["pareto_frontier_prefiltered"]),
        "sha256":report["sha256"]
    },ensure_ascii=False))
    return 0 if report["status"]=="PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
