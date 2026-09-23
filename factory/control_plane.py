#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, time, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
FACTORY=ROOT/"factory"
STATE=ROOT/"state"/"factory"
REPORTS=ROOT/"reports"/"factory"
PUBLIC=ROOT/"public"/"data"/"factory"
for p in [STATE,REPORTS,PUBLIC]: p.mkdir(parents=True,exist_ok=True)

sys.path.insert(0,str(FACTORY))
from program_director import create_or_update_programs
from policy_foundry import propose_variants, select_safe_variant
from human_bridge import build_human_bridges
from reasoning_engine import reason_program
from scientific_memory import update_scientific_memory

REG=json.loads((FACTORY/"brick_registry.json").read_text(encoding="utf-8"))
ACTIVE={x["id"]:x for x in REG["active"]}

def now(): return datetime.now(timezone.utc).isoformat()
def load(path,default):
    if path.exists():
        try:return json.loads(path.read_text(encoding="utf-8"))
        except Exception:return default
    return default
def save(path,obj):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

class Usage:
    def __init__(self):
        self.events=[]
    def use(self,brick,output_ref,metric,value,status="PASS"):
        assert brick in ACTIVE, f"unregistered brick {brick}"
        self.events.append({
            "brick_id":brick,"name":ACTIVE[brick]["name"],"stage":ACTIVE[brick]["stage"],
            "time":now(),"output_ref":output_ref,"metric":metric,"value":value,"status":status
        })

def compile_mission_graph(program):
    stages=["PLAN","OBSERVE","DISCOVER","VERIFY","EVALUATE","FALSIFY","TRANSLATE","EXPERIMENT","BENCHMARK","IMPROVE","MEMORY","DECIDE","OPERATE"]
    return {
        "program_id":program["id"],
        "nodes":[{"id":f"{program['id']}:{s}","stage":s,"status":"PLANNED"} for s in stages],
        "edges":[{"from":f"{program['id']}:{stages[i]}","to":f"{program['id']}:{stages[i+1]}"} for i in range(len(stages)-1)]
    }

def fuse_sources(committee):
    labs=committee.get("labs",[])
    portfolio=committee.get("portfolio",[])
    valid=[x for x in labs if x.get("status") in ("PASS","PARTIAL")]
    return {"labs":valid,"portfolio":portfolio,"valid_ratio":len(valid)/max(1,len(labs))}

def trust_gate(bundle):
    accepted=[];rejected=[]
    for c in bundle.get("portfolio",[]):
        has_taxon_proof=bool(c.get("taxon_verified"))
        if c.get("sources") and c.get("name") and has_taxon_proof:
            accepted.append(c)
        else:
            rejected.append({"candidate":c,"reason":"missing provenance/name/taxon proof"})
    return {"accepted":accepted,"rejected":rejected}

def build_evidence_ledgers(trusted):
    """Separate exploratory observations from replicated claims.
    A single paper can nominate a SCOUT observation, but cannot create a claim.
    """
    claims=[]; scouts=[]
    for c in trusted["accepted"]:
        record={
            "subject":c["name"],"sources":c.get("sources",[]),
            "mechanisms":c.get("mechanisms",[]),"labs":c.get("labs",[]),
            "genes":c.get("genes",[]),"taxon_verified":bool(c.get("taxon_verified")),
            "taxon_proofs":c.get("taxon_proofs",[]),
            "source_count":c.get("source_count",len(c.get("sources",[])))
        }
        record["pmid_sources"]=sorted({s for s in record["sources"] if str(s).startswith("PMID:")})
        record["independent_source_count"]=len(record["pmid_sources"])
        if record["independent_source_count"] >= 2:
            record["status"]="SUPPORTED"
            record["claim"]=f"{c['name']} is a replicated cross-species research candidate; this is not a human efficacy claim."
            claims.append(record)
        else:
            record["status"]="SCOUT"
            record["observation"]=f"{c['name']} is a single-source observation awaiting independent replication."
            record["replication_needed"]=max(0,2-record["independent_source_count"])
            scouts.append(record)
    return claims,scouts

