#!/usr/bin/env python3
"""Public gene-expression CSV quality gate; not clinical or aging inference."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlparse


def analyze(csv_path, source_url, public_approved):
    if not public_approved:
        raise PermissionError('Only lawfully public, non-identifiable datasets allowed')
    url = urlparse(source_url)
    if url.scheme != 'https' or not url.netloc or url.username or url.password:
        raise ValueError('HTTPS source citation required without credentials')
    path = Path(csv_path)
    if not path.is_file() or path.suffix.lower() != '.csv':
        raise ValueError('Expected a real CSV sample-by-gene matrix')
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header or len(header) < 3 or header[0].strip().lower() != 'sample_id':
            raise ValueError('CSV columns must begin with sample_id and >=2 genes')
        genes = [g.strip() for g in header[1:]]
        if not all(genes) or len(set(genes)) != len(genes):
            raise ValueError('Gene identifiers must be nonempty and unique')
        seen = set()
        totals, detected = [], []
        for row in reader:
            if len(row) != len(header):
                raise ValueError('Inconsistent gene counts in row')
            sample_id = row[0].strip()
            if not sample_id or sample_id in seen:
                raise ValueError('Sample IDs must be nonempty and unique')
            seen.add(sample_id)
            values = []
            for item in row[1:]:
                try:
                    value = float(item)
                except ValueError:
                    raise ValueError('Non-numeric expression value') from None
                if not math.isfinite(value) or value < 0:
                    raise ValueError('Negative or non-finite expression value')
                values.append(value)
            totals.append(sum(values))
            detected.append(sum(v > 0 for v in values))
        if len(seen) < 2:
            raise ValueError('Need at least two distinct samples')
    return {'status': 'PARTIAL', 'gate': 'PUBLIC_MATRIX_QC_PASS',
            'input_sha256': h, 'source_url_declared': source_url,
            'public_approval': 'DECLARED_NOT_INDEPENDENTLY_VERIFIED',
            'n_samples': len(seen), 'n_genes': len(genes),
            'zero_library_samples': sum(v == 0 for v in totals),
            'min_detected_genes_per_sample': min(detected),
            'max_detected_genes_per_sample': max(detected),
            'biological_replication': 'UNVERIFIED',
            'aging_or_clinical_effect': 'UNVERIFIED'}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--matrix-csv', required=True)
    p.add_argument('--source-url', required=True)
    p.add_argument('--public-approved', action='store_true')
    p.add_argument('--output', default='/kaggle/working/bio-mimic-x-expression-qc.json')
    a = p.parse_args(argv)
    out = Path(a.output).resolve()
    if out == Path(a.matrix_csv).resolve():
        raise ValueError('Never replace source data')
    report = analyze(a.matrix_csv, a.source_url, a.public_approved)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
