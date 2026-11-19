#!/usr/bin/env python3
"""Bridge genuine Thermo Fisher MoGene-2_0-st-v1 probe-tab ZIP to ASTRA probe gate.

No gene assignments are invented. Without an independently versioned gene map,
probe-set identifiers are labeled UNMAPPED_PROBESET_* and biological gene/module
interpretation must remain UNVERIFIED.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024), b''):h.update(chunk)
    return h.hexdigest()


def norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+','',s.casefold().lstrip('# '))


def columns(keys):
    d={norm(k):k for k in keys}
    def name(*alias):
        for a in alias:
            if norm(a) in d:return d[norm(a)]
        return None
    return {'seq':name('Probe Sequence','probe_sequence','ProbeSequence','sequence'),
            'set':name('Probe Set Name','probeset_id','ProbeSet','Probe Set ID'),
            'x':name('Probe X','ProbeX','X'), 'y':name('Probe Y','ProbeY','Y')}


def read_map(path: Path | None) -> dict:
    if path is None:return {}
    with path.open(encoding='utf-8-sig',newline='') as f:
        first=f.readline(); delim='\t' if first.count('\t')>=first.count(',') else ','
        r=csv.DictReader([first,*f],delimiter=delim)
        if not r.fieldnames or not {'probeset','gene_id'}.issubset(set(r.fieldnames)):
            raise ValueError('gene_map_requires_probeset_and_gene_id_columns')
        m={}
        for row in r:
            k=row['probeset'].strip();v=row['gene_id'].strip()
            if not k or not v or k in m:raise ValueError('blank_or_duplicate_gene_map_entry')
            m[k]=v
        if not m:raise ValueError('empty_gene_map')
        return m


def convert(vendor_zip: Path, outdir: Path, gene_map: Path | None=None):
    if not vendor_zip.is_file():raise FileNotFoundError(vendor_zip)
    mapping=read_map(gene_map)
    outdir.mkdir(parents=True,exist_ok=True)
    total=0;seq_unique=set();missing_map=set();member_names=[];seen_coords=set()
    tsv=outdir/'gpl16570_probes.tsv'
    meta=outdir/'gpl16570_probe_provenance.tsv'
    with zipfile.ZipFile(vendor_zip) as z, tsv.open('w',encoding='utf-8',newline='') as f, meta.open('w',encoding='utf-8',newline='') as provenance:
        corrupt=z.testzip()
        if corrupt:raise ValueError(f'zip_crc_fail:{corrupt}')
        w=csv.DictWriter(f,fieldnames=['probe_id','gene_id','sequence'],delimiter='\t');w.writeheader()
        wm=csv.DictWriter(provenance,fieldnames=['probe_id','probeset','x','y','sequence'],delimiter='\t');wm.writeheader()
        for item in z.infolist():
            if item.is_dir() or not item.filename.lower().endswith(('.txt','.tsv','.tab','.csv')):continue
            if item.file_size>2_000_000_000:raise ValueError('zip_member_too_large')
            with z.open(item) as raw:
                stream=io.TextIOWrapper(raw,encoding='utf-8-sig',errors='strict',newline='')
                lines=(line for line in stream if line.strip() and not line.startswith(('#%', '##', '//')))
                first=next(lines,None)
                if first is None:continue
                delim='\t' if first.count('\t')>=first.count(',') else ','
                reader=csv.DictReader(_prepend(first,lines),delimiter=delim)
                c=columns(reader.fieldnames or [])
                if not c['seq'] or not c['set']:continue
                member_names.append(item.filename)
                if len(member_names)>1:raise ValueError('multiple_probe_sequence_tables_ambiguous')
                for i,row in enumerate(reader,2):
                    seq=(row[c['seq']] or '').strip().upper();ps=(row[c['set']] or '').strip()
                    if not ps or len(seq)!=25 or any(ch not in 'ACGT' for ch in seq):
                        raise ValueError(f'invalid_25mer:{item.filename}:{i}')
                    x=(row.get(c['x']) or '').strip() if c['x'] else ''
                    y=(row.get(c['y']) or '').strip() if c['y'] else ''
                    if x and y:
                        key=(ps,x,y)
                        if key in seen_coords:raise ValueError(f'duplicate_probe_coordinates:{key}')
                        seen_coords.add(key)
                    total+=1;pid=f'P{total:09d}'
                    gene=mapping.get(ps)
                    if gene is None:
                        missing_map.add(ps);gene=f'UNMAPPED_PROBESET_{ps}'
                    w.writerow({'probe_id':pid,'gene_id':gene,'sequence':seq})
                    wm.writerow({'probe_id':pid,'probeset':ps,'x':x,'y':y,'sequence':seq})
                    seq_unique.add(seq)
    if not member_names or total==0:raise ValueError('no_valid_vendor_probe_table')
    report={'status':'PASS_PROBE_CONVERSION_ONLY','vendor_zip_sha256':sha256(vendor_zip),
            'gene_map_sha256':sha256(gene_map) if gene_map else None,
            'probe_rows':total,'unique_sequences':len(seq_unique),
            'probesets_without_authoritative_gene_id':len(missing_map),
            'gene_annotation_complete':len(missing_map)==0 and bool(gene_map),
            'source_zip_member':member_names[0],
            'cross_species_probe_alignment_executed':False,
            'biological_replication_validated':False}
    (outdir/'vendor_bridge_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


def _prepend(first,lines):
    yield first
    yield from lines


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vendor-zip',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--gene-map',type=Path,help='Versioned probeset-to-gene mapping table; otherwise UNMAPPED labels')
    a=p.parse_args()
    print(json.dumps(convert(a.vendor_zip,a.out,a.gene_map),indent=2,ensure_ascii=False))

if __name__=='__main__':main()