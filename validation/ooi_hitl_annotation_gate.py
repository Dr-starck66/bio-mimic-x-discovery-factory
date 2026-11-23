#!/usr/bin/env python3
"""Extend the existing OOI Escargot screen with conservative human-annotation exclusions.

No real sample temperatures or anomaly claims until pinned NetCDF + annotations
are downloaded, hash-checked and actually analyzed.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from validation.ooi_axial_hydrothermal import (analyze_file, screen, NTP_EPOCH,
                                                 OOI_2026_08_04_FILENAME)


def _as_utc(value):
    if isinstance(value,(float,int)):
        # OOI annotations frequently express Unix milliseconds; not NTP seconds.
        ts=float(value)/1000 if float(value)>1e11 else float(value)
        return datetime.fromtimestamp(ts,timezone.utc)
    if isinstance(value,str):
        value=value.strip().replace("Z","+00:00")
        dt=datetime.fromisoformat(value)
        if dt.tzinfo is None: raise ValueError("annotation_timestamp_without_timezone")
        return dt.astimezone(timezone.utc)
    raise ValueError("bad_annotation_timestamp")


def normalize_annotations(raw):
    if isinstance(raw,dict):
        if "annotations" in raw: raw=raw["annotations"]
        else: raise ValueError("annotation_object_missing_annotations_key")
    if not isinstance(raw,list): raise ValueError("annotations_must_be_array")
    out=[]
    for i,item in enumerate(raw):
        start=item.get("beginDT",item.get("start"))
        end=item.get("endDT",item.get("end"))
        if start is None or end is None: raise ValueError("annotation_missing_interval")
        start,end=_as_utc(start),_as_utc(end)
        if end<start: raise ValueError("annotation_reversed_interval")
        note=" ".join(str(item.get(key,"")) for key in ("annotation","comment","description","exclusionReason"))
        flag=item.get("qcFlag",item.get("qc_flag"))
        # Conservatively mask ANY temporal annotation until review, including
        # ambiguous intervals. Deployment markers may reduce coverage; this is recorded.
        out.append({"index":i,"start":start,"end":end,"note":note,"qc_flag":flag,
                    "hitl": "HITL" in note.upper() or "HUMAN-IN-THE-LOOP" in note.upper()})
    return out


def screen_with_annotations(times,temperatures,qartod_flags,annotations,*,min_good=12):
    annotations=normalize_annotations(annotations)
    new_flags=list(qartod_flags)
    masked=[]; hitl_masked=[]
    for i,stamp in enumerate(times):
        utc=NTP_EPOCH+__import__('datetime').timedelta(seconds=float(stamp))
        overlaps=[a for a in annotations if a["start"]<=utc<=a["end"]]
        if overlaps:
            if int(qartod_flags[i]) == 1: masked.append(i)
            if int(qartod_flags[i]) == 1 and any(a["hitl"] for a in overlaps): hitl_masked.append(i)
            new_flags[i]=4
    before=screen(times,temperatures,qartod_flags,min_good=min_good)
    after=screen(times,temperatures,new_flags,min_good=min_good)
    return {"status":"ANNOTATION_AWARE_SCREEN_NOT_GEOLOGIC_VALIDATION",
            "n_annotations":len(annotations),"n_hitl_annotations":sum(a["hitl"] for a in annotations),
            "n_original_qartod_pass_valid":before["n_qartod_pass_valid"],
            "n_after_annotation_qartod_pass_valid":after["n_qartod_pass_valid"],
            "n_qartod_pass_overlapping_annotation":len(masked),
            "n_qartod_pass_overlapping_hitl":len(hitl_masked),
            "masked_sample_indices":masked,
            "original_qartod_counts":before["qartod_counts"],
            "candidate_anomalies_before_annotation":before["candidate_anomalies"],
            "candidate_anomalies_after_annotation":after["candidate_anomalies"],
            "post_filter_status":after["status"],
            "physical_event_confirmed":False,
            "warnings":["All annotated intervals are conservatively masked, including non-HITL; review manually",
                        "HITL flags can be unrecognized if documentation lacks the literal HITL tag",
                        "Unknown annotation coverage is not evidence that no annotation exists"]}


def analyze_pinned_file_with_annotations(path:Path,annotation_path:Path):
    # Reuse pre-existing identity, checksum and structural checks.
    original=analyze_file(path)
    import h5py
    with h5py.File(path,"r") as ds:
        times=ds["time"][:].tolist()
        temperatures=ds["vent_fluid_temperature"][:].tolist()
        flags=ds["vent_fluid_temperature_qartod_results"][:].tolist()
    content=annotation_path.read_bytes()
    return {**screen_with_annotations(times,temperatures,flags,json.loads(content)),
            "data_source_filename":OOI_2026_08_04_FILENAME,
            "data_source_sha256":original["source_sha256"],
            "annotation_source_sha256":sha256(content).hexdigest(),
            "input_type":"REAL_BYTES_PROVIDED_NOT_AUTOMATICALLY_VERIFIED_AS_OFFICIAL",
            "original_screen_version":original["analysis_version"]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--annotations-json",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if not a.input.exists() or not a.annotations_json.exists():
        raise SystemExit("UNVERIFIED: need both actual pinned OOI NetCDF and official annotation export")
    r=analyze_pinned_file_with_annotations(a.input,a.annotations_json)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"status":r["status"],"n_qartod_pass_overlapping_hitl":r["n_qartod_pass_overlapping_hitl"]}))

if __name__=="__main__":main()
