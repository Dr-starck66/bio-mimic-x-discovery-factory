"""Infer FG-NET landmark numbering from aggregate coordinates; never export individual faces.

A reference audit, not a benchmark or a post-hoc performance-driven threshold change.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
from validation.archer_fgnet_manifest_gate import census,parse_points

def schema(zip_bytes:bytes):
    manifest=census(zip_bytes)
    if manifest["status"]!="PASS_ACCESS_AND_ANNOTATION_GATE":raise ValueError("FG-NET integrity fail")
    rows=[];count=0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for item in z.infolist():
            if Path(item.filename).suffix.lower()!=".pts":continue
            p=np.asarray(parse_points(z.read(item)),dtype=np.float64)
            if p.shape!=(68,2):continue
            lo=p.min(axis=0);hi=p.max(axis=0)
            scale=hi-lo
            if np.any(scale<=1):continue
            rows.append((p-lo)/scale)
            count+=1
    a=np.stack(rows)
    mean=a.mean(axis=0)
    med=np.median(a,axis=0)
    std=a.std(axis=0)
    output={
        "schema":"FGNET_ANON_LANDMARK_INDEX_SCHEME_DIAGNOSTIC_V1",
        "source_sha256":manifest["zip_sha256"],
        "n_manual_68_point_annotations":count,
        "coordinates_normalized_to_each_annotation_bbox":True,
        "aggregation":"mean, median, std over all 1002 annotations",
        "index_base":0,"privacy":"no individual photo or full per-person landmarks stored",
        "points":[{"index0":i,"mean":[round(float(x),4) for x in mean[i]],
                    "median":[round(float(x),4) for x in med[i]],
                    "std":[round(float(x),4) for x in std[i]]}
                  for i in range(68)],
        "assumed_ibug_eye_groups":{"first":mean[36:42].mean(axis=0).round(4).tolist(),
                                    "second":mean[42:48].mean(axis=0).round(4).tolist()},
        "assumed_ibug_nose":mean[30].round(4).tolist(),
        "assumed_ibug_mouth":mean[62].round(4).tolist(),
        "status":"INDEX_GEOMETRY_MEASURED_NOT_VALIDATED_AS_IBUG"
    }
    return output
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=schema(a.zip.read_bytes())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":report["status"],"n":report["n_manual_68_point_annotations"],
                      "indexed_medians":{str(i):report["points"][i]["median"] for i in range(68)}},indent=2))
if __name__=="__main__":main()
