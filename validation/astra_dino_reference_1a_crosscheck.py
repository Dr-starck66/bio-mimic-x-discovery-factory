#!/usr/bin/env python3
"""ASTRA DINO Ω — independently verify complete chr1A (GCA_902806625.1).
Compares Ensembl release 116 dna_sm FASTA with original GenBank LR761574.1
obtained from ENA. Whole genome other than chr1A is NOT asserted identical.
"""
import argparse
import gzip
import hashlib
import json
import urllib.request
from pathlib import Path

ENSEMBL='https://ftp.ensembl.org/pub/release-116/fasta/camarhynchus_parvulus/dna/Camarhynchus_parvulus.Camarhynchus_parvulus_V1.1.dna_sm.primary_assembly.1A.fa.gz'
ENA='https://www.ebi.ac.uk/ena/browser/api/fasta/LR761574.1?download=false'
ASSEMBLY='GCA_902806625.1'
CHROM_LEN=72438334
EXPECTED='8f718d54d008f90f3d5075919a35a55354757d0b761d3a6313ae7b2772ed5803'
ENSEMBL_GZIP_SHA='5029540b231f58260d74ca83b6f5f2f8d0971c3a2f797c01fd70d47d5714b82e'

class SequenceMismatch(Exception):pass

def sequence_from_fasta(data,identifier):
    lines=data.splitlines()
    if not lines or not lines[0].startswith(b'>'):raise SequenceMismatch('INVALID_FASTA:'+identifier)
    if identifier=='ensembl' and not lines[0].startswith(b'>1A dna_sm:primary_assembly primary_assembly:Camarhynchus_parvulus_V1.1:1A:1:72438334:1'):
        raise SequenceMismatch('ENSEMBL_WRONG_ASSEMBLY_HEADER')
    if identifier=='ena' and b'LR761574.1' not in lines[0]:
        raise SequenceMismatch('ENA_WRONG_GENBANK_ACCESSION')
    seq=b''.join(lines[1:]).upper()
    if any(c not in b'ACGTN' for c in seq):raise SequenceMismatch('INVALID_NUCLEOTIDE')
    return seq

def compare(x,y,expected_len=CHROM_LEN,expected_sha=EXPECTED):
    if len(x)!=len(y) or len(x)!=expected_len:raise SequenceMismatch('CHROMOSOME_LENGTH_MISMATCH')
    d1=hashlib.sha256(x).hexdigest();d2=hashlib.sha256(y).hexdigest()
    if d1!=d2 or d1!=expected_sha or x!=y:
        raise SequenceMismatch('CHROMOSOME_SEQUENCE_MISMATCH')
    return {'status':'PASS_FULL_CHR1A_BASE_FOR_BASE','length':len(x),
            'sha256_ensembl':d1,'sha256_ena':d2,'differences':0}

def download(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ASTRA-DINO-OMEGA/1.0'}),timeout=120) as r:
        if r.status!=200:raise SequenceMismatch('HTTP_NOT_200:'+str(r.status))
        return r.read()

def run():
    xgz=download(ENSEMBL)
    if hashlib.sha256(xgz).hexdigest()!=ENSEMBL_GZIP_SHA:raise SequenceMismatch('ENSEMBL_GZIP_HASH_CHANGED')
    x=sequence_from_fasta(gzip.decompress(xgz),'ensembl')
    y=sequence_from_fasta(download(ENA),'ena')
    result=compare(x,y)
    result.update({'assembly':ASSEMBLY,'genbank_chr1A':'LR761574.1',
                   'ensembl_release':116,'source_ensembl':ENSEMBL,'source_ena':ENA,
                   'scope':'Full chr1A only; full 1756-contig genome and researchers local C_parvulus_sm.fa byte identity unverified'})
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try:
        obj=run()
        Path(args.output).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'status':obj['status'],'length':obj['length'],'sha256':obj['sha256_ena']}))
    except (OSError,ValueError,SequenceMismatch) as e:
        print(json.dumps({'status':'FAIL_CLOSED','reason':str(e)}))
        raise SystemExit(2)
