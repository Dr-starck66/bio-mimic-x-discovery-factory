#!/usr/bin/env python3
"""Institution-side BIO-MIMIC X RNA age-vs-cell-identity analysis (no data export).

This module wraps the EXISTING GSE295849 RNA identity gate. This code is
PUBLIC; restricted RNA values are not. A bona-fide dbGaP/institution-authorized
researcher must run it entirely inside their approved security boundary.
It refuses to release any report without a separately approved disclosure.
CLI declarations are NOT themselves proof of approval; institutional review
must verify the agreement and proposed aggregate before execution/release.
"""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
from validation.gse295849_rna_identity_gate import (
    ROOT, METH, RNA, structural_gate, read_count_matrix,
    identity_scores, conditioned_age_delta,
)

EXPECTED_DONORS = ("190", "216", "218", "286", "287", "288")
EXPECTED_RUNS = (
    "SRR34149245", "SRR34149253", "SRR34149282", "SRR34149276",
    "SRR34149268", "SRR34149289", "SRR34149280", "SRR34149287",
    "SRR34149266", "SRR34149274", "SRR34149251", "SRR34149261",
)
FIXED_RELEASE_KEYS = (
    "donor_pairs", "observed_mean_age_delta_years",
    "observed_mean_identity_delta", "slope_age_per_identity_unit",
    "identity_constant_intercept_age_delta", "fit_residual_sd_years",
    "zero_identity_change_within_observed_support",
    "identity_constant_effect_interpretation",
)

def ensure_private_runtime(counts_path: Path, output_path: Path,
                           authorized_processing: bool,
                           release_approved: bool,
                           authorization_ref: str,
                           release_ref: str):
    """Fail before opening any restricted RNA file."""
    if not authorized_processing or not release_approved:
        raise PermissionError("Independent institution/DAC processing authorization AND approval to release these aggregate statistics are required")
    if len(authorization_ref.strip()) < 8 or len(release_ref.strip()) < 8:
        raise PermissionError("Institutional processing and aggregate-release reference identifiers are required")
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true" or os.environ.get("CI", "").lower() == "true":
        raise PermissionError("Never run controlled-access data analysis on CI/GitHub Actions")
    repo = ROOT.resolve()
    counts = counts_path.resolve()
    out = output_path.resolve()
    if counts == out:
        raise ValueError("RNA input and aggregate output must be separate files")
    if counts == repo or counts.is_relative_to(repo):
        raise PermissionError("Restricted RNA input may not be stored in the public repository")
    if out == repo or out.is_relative_to(repo):
        raise PermissionError("Restricted-derived output may not be written inside the repository")
    if out.suffix.lower() != ".json":
        raise ValueError("Approved aggregate must be written as a JSON report outside the repository")
    if out.exists():
        raise FileExistsError("Refusing to overwrite an existing approved report")
    if not counts.is_file():
        raise FileNotFoundError("Institutional restricted input file not found")

def condition_and_run_gate(meth: dict, meta: dict):
    public = structural_gate(meth, meta)
    if tuple(public["D14_LP_paired_donor_genotypes"]) != EXPECTED_DONORS:
        raise ValueError("The six registered donors changed: abort before accessing restricted RNA")
    matched = [x for x in meta["rna_samples"]
               if x["donor_genotype_from_public_SRA_title"] in EXPECTED_DONORS
               and x["cell_type"] == "iNSC" and x["harvest_stage"] in ("D14", "LP")]
    mapping = {(x["donor_genotype_from_public_SRA_title"], x["harvest_stage"]): x["rna_run"]
               for x in matched}
    if len(matched) != 12 or len(mapping) != 12:
        raise ValueError("Need exactly 12 unique donor-stage profiles")
    ordered = [mapping[(donor,stage)] for donor in EXPECTED_DONORS for stage in ("D14","LP")]
    if tuple(ordered) != EXPECTED_RUNS:
        raise ValueError("Unexpected 12-run public crosswalk: abort")
    return ordered

def release_safe_aggregate(result: dict):
    """Whitelist ONLY 8 aggregate numeric fields. No pseudonym, SRR or sample scores."""
    if result.get("status") != "PASS_EXPLORATORY_ORTHOGONAL_RNA_ASSOCIATION_ONLY":
        raise ValueError("No valid independent RNA analysis")
    if result.get("donor_pairs") != len(EXPECTED_DONORS) or len(result.get("pairs", [])) != 6:
        raise ValueError("Require six complete donor pairs before summarizing")
    output = {k: result[k] for k in FIXED_RELEASE_KEYS}
    for field in FIXED_RELEASE_KEYS:
        if field in ("donor_pairs", "zero_identity_change_within_observed_support",
                     "identity_constant_effect_interpretation"):
            continue
        if not isinstance(output[field], (float, int)) or not math.isfinite(output[field]):
            raise ValueError("Nonfinite aggregate: " + field)
    if not isinstance(output["zero_identity_change_within_observed_support"], bool):
        raise ValueError("Support gate must be Boolean")
    if output["identity_constant_effect_interpretation"] not in (
        "DESCRIPTIVE_ONLY_NOT_CAUSAL",
        "UNVERIFIED_EXTRAPOLATED_OUTSIDE_IDENTITY_SUPPORT",
    ):
        raise ValueError("Invalid intercept caveat")
    if not output["zero_identity_change_within_observed_support"]:
        # Even the presence of an intercept is not worth promoting here.
        output.pop("identity_constant_intercept_age_delta", None)
    return {
        "schema":"BIO-MIMIC-X/INSTITUTIONALLY-APPROVED-AGGREGATE-ONLY/1",
        "data_source":"GSE295849 / dbGaP phs004047.v1.p1",
        "status":"DESCRIPTIVE_SIX_DONOR_RNA_ADJUSTED_ASSOCIATION_ONLY",
        "release_requires_prior_institutional_approval":True,
        "per_donor_genetic_or_RNA_data_included":False,
        "RNA_DNAm_same_aliquot":"UNVERIFIED",
        "RNA_treatment_and_batch":"UNVERIFIED",
        "causal_fate_independent_rejuvenation":"UNVERIFIED",
        "statistics":output,
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rna-counts",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--institutionally-authorized",action="store_true")
    parser.add_argument("--aggregate-release-approved",action="store_true")
    parser.add_argument("--authorization-reference",required=True)
    parser.add_argument("--release-reference",required=True)
    args=parser.parse_args(argv)
    ensure_private_runtime(args.rna_counts,args.out,args.institutionally_authorized,
                           args.aggregate_release_approved,args.authorization_reference,
                           args.release_reference)
    meth=json.loads(METH.read_text(encoding="utf-8"))
    rna=json.loads(RNA.read_text(encoding="utf-8"))
    ordered=condition_and_run_gate(meth,rna)
    table=read_count_matrix(args.rna_counts,ordered)
    score=identity_scores(table)
    internal=conditioned_age_delta(meth,rna,score)
    approved=release_safe_aggregate(internal)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    # Private out-of-repo file, strict permissions. No print of donor values.
    fd=os.open(args.out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as stream:
        json.dump(approved,stream,sort_keys=True,indent=2)
        stream.write("\n")
    print("BIO_MIMIC_INSTITUTION_APPROVED_AGGREGATE_WRITTEN; samplewise restricted data NOT printed or exported")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
