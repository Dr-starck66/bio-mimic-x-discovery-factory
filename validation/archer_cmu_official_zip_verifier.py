#!/usr/bin/env python3
"""Byte-level verification of UCI CMU ZIP against a locally SHA-pinned TAR mirror.

A checksum quoted on a website does not prove that the downloaded bytes match it.
Default accepts only the published UCI SHA-256. The optional expected SHA
argument is for unit-test fixtures ONLY, and never reports official PASS.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import tarfile
import zipfile
from pathlib import Path
from validation.archer_vision_real_cmu import DATASET_SHA256, DATASET_URL
from validation.archer_cmu_mirror_audit import MIRROR_SHA256

MAX_ZIP_BYTES = 34 * 1024 * 1024
MAX_NESTED_BYTES = 3 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pgm_manifest(content: bytes) -> dict:
    entries = {}
    with tarfile.open(fileobj=io.BytesIO(content), mode='r:gz') as tar:
        for item in tar:
            if not item.isfile() or not item.name.endswith('.pgm'):
                continue
            name = item.name.removeprefix('./')
            if '..' in Path(name).parts or name.startswith('/'):
                raise ValueError('Unsafe TAR member path')
            if name in entries:
                raise ValueError('Duplicate member path: '+name)
            if item.size > 65536:
                raise ValueError('Unexpectedly large individual PGM')
            blob = tar.extractfile(item).read()
            if len(blob) != item.size:
                raise ValueError('Truncated PGM member')
            entries[name] = sha(blob)
    return entries


def inspect_zip_bytes(official: bytes, mirror_tar: bytes, *, expected_zip_sha: str=DATASET_SHA256,
                      expected_pgm_count: int=624) -> dict:
    if not official or len(official) > MAX_ZIP_BYTES:
        raise ValueError('Official ZIP missing or outside bounded size')
    official_digest = sha(official)
    if official_digest != expected_zip_sha:
        raise ValueError('Official ZIP SHA-256 mismatch: '+official_digest)
    with zipfile.ZipFile(io.BytesIO(official)) as z:
        members=[x for x in z.infolist() if x.filename.rsplit('/',1)[-1]=='faces_4.tar.gz']
        if len(members)!=1:
            raise ValueError('Expected exactly one faces_4.tar.gz')
        member=members[0]
        if member.file_size > MAX_NESTED_BYTES:
            raise ValueError('Nested TAR oversized')
        nested=z.read(member)
    if len(nested)>MAX_NESTED_BYTES:
        raise ValueError('Oversized nested bytes')
    nested_digest=sha(nested)
    mirror_digest=sha(mirror_tar)
    real_pgm=pgm_manifest(nested)
    mirrored_pgm=pgm_manifest(mirror_tar)
    if len(real_pgm)!=expected_pgm_count or len(mirrored_pgm)!=expected_pgm_count:
        raise ValueError('PGM census mismatch')
    changed=sorted(k for k in real_pgm.keys() & mirrored_pgm.keys() if real_pgm[k]!=mirrored_pgm[k])
    missing=sorted(real_pgm.keys()-mirrored_pgm.keys())
    extra=sorted(mirrored_pgm.keys()-real_pgm.keys())
    official_authentic = expected_zip_sha == DATASET_SHA256
    mirror_pinned=mirror_digest == MIRROR_SHA256
    all_same=not(changed or missing or extra)
    return {
        'status': 'PASS_OFFICIAL_ZIP_VERIFIED' if official_authentic and mirror_pinned and all_same
                  else 'PARTIAL_MISMATCH_OR_FIXTURE',
        'official_zip_url':DATASET_URL,
        'official_zip_bytes':len(official),
        'official_zip_sha256_computed':official_digest,
        'official_zip_sha256_matches_published':official_authentic,
        'fixture_override_used':not official_authentic,
        'nested_tar_sha256':nested_digest,
        'nested_tar_matches_mirror_bytewise':nested==mirror_tar,
        'mirror_tar_sha256_computed':mirror_digest,
        'mirror_tar_sha256_matches_pinned':mirror_pinned,
        'official_pgm_count':len(real_pgm),
        'mirror_pgm_count':len(mirrored_pgm),
        'same_pgm_file_bytes':all_same,
        'missing_from_mirror':missing[:25],
        'extra_in_mirror':extra[:25],
        'changed_pgm_entries':changed[:25],
        'no_real_face_images_redistributed':True,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--official-zip',type=Path,required=True)
    ap.add_argument('--mirror-tar',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if not args.official_zip.exists():
        raise SystemExit('FAIL_CLOSED: official UCI ZIP not present; no provenance PASS')
    raw=args.official_zip.read_bytes()
    mirror=args.mirror_tar.read_bytes()
    report=inspect_zip_bytes(raw,mirror)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ['status','official_zip_sha256_computed','nested_tar_sha256',
                'nested_tar_matches_mirror_bytewise','same_pgm_file_bytes']},indent=2))
    if report['status']!='PASS_OFFICIAL_ZIP_VERIFIED':
        raise SystemExit('PARTIAL: SHA or individual image mismatch; inspect report')

if __name__=='__main__':main()
