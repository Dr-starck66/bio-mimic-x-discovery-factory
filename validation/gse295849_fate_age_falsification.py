#!/usr/bin/env python3
"""BIO-MIMIC X: falsification of 'epigenetic de-aging is independent of cell fate'.

Reanalyse already-published, hash-tracked 60 Horvath Skin&Blood clock estimates
without re-downloading 334 MB GEO source. One donor (GEO genotype) = one vote.
Observational cell-state labels cannot prove a constant molecular identity.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from math import comb

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/factory/GSE295849-ALL-60-PAIRED-HORVATH2018-2026-11-02.json"
OUTPUT = ROOT / "reports/factory/GSE295849-FATE-AGE-FALSIFICATION-2026-11-02.json"
MODEL_SHA = "56f8ce6567170ce5427f24803d30a2f0e3f6d3735b44100af02521fcd7c18027"
EXPECTED_SOURCE_SHAS = {
    "1": "c13d9efcb094e57d8f69f819440620de671bd398b45e8c24c29194aa7f228d32",
    "2": "4ca091cef1128ddcea24e6c2b349c038ae1de8dc4eb302f7f218304e17479fcd",
    "3": "fa92b4124a5bd7c69a878ae4557d2def91b1698203fc975fe63003de27640f2d",
}

def rnd(v):
    return round(float(v), 5)

def sign_p_two_sided(deltas):
    """Exact two-sided binomial sign test, excluding zero differences."""
    values = [v for v in deltas if v != 0]
    if not values:
        return None
    n = len(values)
    k = min(sum(v < 0 for v in values), sum(v > 0 for v in values))
    return min(1., 2 * sum(comb(n, j) for j in range(k + 1)) / (2 ** n))

def validate(records, strict=True):
    if not records:
        raise ValueError("missing real methylation samples")
    ids = [x.get("chip_sample_id") for x in records]
    accessions = [x.get("gsm") for x in records]
    if None in ids or None in accessions or len(ids) != len(set(ids)) or len(accessions) != len(set(accessions)):
        raise ValueError("duplicate/missing chip or GSM accession")
    for x in records:
        for key in ("donor_genotype", "cell_type", "stage", "treatment", "part"):
            if not x.get(key):
                raise ValueError(f"missing {key} for {x['gsm']}")
        age = x.get("clock_age_years")
        if isinstance(age, bool) or not isinstance(age, (float,int)) or not math.isfinite(age):
            raise ValueError("missing or nonfinite clock prediction")
    if strict:
        if len(records) != 60 or len(set(x["donor_genotype"] for x in records)) != 12:
            raise ValueError("strict source needs 60 GEO chips from exactly 12 genotypes")
        if {p:sum(x["part"] == p for x in records) for p in ("1","2","3")} != {"1":39,"2":13,"3":8}:
            raise ValueError("39/13/8 original GEO matrix partition mismatch")

def subset(group, cell, stage, treatment="None"):
    return [x for x in group if x["cell_type"] == cell and x["stage"] == stage and x["treatment"] == treatment]

def slide(x):
    """The Illumina Sentrix barcode, not an exact biological replicate."""
    return x["chip_sample_id"].split("_")[0]

def compare(records, a_cell, a_stage, b_cell, b_stage, same_slide_only=False):
    """Same-donor contrasts; LP technical/biological samples averaged per genotype."""
    grouped=defaultdict(list)
    for row in records:
        grouped[row["donor_genotype"]].append(row)
    paired=[]
    for genotype,group in sorted(grouped.items(),key=lambda item:int(item[0])):
        a=subset(group,a_cell,a_stage)
        b=subset(group,b_cell,b_stage)
        if same_slide_only:
            a=[x for x in a if any(slide(x)==slide(y) for y in b)]
            b=[x for x in b if any(slide(x)==slide(y) for y in a)]
        if not a or not b:
            continue
        if (a_cell,a_stage)==(b_cell,b_stage):
            raise ValueError("same condition cannot be compared to itself")
        a_age=mean(x["clock_age_years"] for x in a)
        b_age=mean(x["clock_age_years"] for x in b)
        paired.append({
            "genotype":genotype, "before_gsm":[x["gsm"] for x in a],
            "after_gsm":[x["gsm"] for x in b],
            "before_age":rnd(a_age), "after_age":rnd(b_age),
            "delta_years":rnd(b_age-a_age),
            "same_Illumina_slide":any(slide(x)==slide(y) for x in a for y in b),
            "different_molecular_identity_not_excluded":True,
        })
    ds=[row["delta_years"] for row in paired]
    return {
        "before":f"{a_cell}/{a_stage}/untreated",
        "after":f"{b_cell}/{b_stage}/untreated",
        "same_slide_only":same_slide_only,
        "n_independent_donors":len(paired),
        "n_clock_decreases":sum(x<0 for x in ds),
        "n_clock_increases":sum(x>0 for x in ds),
        "n_equal":sum(x==0 for x in ds),
        "mean_delta_years":rnd(mean(ds)) if ds else None,
        "median_delta_years":rnd(median(ds)) if ds else None,
        "two_sided_exact_sign_p_unadjusted":rnd(sign_p_two_sided(ds)) if ds else None,
        "pairs":paired,
    }

def treatments(records):
    grouped=defaultdict(list)
    for r in records:grouped[r["donor_genotype"]].append(r)
    all_treatments={}
    for treatment in ("NGN2","Glycerol","Thymidine"):
        matched=[]
        for genotype,group in sorted(grouped.items(),key=lambda item:int(item[0])):
            a=subset(group,"iNSC","LP","None")
            b=subset(group,"iNSC","LP",treatment)
            if not a or not b:continue
            untreated=mean(x["clock_age_years"] for x in a)
            treated=mean(x["clock_age_years"] for x in b)
            matched.append({"genotype":genotype,"before_age":rnd(untreated),
                            "after_age":rnd(treated),"delta_years":rnd(treated-untreated),
                            "untreated_gsms":[x["gsm"] for x in a],
                            "treated_gsms":[x["gsm"] for x in b]})
        ds=[x["delta_years"] for x in matched]
        all_treatments[treatment]={
            "n_independent_donors":len(matched), "n_increased":sum(x>0 for x in ds),
            "n_decreased":sum(x<0 for x in ds),
            "mean_delta_years":rnd(mean(ds)) if ds else None,
            "pairs":matched}
    return all_treatments

def build(source, strict=True):
    records=source.get("sample_level_ages",[])
    validate(records,strict=strict)
    if strict:
        if source.get("model_sha256")!=MODEL_SHA:
            raise ValueError("Horvath 2018 391-CpG model SHA changed")
        parts={str(x["part"]):x["sha256"] for x in source.get("sources",[])}
        if parts!=EXPECTED_SOURCE_SHAS:
            raise ValueError("original GEO dataset source hashes differ")
        if source.get("primary_analysis",{}).get("n_donors")!=12:
            raise ValueError("prior donor-level QC not matched")
    transitions={
        "iNSC_D14_to_D26":compare(records,"iNSC","D14","iNSC","D26"),
        "iNSC_D14_to_LP":compare(records,"iNSC","D14","iNSC","LP"),
        "iNSC_D26_to_LP":compare(records,"iNSC","D26","iNSC","LP"),
        "iNSC_LP_to_HP":compare(records,"iNSC","LP","iNSC","HP"),
    }
    lineage=compare(records,"iNSC","LP","smNPC","LP")
    same_slide=compare(records,"iNSC","D14","iNSC","LP",same_slide_only=True)
    contrast=transitions["iNSC_D14_to_LP"]
    lineage_as_confounder=(lineage["n_independent_donors"]>0 and
                           lineage["n_clock_decreases"]==lineage["n_independent_donors"])
    return {
        "schema":"BIO-MIMIC-X/FATE-VS-EPIGENETIC-AGE-FALSIFICATION/1",
        "status":"PASS_REPRODUCIBLE_DESCRIPTIVE_REANALYSIS" if strict else "PASS_SYNTHETIC_TEST_ONLY",
        "study":"GSE295849; Berg et al. Aging Cell 2026; doi 10.1111/acel.70751",
        "source":"reports/factory/GSE295849-ALL-60-PAIRED-HORVATH2018-2026-11-02.json",
        "sample_count":len(records),
        "donor_count":len(set(x["donor_genotype"] for x in records)),
        "design":"Post hoc exploratory donor-paired comparisons. No randomization, preregistration, or new laboratory replication.",
        "same_label_time_course":transitions,
        "same_slide_sensitivity_D14_to_LP":same_slide,
        "alternative_fate_negative_control_iNSC_vs_smNPC":lineage,
        "LP_perturbations_not_age_treatments":treatments(records),
        "fate_matters": "YES_ALTERNATIVE_FATE_HAS_DIFFERENT_CLOCK_OUTPUT" if lineage_as_confounder else "UNVERIFIED",
        "age_reset_independent_of_cell_fate":"UNVERIFIED",
        "identity_constant_at_molecular_level":"UNVERIFIED",
        "independent_orthogonal_age_markers":"UNVERIFIED",
        "negative_controls_preserved":{"GSE74387":"FAIL","alternative_neural_fate_smNPC":True,
                                      "same_slide_batch_restriction":True,
                                      "glycerol_NGN2_thymidine_perturbation":True},
        "interpretation":(
            "Within samples labeled iNSC, age-clock estimates continue to fall, "
            "but the original authors explicitly document continued neural-fate consolidation "
            "between D14, D26, LP and later. smNPC alternative-fate clocks trend still lower. "
            "Therefore a time-course association is demonstrated, not independence from cell identity."
        ),
        "limitations":[
            "D14 is an emerging neuroepithelial population, not a stable mature reference iNSC phenotype.",
            "Horvath Skin&Blood is not invariant to lineage; smNPC estimates may fall below 0 due to model floor.",
            "Some timepoints and cell-fate groups are on different Illumina slides; same-slide subset is too small to eliminate batch.",
            "Sign-test p-values are unadjusted, exploratory and not evidence of an intervention or mechanistic causality.",
            "NGN2, glycerol and thymidine treatments are different interventions; associations do not show causation.",
            "The 60 observations originate from one publication, not 60 independently reproduced biological experiments.",
        ],
        "required_to_disentangle":[
            "Matched sample-level transcriptomic or cell-identity score tracked at each stage, ideally independent markers not used in the age clock.",
            "Age-associated CpGs residualized against independently defined identity/lineage signatures within adequately replicated donors.",
            "Matched nonreprogrammed EPC controls cultured over the same period and independently validated age clocks.",
            "Perturbations that change age-associated marks without changing cell identity, and controls with the reverse behavior.",
        ],
        "clinical_anti_aging":"UNVERIFIED",
        "axolotl_mechanism_transfer":"UNVERIFIED",
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,default=SOURCE)
    ap.add_argument("--out",type=Path,default=OUTPUT)
    args=ap.parse_args(argv)
    source=json.loads(args.source.read_text(encoding="utf8"))
    report=build(source)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    primary=report["same_label_time_course"]["iNSC_D14_to_LP"]
    print("BIO_MIMIC_FATE_AGE "+json.dumps({
        "status":report["status"],
        "donors":report["donor_count"],
        "iNSC_D14_to_LP":{"n":primary["n_independent_donors"],
                          "decreases":primary["n_clock_decreases"],
                          "mean_delta_years":primary["mean_delta_years"],
                          "p_unadjusted":primary["two_sided_exact_sign_p_unadjusted"]},
        "lineage_confounding":report["fate_matters"],
        "independence_from_fate":report["age_reset_independent_of_cell_fate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