def morpheus_audit(program,claim):
    flags=[]
    if len(claim.get("sources",[]))<2: flags.append("insufficient independent-source replication")
    if len(claim.get("labs",[]))<2: flags.append("single-lab dependence")
    if not claim.get("mechanisms"): flags.append("phenotype without mechanism")
    flags += ["phylogeny confound","publication bias","correlation not causation","human functional divergence"]
    return {
        "program_id":program["id"],"flags":flags,
        "kill_criteria":[
            "no reproducible phenotype",
            "no conserved mechanism",
            "human perturbation does not reproduce direction of effect",
            "unacceptable toxicity or contradictory evidence"
        ]
    }

def causal_uncertainty(claim,audit):
    uncertainty={
        "taxonomic":0.25 if len(claim.get("labs",[]))>=2 else 0.55,
        "mechanistic":0.30 if claim.get("mechanisms") else 0.75,
        "human_translation":0.70,
        "publication_bias":0.35
    }
    return {
        "association_only":True,
        "uncertainty":uncertainty,
        "counterfactual_tests":[
            "compare a close species lacking the phenotype",
            "perturb candidate mechanism and perform rescue",
            "test same mechanism in an evolutionarily distant species with similar phenotype",
            "test human orthologue/pathway in disease-relevant human cells"
        ]
    }

def apply_negative_memory(claim,negative):
    names={" ".join(x.get("subject","").lower().split()) for x in negative}
    blocked=" ".join(claim["subject"].lower().split()) in names
    return {"blocked":blocked,"reason":"negative knowledge hit" if blocked else None}

def human_translation_gate(claim,bridge_index):
    hits=bridge_index.get(claim["subject"],[])
    if hits:
        return {
            "subject":claim["subject"],
            "status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
            "bridges":hits,
            "remaining":["disease-specific human evidence","causal perturbation","toxicity check"],
            "animal_claim_not_promoted_to_human_efficacy":True
        }
    return {
        "subject":claim["subject"],
        "status":"UNVERIFIED_HUMAN_BRIDGE",
        "bridges":[],
        "required":["Ensembl-resolvable species","verified human orthologue","Open Targets target context","causal perturbation","toxicity check"],
        "animal_claim_not_promoted_to_human_efficacy":True
    }

def forge_experiment(program,claim,causal,audit):
    spec={
        "program_id":program["id"],"subject":claim["subject"],
        "hypothesis":f"A mechanism associated with {claim['subject']} may causally contribute to the target phenotype.",
        "steps":[
            "replicate phenotype under controlled conditions",
            "perturb candidate mechanism",
            "perform rescue experiment",
            "test evolutionarily close negative control",
            "test human-relevant model only after conservation check"
        ],
        "counterfactual_tests":causal["counterfactual_tests"],
        "kill_criteria":audit["kill_criteria"],
        "sources":claim.get("sources",[])
    }
    spec["sha256"]=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()
    return spec

def benchmark_cycle(metrics):
    baseline={"provenance_ratio":0.5,"falsification_depth":0.0,"cross_lab_diversity":0.1}
    return {k:round(metrics.get(k,0)-v,4) for k,v in baseline.items()}

def update_memory(cycle):
    mem=load(STATE/"long_term_memory.json",{"cycles":0,"program_events":[],"claims":{},"experiments":{}})
    mem["cycles"]+=1
    for c in cycle["claims"]:
        mem["claims"][c["subject"]]=c
    for e in cycle["experiments"]:
        mem["experiments"][e["program_id"]]=e
    mem["program_events"].append({"time":cycle["time"],"cycle_sha256":cycle["sha256"],"programs":[p["id"] for p in cycle["programs"]]})
    mem["program_events"]=mem["program_events"][-365:]
    save(STATE/"long_term_memory.json",mem)
    return mem

