#!/usr/bin/env python3
"""Download and audit a public GSE295849 beta matrix; no claims about DNAm age.

Fail closed: HTTP provenance, bounded byte count, full checksum, full gzip
integrity, parseability, CpG row identifiers, numeric beta range. Results are
scientific QC only, not reproduction of the published epigenetic clocks.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request

BASE = 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE295nnn/GSE295849/suppl/'
FILES = {
    '1': ('GSE295849_Berg_et_al_beta_values_1.txt.gz', 230_000_000),
    '2': ('GSE295849_Berg_et_al_beta_values_2.txt.gz', 130_000_000),
    '3': ('GSE295849_Berg_et_al_beta_values_3.txt.gz', 95_000_000),
}

def audit_local(path, source_url, expected_sha256=None, min_bytes=500):
    """Analyze complete local gzip and record per-column means, not ages."""
    sha = hashlib.sha256()
    size = 0
    with open(path, 'rb') as fh:
        while (chunk := fh.read(1024 * 1024)):
            sha.update(chunk)
            size += len(chunk)
    digest = sha.hexdigest()
    if expected_sha256 and digest != expected_sha256.lower():
        raise ValueError('expected source hash mismatch')
    if size < min_bytes:
        raise ValueError('gzip source implausibly short')
    with open(path, 'rb') as fh:
        if fh.read(2) != b'\x1f\x8b':
            raise ValueError('gzip magic mismatch')
    header = None
    samples = []
    sums = []
    seen = []
    numeric_failures = 0
    out_of_range = 0
    rows = 0
    duplicate_cpgs = 0
    prev_cpg = None
    # csv reader consumes gzip through EOF: trailer and CRC validated.
    with gzip.open(path, 'rt', encoding='utf-8-sig', errors='strict', newline='') as f:
        peek = f.readline()
        delimiter = '\t' if peek.count('\t') >= peek.count(',') else ','
        f.seek(0)
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if not row or row[0].startswith(('#', '!')):
                continue
            if header is None:
                header = [c.strip() for c in row]
                if len(header) < 3:
                    raise ValueError('no multi-sample matrix header')
                samples = header[1:]
                sums = [0.0] * len(samples)
                seen = [0] * len(samples)
                if len(set(samples)) != len(samples):
                    raise ValueError('duplicate sample column name')
                continue
            if len(row) != len(header):
                raise ValueError('unexpected row width at row '+str(rows+2))
            cpg = row[0].strip()
            if not cpg:
                raise ValueError('empty probe identifier')
            if cpg == prev_cpg:
                duplicate_cpgs += 1
            prev_cpg = cpg
            rows += 1
            for j, value in enumerate(row[1:]):
                v = value.strip()
                if not v or v.upper() in {'NA','NAN','NULL'}:
                    continue
                try:
                    x = float(v)
                except ValueError:
                    numeric_failures += 1
                    continue
                if not (0 <= x <= 1):
                    out_of_range += 1
                else:
                    sums[j] += x
                    seen[j] += 1
    if not rows or not seen or not any(seen):
        raise ValueError('no numeric beta values')
    if numeric_failures or out_of_range:
        raise ValueError('invalid beta values: nonnumeric='+str(numeric_failures)+' out_of_range='+str(out_of_range))
    return {
        'dataset':'GSE295849', 'source_url':source_url, 'compressed_bytes':size,
        'compressed_sha256':digest, 'rows':rows, 'columns':len(samples),
        'column_summary':[{ 'sample':name, 'nonmissing':seen[j],
                            'mean_beta':round(sums[j] / seen[j], 8) if seen[j] else None}
                            for j,name in enumerate(samples)],
        'compression_integrity':'PASS', 'numeric_beta_qc':'PASS',
        'methylation_clock_reproduction':'UNVERIFIED',
        'biological_rejuvenation':'UNVERIFIED',
        'comment':'Per-column methylation mean is NOT epigenetic age.',
    }

def audit_remote(part, timeout=120):
    name, limit = FILES[part]
    url = BASE + name
    request = urllib.request.Request(url, headers={'User-Agent':'BIO-MIMIC-X-GEO-integrity/1.0'})
    hasher = hashlib.sha256()
    total = 0
    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / name
        with urllib.request.urlopen(request, timeout=timeout) as r, open(target,'wb') as output:
            if r.status != 200 or r.url != url:
                raise RuntimeError('unexpected HTTP status or redirect')
            expected = int(r.headers.get('Content-Length','0') or '0')
            if expected and expected > limit:
                raise ValueError('remote file over byte budget')
            while chunk := r.read(1024 * 1024):
                total += len(chunk)
                if total > limit:
                    raise ValueError('download exceeded byte cap')
                hasher.update(chunk)
                output.write(chunk)
        if expected and total != expected:
            raise ValueError('Content-Length mismatch; likely truncated')
        report = audit_local(target, url, expected_sha256=hasher.hexdigest())
        report['source_content_length'] = expected or None
        return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--part',choices=sorted(FILES),default='3')
    p.add_argument('--local-file',type=Path)
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    try:
        r = audit_local(args.local_file, 'local-synthetic-fixture') if args.local_file else audit_remote(args.part)
        r['status']='PASS_INTEGRITY_AND_DESCRIPTIVE_QC_ONLY'
        code=0
    except Exception as e:
        r={'status':'PARTIAL_SOURCE_FAILURE','dataset':'GSE295849',
           'part':args.part,'reason':f'{type(e).__name__}: {e}',
           'methylation_clock_reproduction':'UNVERIFIED'}
        code=1
    payload=json.dumps(r,indent=2,ensure_ascii=False,sort_keys=True)+'\n'
    print('BIO_MIMIC_GSE295849_QC '+payload)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(payload,encoding='utf-8')
    return code

if __name__=='__main__':
    raise SystemExit(main())
