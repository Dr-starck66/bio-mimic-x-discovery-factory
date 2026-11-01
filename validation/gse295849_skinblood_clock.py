#!/usr/bin/env python3
"""Independent Horvath 2018 391-CpG Skin&Blood clock calculation on GSE295849.

Research-only; predicts an epigenetic biomarker, not human clinical efficacy.
All input and model bytes are hash-pinned. No missing CpGs are imputed.
The 8 individual chip IDs are NOT grouped into donors or biological conditions.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import urllib.request

# Accept execution both as a script and as an imported module.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validation.gse295849_real_qc import audit_remote

MODEL_URLS = (
    "https://huggingface.co/pyaging/skinandblood/resolve/main/skinandblood.pt",
    "https://hf.co/pyaging/skinandblood/resolve/main/skinandblood.pt",
)
MODEL_SHA256 = "56f8ce6567170ce5427f24803d30a2f0e3f6d3735b44100af02521fcd7c18027"
MODEL_SIZE = 17613
# Source: author model's artifact (Hugging Face pyaging/skinandblood), pinned blob.
DATA_FILE3_SHA256 = "fa92b4124a5bd7c69a878ae4557d2def91b1698203fc975fe63003de27640f2d"
HORVATH2018_DOI = "10.18632/aging.101508"
BERG2026_DOI = "10.1111/acel.70751"
VALID_SAMPLE = re.compile(r"^\d+_R\d{2}C\d{2}$")

def inverse_age(z: float, adult_age: float = 20) -> float:
    """Horvath anti-log-linear age transform described by pyaging."""
    if not math.isfinite(z):
        raise ValueError("nonfinite model score")
    return (1 + adult_age) * math.exp(z) - 1 if z < 0 else (1 + adult_age) * z + adult_age


def fetch_pinned_model():
    import torch  # imported after pyaging (required class definitions)
    import pyaging  # noqa: F401 — class module for trusted torch.load
    err = None
    for url in MODEL_URLS:
        try:
            req = urllib.request.Request(url,headers={"User-Agent":"BIO-MIMIC-X-scientific-reproduction/1.0"})
            with urllib.request.urlopen(req,timeout=45) as resp:
                data = resp.read(50_001)
            digest = hashlib.sha256(data).hexdigest()
            if len(data) != MODEL_SIZE or digest != MODEL_SHA256:
                raise ValueError("model bytes differ from pinned publisher-model artifact")
            model = torch.load(io.BytesIO(data),map_location="cpu",weights_only=False)
            features = getattr(model,"features",None)
            if not isinstance(features,(tuple,list)) or len(features) != 391 or len(set(features))!=391:
                raise ValueError("model has wrong feature list")
            if features[0] != "cg12140144":
                raise ValueError("unexpected Skin&Blood model identity")
            layer = model.base_model.linear
            weights = layer.weight.detach().cpu().flatten().tolist()
            intercept = float(layer.bias.detach().cpu().flatten()[0])
            if len(weights)!=len(features) or abs(weights[0]-0.36318117)>1e-5 or abs(intercept+0.447119319)>1e-5:
                raise ValueError("model coefficients mismatch Horvath 2018 reference")
            model.eval()
            return model,features,weights,intercept,url
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
    raise RuntimeError("unable to load hash-pinned clock: "+str(err))


def collect_clock_cpgs(path, features):
    expected=set(features)
    matched={}
    header=None
    sample_ids=None
    expected_width=None
    with gzip.open(path,"rt",encoding="utf-8-sig",errors="strict",newline="") as fh:
        reader=csv.reader(fh,delimiter="\t")
        for rec in reader:
            if not rec or rec[0].startswith("#"):
                continue
            if header is None:
                header=rec
                if all(VALID_SAMPLE.fullmatch(x) for x in header):
                    sample_ids=header[:]  # bare Illumina sample identifiers
                    expected_width=len(header)+1
                elif len(header)>1 and all(VALID_SAMPLE.fullmatch(x) for x in header[1:]):
                    sample_ids=header[1:]  # explicitly labeled CpG index column
                    expected_width=len(header)
                else:
                    raise ValueError("unexpected GEO sample header: columns="+str(len(header))+
                                     ", first="+repr(header[:3]))
                if len(set(sample_ids))!=len(sample_ids):
                    raise ValueError("duplicate Illumina sample identifiers")
                continue
            if len(rec)!=expected_width:
                raise ValueError("CpG row width mismatch")
            key=rec[0]
            if key not in expected:
                continue
            if key in matched:
                raise ValueError("duplicate clock CpG "+key)
            values=[]
            for value in rec[1:]:
                try:
                    v=float(value)
                except ValueError:
                    raise ValueError("missing or nonnumeric clock CpG "+key)
                if not (0 <= v <= 1):
                    raise ValueError("non-beta clock CpG "+key)
                values.append(v)
            matched[key]=values
    if not sample_ids:
        raise ValueError("no sample columns")
    absent=sorted(expected-set(matched))
    if absent:
        raise ValueError(f"clock CpG coverage {len(matched)}/{len(features)}; missing: {absent[:12]}")
    return sample_ids,matched


def predict_samples(path, model,features,weights,intercept):
    import torch
    header,matched=collect_clock_cpgs(path,features)
    values=[[matched[feature][sample_i] for feature in features] for sample_i in range(len(header))]
    xs=torch.tensor(values,dtype=model.base_model.linear.weight.dtype)
    with torch.no_grad():
        predicted=model(xs)
    predictions=predicted.detach().cpu().flatten().tolist()
    if len(predictions)!=len(header):
        raise ValueError("prediction sample count mismatch")
    results=[]
    for sample,featureset,library_age in zip(header,values,predictions):
        raw_score=intercept+sum(w*b for w,b in zip(weights,featureset))
        manual=inverse_age(raw_score)
        if abs(manual-library_age)>0.1:
            raise ValueError(f"model/postprocessing disagreement {manual} != {library_age}")
        results.append({"chip_sample_id":sample,"age_years":round(manual,5),
                        "clock_score":round(raw_score,8)})
    return results


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--part",choices=["1","2","3"],default="3")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args(argv)
    report={"schema":"BIO-MIMIC-X/GSE295849-HORVATH2018-REAL-CLOCK/1",
            "data_series":"GSE295849","part":args.part,
            "clock":"Horvath2018 Skin&Blood", "clock_doi":HORVATH2018_DOI,
            "study_doi":BERG2026_DOI,"model_sha256":MODEL_SHA256,
            "clinical_anti_aging":"UNVERIFIED",
            "donor_condition_time_reproduction":"UNVERIFIED",
            "axolotl_human_regeneration":"UNVERIFIED"}
    try:
        model,features,weights,intercept,model_url=fetch_pinned_model()
        report["model_url"]=model_url
        def from_local(path,validation):
            report["source_sha256"]=validation["compressed_sha256"]
            report["source_sample_count"]=validation["columns"]
            report["source_cpg_rows"]=validation["rows"]
            return predict_samples(path,model,features,weights,intercept)
        validation=audit_remote(args.part,on_file=from_local)
        report["samples"]=validation["derivation"]
        report["feature_count"]=len(features)
        report["status"]="PASS_INDEPENDENT_CLOCK_ESTIMATION_UNGROUPED"
        report["caution"]="Clock ages are algorithmic biomarkers. Not matched to donors, conditions or times; no 61-year anti-aging replication."
        exit_code=0
    except Exception as exc:
        report["status"]="PARTIAL_SOURCE_OR_MODEL_FAILURE"
        report["reason"]=f"{type(exc).__name__}: {exc}"
        exit_code=1
    out=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    print("BIO_MIMIC_HORVATH2018_REAL_CLOCK "+out)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(out,encoding="utf-8")
    return exit_code

if __name__=="__main__":
    raise SystemExit(main())