def telemetry_from(cycle,bundle,trusted,claims,usage):
    verified=sum(1 for x in claims if x["status"]=="SUPPORTED")
    fragile=sum(1 for x in claims if len(x.get("sources",[]))<2)/max(1,len(claims))
    scouts=cycle.get("scout_observations",[])
    labs=set()
    for c in claims: labs.update(c.get("labs",[]))
    return {
        "verified_ratio":verified/max(1,len(claims)),
        # Backward-compatible field for the existing Control Center.
        # It now measures fragility among actual claims, not among scout observations.
        "false_positive_rate":round(fragile,4),
        "fragile_claim_rate":round(fragile,4),
        "scout_count":len(scouts),
        "replication_backlog":sum(x.get("replication_needed",0) for x in scouts),
        "cross_lab_diversity":min(1.0,len(labs)/7),
        "provider_success_ratio":bundle.get("valid_ratio",0),
        "brick_observability_ratio":len({e["brick_id"] for e in usage.events})/len(ACTIVE),
        "claim_count":len(claims)
    }

def run_cycle(committee_path):
    usage=Usage()
    committee=json.loads(Path(committee_path).read_text(encoding="utf-8"))
    usage.use("omega-os","cycle_plan","planned_stages_completed",0,"RUNNING")

    programs_doc=create_or_update_programs(committee)
    programs=[p for p in programs_doc["programs"] if p["status"]=="ACTIVE"][:6]
    usage.use("research-director","state/factory/programs.json","programs_with_testable_milestones",len(programs))
    mission_graphs=[compile_mission_graph(p) for p in programs]
    usage.use("aion-nexus","mission_graphs","missions_with_no_unresolved_dependency",len(mission_graphs))

    bundle=fuse_sources(committee)
    usage.use("data-fusion","normalized_bundle","valid_artifact_ratio",round(bundle["valid_ratio"],4))
    trusted=trust_gate(bundle)
    usage.use("agentshield","trusted_bundle","rejected_untrusted_records",len(trusted["rejected"]))

    # Novel Species Hunter and Decision Engine were executed upstream; this factory consumes and records their outputs.
    usage.use("novel-species-hunter","committee.portfolio","novel_candidate_yield",len(committee.get("portfolio",[])))
    usage.use("decision-engine","committee.allocations","credits_sum_to_100",sum(x.get("research_credits",0) for x in committee.get("allocations",[])))

    claims,scouts=build_evidence_ledgers(trusted)
    prov=sum(1 for c in claims if c.get("sources"))/max(1,len(claims))
    # Human Bridge only operates on replicated SUPPORTED claims.
    human_bridge_result=build_human_bridges(claims)
    bridge_index={}
    for b in human_bridge_result.get("bridges",[]):
        bridge_index.setdefault(b["animal_species"],[]).append(b)
    usage.use("evidence-network","claim_ledger","replicated_claims_with_provenance_ratio",round(prov,4),
              "PASS" if claims else "PARTIAL")

    # DUALITY is represented by the upstream committee's mean arbiter values.
    disagreements=[abs(float(c.get("mean_arbiter",0))-float(c.get("committee_score",0))) for c in committee.get("portfolio",[])[:20]]
    usage.use("duality-x","committee.portfolio","mean_disagreement",round(sum(disagreements)/max(1,len(disagreements)),3))

    negative=load(ROOT/"state"/"negative_knowledge.json",[])
    experiments=[];audits=[];causal_plans=[];human=[];reasoning_dossiers=[]
    for p in programs:
        claim=next((c for c in claims if c["subject"]==p["title"]),None)
        if not claim: continue
        neg=apply_negative_memory(claim,negative)
        if neg["blocked"]:
            continue
        audit=morpheus_audit(p,claim);audits.append(audit)
        causal=causal_uncertainty(claim,audit);causal_plans.append(causal)
        human.append(human_translation_gate(claim,bridge_index))
        experiments.append(forge_experiment(p,claim,causal,audit))
        reasoning_dossiers.append(
            reason_program(
                p,claim,audit,causal,bridge_index.get(claim["subject"],[])
            )
        )
    usage.use("morpheus","morpheus_audits","falsifiable_failure_modes_per_program",round(sum(len(x["flags"]) for x in audits)/max(1,len(audits)),3))
    usage.use("omega-causal","causal_plans","claims_with_counterfactual_test",len(causal_plans))
    usage.use("negative-kg","negative_filter","repeated_dead_ends_prevented",max(0,len(programs)-len(experiments)))
    verified_human=sum(1 for x in human if x["status"]=="ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED")
    bridge_status=human_bridge_result.get("status","PARTIAL")
    usage.use("human-bridge","human_bridge_result","supported_claim_bridge_coverage",
              human_bridge_result.get("coverage_ratio",0),bridge_status)
    usage.use("experiment-forge","experiments","programs_with_explicit_kill_criteria",sum(1 for e in experiments if e["kill_criteria"]))

    hypothesis_count=sum(len(d.get("hypotheses",[])) for d in reasoning_dossiers)
    surviving_count=sum(len(d.get("debate",{}).get("surviving_hypothesis_ids",[])) for d in reasoning_dossiers)
    reasoning_plan_count=sum(len(d.get("experiment_plans",[])) for d in reasoning_dossiers)
    usage.use("scientific-reasoning","scientific_reasoning","reasoning_dossiers_generated",len(reasoning_dossiers),
              "PASS" if reasoning_dossiers else "PARTIAL")
    usage.use("hypothesis-engine","scientific_reasoning","falsifiable_hypotheses_generated",hypothesis_count,
              "PASS" if hypothesis_count else "PARTIAL")
    usage.use("debate-engine","scientific_reasoning","hypotheses_surviving_adversarial_review",surviving_count,
              "PASS" if reasoning_dossiers else "PARTIAL")
    usage.use("experiment-planner","scientific_reasoning","conceptual_experiment_plans_generated",reasoning_plan_count,
              "PASS" if reasoning_plan_count else "PARTIAL")

    metrics={
        "provenance_ratio":prov,
        "falsification_depth":min(1.0,sum(len(x["flags"]) for x in audits)/max(1,len(audits)*8)),
        "cross_lab_diversity":min(1.0,len({lab for c in claims for lab in c.get("labs",[])})/7)
    }
    bench=benchmark_cycle(metrics)
    usage.use("benchmark-x10","benchmark","delta_vs_baseline",round(sum(bench.values()),4))

    policy=load(STATE/"research_policy.json",{
        "exploration_rate":0.20,"minimum_sources":2,"morpheus_penalty":0.20,"novelty_weight":0.30
    })
    # Temporary telemetry prior to policy proposal.
    temp_cycle={"claims":claims,"scout_observations":scouts}
    telemetry={
        "verified_ratio":sum(1 for x in claims if x["status"]=="SUPPORTED")/max(1,len(claims)),
        "false_positive_rate":sum(1 for x in claims if len(x.get("sources",[]))<2)/max(1,len(claims)),
        "fragile_claim_rate":sum(1 for x in claims if len(x.get("sources",[]))<2)/max(1,len(claims)),
        "scout_count":len(scouts),
        "replication_backlog":sum(x.get("replication_needed",0) for x in scouts),
        "cross_lab_diversity":metrics["cross_lab_diversity"],
        "provider_success_ratio":bundle.get("valid_ratio",0)
    }
    variants=propose_variants(policy,telemetry)
    usage.use("omega-foundry","policy_variants","policy_variant_diversity",len(variants))
    gate=select_safe_variant(policy,variants,telemetry)
    if gate["accepted"]:
        save(STATE/"research_policy.json",gate["policy"])
    usage.use("immune-gate","policy_gate","unsafe_policy_changes_blocked",0 if gate["accepted"] else 1)

    cycle={
        "schema":"biomimic-v7-factory-cycle-v1","time":now(),
        "programs":programs,"mission_graphs":mission_graphs,"claims":claims,"scout_observations":scouts,
        "audits":audits,"causal_plans":causal_plans,"human_translation":human,
        "human_bridge_result":human_bridge_result,
        "experiments":experiments,"scientific_reasoning":reasoning_dossiers,
        "benchmark":bench,"policy_gate":gate
    }
    cycle["sha256"]=hashlib.sha256(json.dumps(cycle,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

    mem=update_memory(cycle)
    usage.use("omega-memory","state/factory/long_term_memory.json","new_provenance_edges",len(claims)+len(scouts)+len(experiments))
    reasoning_mem=update_scientific_memory(STATE/"scientific_reasoning_memory.json",reasoning_dossiers)
    usage.use("scientific-memory","state/factory/scientific_reasoning_memory.json","reasoning_hypotheses_retained",
              reasoning_mem.get("hypotheses",0),"PASS" if reasoning_dossiers else "PARTIAL")
    telemetry=telemetry_from(cycle,bundle,trusted,claims,usage)
    usage.use("omega-telemetry","telemetry","brick_observability_ratio",0.0)
    reliability_ratio=round(bundle.get("valid_ratio",0),4)
    usage.use("devops-x","validated_state","successful_daily_cycle_ratio",reliability_ratio,
              "PASS" if reliability_ratio==1.0 else "PARTIAL")

    # Finish Ω-OS with the number of completed stages.
    for e in usage.events:
        if e["brick_id"]=="omega-os":
            e["status"]="PASS"; e["value"]=len({x["stage"] for x in usage.events})

    used={e["brick_id"] for e in usage.events}
    unused=sorted(set(ACTIVE)-used)
    telemetry["brick_observability_ratio"]=round(len(used)/len(ACTIVE),4)
    for e in usage.events:
        if e["brick_id"]=="omega-telemetry":
            e["value"]=telemetry["brick_observability_ratio"]
            e["status"]="PASS" if telemetry["brick_observability_ratio"]==1.0 else "PARTIAL"
    cycle["brick_usage"]=usage.events
    cycle["unused_active_bricks"]=unused
    cycle["telemetry"]=telemetry
    cycle["status"]="PASS" if (not unused and reliability_ratio==1.0) else "PARTIAL"
    # Re-fingerprint after usage audit.
    cycle["sha256"]=hashlib.sha256(json.dumps(cycle,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

    save(STATE/"latest.json",cycle)
    save(STATE/"brick_usage_latest.json",usage.events)
    save(PUBLIC/"latest.json",cycle)
    save(PUBLIC/"brick_usage.json",usage.events)

    report=[
        f"# BIO-MIMIC X V7 Discovery Factory — {cycle['time']}",
        "",f"**Status:** {cycle['status']}",f"**Replay SHA-256:** `{cycle['sha256']}`","",
        "## Active programs"
    ]
    for p in programs:
        report.append(f"- {p['id']} · {p['title']} · score {p.get('committee_score',0)} · labs {', '.join(p.get('labs',[]))}")
    report += ["","## Brick utilization"]
    for e in usage.events:
        report.append(f"- {e['name']}: {e['status']} · {e['metric']}={e['value']} · output={e['output_ref']}")
    if unused:
        report += ["","## ERROR: active but unused bricks"]+[f"- {x}" for x in unused]
    report += ["","## Policy self-improvement gate",json.dumps(gate,ensure_ascii=False)]
    (REPORTS/"LATEST.md").write_text("\n".join(report),encoding="utf-8")
    return cycle

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--committee",required=True)
    a=ap.parse_args()
    x=run_cycle(a.committee)
    print(json.dumps({"status":x["status"],"programs":len(x["programs"]),"claims":len(x["claims"]),"experiments":len(x["experiments"]),"unused_active_bricks":x["unused_active_bricks"],"sha256":x["sha256"]}))
    raise SystemExit(0 if x["status"]=="PASS" else 3)
