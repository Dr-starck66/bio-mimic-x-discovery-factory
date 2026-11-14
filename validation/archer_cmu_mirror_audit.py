#!/usr/bin/env python3
"""ASTRA ARCHER VISION: real photos from a PINNED mirror, never an official-UCI SHA PASS.

Reuses the existing three-model BIO-MIMIC X comparison. No photographs are
written to the repository or to the JSON output; original ZIP not authenticated.
"""
from __future__ import annotations
import argparse, io, json, hashlib, tarfile
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image
from validation.archer_vision_real_cmu import (
    SUBJECTS, TRAIN_VIEWS, TEST_VIEWS, DATASET_SHA256, DATASET_URL, compare, sha256
)
MIRROR_URL = (
    "https://github.com/efeerenc/face_orientation_585/blob/"
    "25984c63f09db08cac5d8ff113bd0963af728406/"
    "cmu%2Bface%2Bimages/faces_4.tar.gz"
)
MIRROR_SHA256 = "fee2175af429f964d51d4b13cd7c2c23afbbc309edf8d9b84c975d2c1b41e8f4"
MIRROR_GIT_BLOB = "618061bbb9563c1cf09da83ee6c106430e843f76"
VIEWS = TRAIN_VIEWS + sum(TEST_VIEWS.values(), ())


def load_mirror_tar(path: Path):
    data = path.read_bytes()
    if sha256(data) != MIRROR_SHA256:
        raise ValueError("Mirror bytes changed: SHA-256 mismatch")
    imgs, checksums = {}, {}
    all_pgms = 0
    all_hashes = []
    rejected = Counter()
    member_count = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for item in tar:
            member_count += 1
            if not item.isfile():
                continue
            if item.name.endswith(".bad"):
                rejected["bad"] += 1
                continue
            if not item.name.endswith(".pgm"):
                continue
            all_pgms += 1
            raw = tar.extractfile(item).read()
            all_hashes.append(sha256(raw))
            person = Path(item.name).parent.name
            name = Path(item.name).name
            if person not in SUBJECTS:
                rejected["unknown_subject"] += 1
                continue
            for view in VIEWS:
                if name != f"{person}_{view}_4.pgm":
                    continue
                key = (person, view)
                if key in imgs:
                    raise ValueError("Duplicate sample: " + repr(key))
                with Image.open(io.BytesIO(raw)) as im:
                    if im.size != (32, 30):
                        raise ValueError(f"Unexpected PGM size {im.size}: {name}")
                    pixels = np.asarray(
                        im.convert("L").resize((64, 64), Image.Resampling.BILINEAR),
                        dtype=np.float32,
                    ) / 255.0
                if not np.isfinite(pixels).all():
                    raise ValueError("Non-finite image pixels")
                imgs[key] = pixels
                checksums[key] = sha256(raw)
    if all_pgms != 624 or len(set(all_hashes)) != 624:
        raise ValueError(f"PGM census mismatch: {all_pgms} images, {len(set(all_hashes))} unique")
    provenance = {
        "mirror_source": MIRROR_URL,
        "mirror_git_blob_sha1": MIRROR_GIT_BLOB,
        "mirror_tar_sha256": sha256(data),
        "mirror_tar_size_bytes": len(data),
        "all_valid_pgms": all_pgms,
        "valid_pgms_in_mirror": all_pgms,
        "all_unique_raw_pgms": len(set(all_hashes)),
        "selected_views_count": len(imgs),
        "tar_members_count": member_count,
        "rejected": dict(rejected),
        "official_uci_url": DATASET_URL,
        "official_zip_expected_sha256": DATASET_SHA256,
        "official_zip_sha256_verified": False,
    }
    return imgs, checksums, provenance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mirror-tar", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    opts = parser.parse_args()
    images, checksums, source = load_mirror_tar(opts.mirror_tar)
    result = compare(images=images, checksums=checksums, verified_source=False)
    result["status"] = "REAL_PHOTOS_MIRROR_PROVENANCE_PARTIAL"
    result["source_verified"] = False
    result["archive_caveat"] = (
        "UCI ZIP SHA-256 not verified. These are real photographs from a "
        "third-party GitHub mirror; NOT an official UCI-archive-verified result."
    )
    result["mirror_manifest"] = source
    result["n_selected_images"] = len(images)
    result["selected_image_sha256"] = {
        f"{person}/{view}": digest for (person, view), digest in checksums.items()
    }
    opts.out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    opts.out.write_text(payload, encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "report": str(opts.out),
        "report_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "eligible_subjects": result["eligible_identities"],
        "excluded": result["excluded_incomplete_subjects"],
        "archive_sha256_uci_verified": False,
    }, indent=2))


if __name__ == "__main__":
    main()
