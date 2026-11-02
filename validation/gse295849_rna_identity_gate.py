#!/usr/bin/env python3
"""BIO-MIMIC X: honest cross-assay age-vs-cell-identity gate.

PUBLIC data: RNA SRA titles, donor pseudonyms, sample stage, access flags,
60 public GEO DNAm Horvath clock estimates. Raw RNA-seq reads / feature counts
for phs004047.v1.p1 are CONTROLLED-ACCESS, not public.

When independent authorized local RNA counts later exist, compute a predeclared
RNA marker identity score, then donor-level D14->LP contrast residuals.
Never infer RNA expression from stage labels, manuscript figures, or SRR names.
Never upload donor-level restricted counts or matrices to a public GitHub repo.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
METH = ROOT / "reports/factory/GSE295849-ALL-60-PAIRED-HORVATH2018-2026-11-02.json"
RNA = ROOT / "reports/factory/GSE295849-SRP594303-RNA-METADATA-2026-11-02.json"
OUTPUT = ROOT / "reports/factory/GSE295849-RNA-IDENTITY-ADJUSTMENT-LATEST.json"

# Independent assay genes, fixed in advance, NOT selected by DNAm clock changes.
# Initial candidate panel only, not a validated diagnostic identity classifier.
NEURAL = ("PAX6", "DACH1", "NES", "SOX2", "SOX1", "HES5")
ERYTHROID = ("GATA1", "KLF1", "HBB", "ALAS2", "EPOR", "GYPA")
ALL_MARKERS = NEURAL + ERYTHROID

def structural_gate(methylation: dict, rna_meta: dict) -> dict:
    ages = methylation["sample_level_ages"]
    rna = rna_meta["rna_samples"]
    if len(ages) != 60 or len({x["gsm"] for x in ages}) != 60:
        raise ValueError("public DNAm age evidence must contain 60 unique GEO GSM samples")
    if len(rna) != 48 or len({x["rna_experiment"] for x in rna}) != 48 or len({x["rna_run"] for x in rna}) != 48:
        raise ValueError("public RNA run metadata must contain exactly 48 unique experiments")
    if any(x["rna_data_access"] != "DBGAP_AUTHORIZED_ACCESS_ONLY" for x in rna):
        raise ValueError("unexpected public RNA access status: re-audit before processing")
    by_gsm = {x["gsm"]:x for x in ages}
    stage_links = []
    for x in rna:
        condition = (x["donor_genotype_from_public_SRA_title"], x["cell_type"], x["harvest_stage"])
        matched = x["matched_DNAm_GSMs"]
        if len(matched) != len(set(matched)):
            raise ValueError("duplicate GEO GSM among RNA condition candidates")
        expected = {m["gsm"] for m in ages if
                    (m["donor_genotype"], m["cell_type"], m["stage"]) == condition
                    and m["treatment"] == "None"}
        if set(matched) != expected:
            raise ValueError("SRA public title to DNAm condition crosswalk mismatch: "+x["rna_experiment"])
        stage_links.append({
            "sra_experiment":x["rna_experiment"], "sra_run":x["rna_run"],
            "donor_genotype":condition[0], "cell_type":condition[1], "stage":condition[2],
            "methylation_gsms":matched, "condition_level_match":bool(matched),
            "physical_aliquot_verified":False, "RNA_treatment_verified":False
        })
    donors = {}
    for x in stage_links:
        if not x["condition_level_match"] or x["cell_type"]!="iNSC":
            continue
        donors.setdefault(x["donor_genotype"],{}).setdefault(x["stage"],[]).append(x)
    eligible = [genotype for genotype,stage in sorted(donors.items(),key=lambda p:int(p[0]))
                if len(stage.get("D14",[]))==1 and len(stage.get("LP",[]))==1]
    return {
        "metadata_status":"PASS_PUBLIC_CONDITION_CROSSWALK_ONLY",
        "rnaseq_run_count":len(rna),
        "rnaseq_controlled_access_count":sum(x["rna_data_access"]=="DBGAP_AUTHORIZED_ACCESS_ONLY" for x in rna),
        "DNAm_Clock_sample_count":len(ages),
        "condition_matched_RNA_runs":sum(bool(x["methylation_gsms"]) for x in stage_links),
        "independent_donors_with_RNA_D14_and_LP_condition_metadata":len(eligible),
        "D14_LP_paired_donor_genotypes":eligible,
        "RNA_to_DNAm_accession_links":stage_links,
        "no_same_biological_aliquot_claim":True,
        "RNA_treatment_status":"UNVERIFIED",
        "RNA_expression_status":"RESTRICTED_NO_COUNTS_AVAILABLE",
        "RNA_identity_score_status":"UNVERIFIED",
        "age_effect_after_identity_adjustment":"UNVERIFIED",
        "reason":"SRA experiments are public metadata; 48 read paths are @dbgap@; no approved sample-level RNA count matrix is present.",
        "negative_controls":{"GSE74387":"FAIL_RETAINED",
                             "cell_fate_confounding":"NOT_EXCLUDED",
                             "stage_labels_are_not_expression_measurements":True}
    }

def read_count_matrix(path: Path, needed_runs, *, min_genes=1000, max_bytes=200_000_000):
    """Secure LOCAL ONLY; all genes required for meaningful library-size CPM."""
    if path.stat().st_size > max_bytes:
        raise ValueError("count table exceeds local memory/size budget")
    expected = set(needed_runs)
    counts = {}
    gene_count=0
    library = {run:0 for run in expected}
    with path.open("rt",encoding="utf-8-sig",newline="") as handle:
        reader = csv.reader(handle,delimiter="\t")
        columns=next(reader,None)
        if (not columns or columns[0]!="gene_symbol" or
                len(columns)!=len(set(columns)) or not expected.issubset(set(columns[1:]))):
            raise ValueError("header must contain unique gene_symbol and RNA run IDs")
        positions=[columns.index(run) for run in needed_runs]
        for row in reader:
            if not row:continue
            if len(row)!=len(columns):
                raise ValueError("invalid RNA gene count row width")
            symbol=row[0].strip()
            if not symbol or symbol in counts:
                raise ValueError("missing or duplicate RNA gene symbol")
            vals=[]
            for idx in positions:
                v=row[idx].strip()
                if not v.isdecimal():
                    raise ValueError("raw RNA counts must be nonnegative integers, not imputed/TPM")
                n=int(v)
                vals.append(n)
            for r,n in zip(needed_runs,vals):
                library[r]+=n
            counts[symbol]=vals
            gene_count+=1
    if gene_count < min_genes or any(library[r]<1000 for r in needed_runs):
        raise ValueError("insufficient full-transcriptome genes or RNA library size")
    if not all(g in counts for g in ALL_MARKERS):
        raise ValueError("predeclared neural/erythroid identity genes missing, cannot impute")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    return {"counts":counts,"library_sizes":library,"rna_run_order":needed_runs,
            "n_genes":gene_count,"source_sha256":digest}

def identity_scores(count_table):
    """Gene-wise standardized log2 CPM (RNA only, age-blind)."""
    from math import log2
    runs=count_table["rna_run_order"]
    libraries=count_table["library_sizes"]
    matrix=count_table["counts"]
    norm={}
    for gene in ALL_MARKERS:
        values=[log2(1 + matrix[gene][i]/libraries[run]*1_000_000)
                for i,run in enumerate(runs)]
        m=mean(values)
        sd=math.sqrt(mean((v-m)**2 for v in values))
        if sd<1e-8:
            raise ValueError("constant identity marker; RNA identity panel is not discriminative: "+gene)
        norm[gene]=[(v-m)/sd for v in values]
    return {run:sum(norm[g][i] for g in NEURAL)/len(NEURAL) -
                sum(norm[g][i] for g in ERYTHROID)/len(ERYTHROID)
            for i,run in enumerate(runs)}

def conditioned_age_delta(methylation, metadata, scores):
    """Exploratory donor paired stage effect after a fixed RNA identity score.

    An extrapolated intercept is not a cell-fate-independent causal effect.
    """
    samples=methylation["sample_level_ages"]
    rna=metadata["rna_samples"]
    by_donor={}
    for x in rna:
        if x["cell_type"]=="iNSC" and x["harvest_stage"] in ("D14","LP") and x["matched_DNAm_GSMs"]:
            by_donor.setdefault(x["donor_genotype_from_public_SRA_title"],{}).setdefault(x["harvest_stage"],[]).append(x)
    primary=[]
    for donor,groups in sorted(by_donor.items(),key=lambda a:int(a[0])):
        if len(groups.get("D14",[]))!=1 or len(groups.get("LP",[]))!=1:
            continue
        before,after=groups["D14"][0],groups["LP"][0]
        if before["rna_run"] not in scores or after["rna_run"] not in scores:
            continue
        b_age=[x["clock_age_years"] for x in samples if x["gsm"] in before["matched_DNAm_GSMs"]]
        a_age=[x["clock_age_years"] for x in samples if x["gsm"] in after["matched_DNAm_GSMs"]]
        if not b_age or not a_age:
            raise ValueError("DNAm methylation age missing at matched donor condition")
        primary.append({"donor_genotype":donor,"delta_age_clock_years":mean(a_age)-mean(b_age),
                        "delta_RNA_identity_score":scores[after["rna_run"]]-scores[before["rna_run"]],
                        "rna_runs":[before["rna_run"],after["rna_run"]],
                        "same_physical_aliquot_verified":False})
    if len(primary)<5:
        raise ValueError("not enough independent donors with paired RNA expression and DNAm age (n<5)")
    xx=[x["delta_RNA_identity_score"] for x in primary]
    yy=[x["delta_age_clock_years"] for x in primary]
    mean_x,mean_y=mean(xx),mean(yy)
    ssx=sum((x-mean_x)**2 for x in xx)
    if ssx<1e-8:
        raise ValueError("identity score contrasts are collinear/constant; adjustment unidentifiable")
    beta=sum((x-mean_x)*(y-mean_y) for x,y in zip(xx,yy))/ssx
    intercept=mean_y-beta*mean_x
    residuals=[y-(intercept+beta*x) for x,y in zip(xx,yy)]
    residual_sd=math.sqrt(sum(v*v for v in residuals)/(len(primary)-2))
    support_for_identity_constant = min(xx) <= 0 <= max(xx)
    return {
        "status":"PASS_EXPLORATORY_ORTHOGONAL_RNA_ASSOCIATION_ONLY",
        "donor_pairs":len(primary),"pairs":primary,
        "observed_mean_age_delta_years":round(mean_y,5),
        "observed_mean_identity_delta":round(mean_x,5),
        "slope_age_per_identity_unit":round(beta,5),
        "identity_constant_intercept_age_delta":round(intercept,5),
        "fit_residual_sd_years":round(residual_sd,5),
        "zero_identity_change_within_observed_support":support_for_identity_constant,
        "identity_constant_effect_interpretation":(
            "DESCRIPTIVE_ONLY_NOT_CAUSAL" if support_for_identity_constant
            else "UNVERIFIED_EXTRAPOLATED_OUTSIDE_IDENTITY_SUPPORT"),
        "age_reset_independent_of_cell_fate":"UNVERIFIED",
        "limitations":[
            "RNA and DNAm matched by public pseudonymous donor/stage labels, not the same physical aliquot.",
            "RNA treatments and batch effects are not independently documented.",
            "Linear adjustment extrapolates if no independent samples with near-zero identity change.",
            "n donors small; RNA markers are a predeclared candidate panel, not externally calibrated classifier.",
            "Clock outcomes and cell identity progression may be causally entangled; statistical adjustment is not mechanistic proof.",
        ],
    }

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--rna-counts",type=Path,default=None,help="Restricted counts only in an authorized PRIVATE/LOCAL environment.")
    p.add_argument("--local-authorized",action="store_true",help="Operator attests to lawful approved dbGaP processing.")
    p.add_argument("--meth-report",type=Path,default=METH)
    p.add_argument("--rna-metadata",type=Path,default=RNA)
    p.add_argument("--out",type=Path,default=OUTPUT)
    args=p.parse_args(argv)
    methyl=json.loads(args.meth_report.read_text(encoding="utf-8"))
    meta=json.loads(args.rna_metadata.read_text(encoding="utf-8"))
    report={"schema":"BIO-MIMIC-X/ORTHOGONAL-RNA-IDENTITY-GATE/1",
            "status":"PARTIAL_NO_AUTHORIZED_TRANSCRIPTOME",
            "provenance":{"rna_study":"SRP594303","dbgap":"phs004047.v1.p1","dnAm_series":"GSE295849"},
            "public_metadata":structural_gate(methyl,meta),
            "raw_data_exported":False,"clinical_age_rejuvenation":"UNVERIFIED"}
    if args.rna_counts is not None:
        if not args.local_authorized or os.getenv("GITHUB_ACTIONS")=="true":
            raise PermissionError("Controlled-access RNA counts may be analyzed only in an authorized private execution environment; never in public GitHub Actions.")
        eligible=report["public_metadata"]["D14_LP_paired_donor_genotypes"]
        matched=[x for x in meta["rna_samples"]
                 if x["donor_genotype_from_public_SRA_title"] in eligible and
                 x["cell_type"]=="iNSC" and x["harvest_stage"] in ("D14","LP")]
        needed=[x["rna_run"] for x in matched]
        table=read_count_matrix(args.rna_counts,needed)
        score=identity_scores(table)
        result=conditioned_age_delta(methyl,meta,score)
        report["status"]="PARTIAL_ORTHOGONAL_ASSOCIATION_NOT_CAUSAL"
        report["RNA_counts_sha256"]=table["source_sha256"]
        report["samplewise_identity_source"]="Independently measured RNA-seq counts, predeclared 12-gene panel."
        report["identity_adjusted_result"]=result
        # ONLY high-level output, DO NOT save per-sample counts or identity scores.
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("BIO_MIMIC_RNA_IDENTITY_GATE "+json.dumps({
        "status":report["status"],
        "rna_experiments":report["public_metadata"]["rnaseq_run_count"],
        "matched_conditions":report["public_metadata"]["condition_matched_RNA_runs"],
        "within_iNSC_donor_pairs":report["public_metadata"]["independent_donors_with_RNA_D14_and_LP_condition_metadata"],
        "molecular_identity_score":report["public_metadata"]["RNA_identity_score_status"] if args.rna_counts is None else "EXPLORATORY_RNA_ASSOCIATION",
        "mechanistic_age_reset_independent_of_fate":"UNVERIFIED",
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
