#!/usr/bin/env python3
"""Inventory FG-NET researcher-hosted photos and 68-point manual annotations.

No portraits or identity-level records are exported. An altered ZIP is rejected.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,re,zipfile
from pathlib import Path
FGNET_SOURCE="https://yanweifu.github.io/FG_NET_data/FGNET.zip"
EXPECTED_MD5="1206978cac3626321b84c22b24cc8d19"
IMAGE_EXT={".jpg",".jpeg",".png",".bmp"}
KEY=re.compile(r"(?<![0-9])(?P<id>\d{3})A\d+",re.IGNORECASE)
MAX_ZIP=80_000_000

def parse_points(raw:bytes):
    text=raw.decode("latin1").replace("\r","\n")
    rows=[]
    for line in text.split("\n"):
        t=line.strip().strip("{}").replace(","," ")
        if not t or t.startswith(("#","version:","n_points:","points:")):continue
        cells=t.split()
        if len(cells)!=2:continue
        try:a,b=map(float,cells)
        except ValueError:continue
        if not (-1e5<a<1e5 and -1e5<b<1e5):
            raise ValueError("Invalid coordinate")
        rows.append([a,b])
    return rows

def census(zip_bytes:bytes,*,expected_md5=EXPECTED_MD5,require_annotated_identities=25):
    if len(zip_bytes)>MAX_ZIP or not zip_bytes:raise ValueError("ZIP missing or >80 MB")
    digest=hashlib.md5(zip_bytes,usedforsecurity=False).hexdigest()
    if digest!=expected_md5:raise ValueError("Research ZIP MD5 mismatch")
    sha=hashlib.sha256(zip_bytes).hexdigest()
    bystem=collections.defaultdict(lambda:dict(images=[],points=[]))
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        contents=z.infolist()
        if len(contents)>15000:raise ValueError("Unexpected member count")
        names=set()
        for member in contents:
            name=member.filename.replace("\\","/")
            if name.startswith("/") or ".." in name.split("/"):raise ValueError("Unsafe ZIP member path")
            if name in names:raise ValueError("Duplicate ZIP member")
            names.add(name)
            if member.is_dir():continue
            ext=Path(name).suffix.lower()
            if ext not in IMAGE_EXT|{".pts"}:continue
            match=KEY.search(Path(name).stem)
            if not match:continue
            stem=Path(name).stem.upper()
            if ext in IMAGE_EXT:bystem[stem]["images"].append(name)
            else:bystem[stem]["points"].append(name)
        pairs=[(stem,d) for stem,d in bystem.items() if len(d["images"])==1 and len(d["points"])==1]
        per_id=collections.Counter()
        fmt=collections.Counter()
        examples=[]
        for stem,d in pairs:
            item=z.getinfo(d["points"][0])
            if item.file_size>20000:raise ValueError("Oversized landmark annotation")
            pts=parse_points(z.read(item))
            fmt[len(pts)]+=1
            if len(pts)!=68:continue
            per_id[KEY.search(stem).group("id")]+=1
            if len(examples)<2:
                examples.append({"rows_count":len(pts),"coord_first5":pts[:5],
                                 "coord_range":[min(p[0] for p in pts),max(p[0] for p in pts),
                                                min(p[1] for p in pts),max(p[1] for p in pts)]})
        eligible=sum(n>=3 for n in per_id.values())
        report={"source_url":FGNET_SOURCE,"zip_sha256":sha,"zip_md5":digest,
                "publisher_md5_reference":"dlordinal FGNet loader",
                "total_zip_bytes":len(zip_bytes),"zip_members":len(contents),
                "recognized_stems":len(bystem),"matched_image_landmark_pairs":len(pairs),
                "manual_landmark_point_counts":dict(fmt),"valid_68_point_image_pairs":sum(per_id.values()),
                "paired_identities":len(per_id),"identities_with_3plus_pairs":eligible,
                "minimum_preregistered_identities":require_annotated_identities,
                "max_pairs_per_identity":max(per_id.values(),default=0),
                "min_pairs_per_identity":min(per_id.values(),default=0),
                "points_format_examples":examples,
                "nonmatching_pair_count":len(bystem)-len(pairs),
                "status":"PASS_ACCESS_AND_ANNOTATION_GATE" if eligible>=require_annotated_identities and sum(per_id.values())>=75 else "FAIL_CLOSED_INSUFFICIENT_ANNOTATED_IDENTITIES",
                "raw_portraits_exported":False,"face_identities_exported":False,
                "license_for_commercial_use":"UNVERIFIED","face_recognition_accuracy":"NOT_TESTED"}
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--zip",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    report=census(a.zip.read_bytes())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:report[k] for k in ("status","zip_sha256","total_zip_bytes",
         "matched_image_landmark_pairs","paired_identities","identities_with_3plus_pairs",
         "manual_landmark_point_counts","nonmatching_pair_count","points_format_examples")},indent=2))
    if report["status"]!="PASS_ACCESS_AND_ANNOTATION_GATE":raise SystemExit(3)

if __name__=="__main__":main()
