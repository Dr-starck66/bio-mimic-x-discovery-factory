#!/usr/bin/env python3
"""ASTRA DINO Ω. Verified Oslo VCF intersection; rejects unpublished haploblock boundaries.

The gene bodies and equal-width flanks are *comparison controls*, NOT Rubin 2022 Data S2.
VCF and optional interval inputs are never copied into the output.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re

ASSEMBLY = 'GCA_902806625.1'
SHA = {
  'Morphometrics.txt':'4722f565feeda8290d3985b4a65d9e0c4e91690270264cfc931d26f24cc51555',
  'pPCAeigen.txt':'d615bd8dd3fd22091b971b20f18a49832d1f2afaf390a30ea3465f6a276b5bff',
  'Prun64_3miss2mafNoZ_1.vcf.gz':'471db73a5eb65a8bb6af8f25872a5a2d0bc0115556203250f69eb61988163d34'
}
GENES = {
  'ALX1':('1A', 40877644,40920855),
  'HMGA2':('1A', 33408202,33520236)
}

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def checked_originals(folder):
    hashes={}
    for name,expected in SHA.items():
        p=Path(folder)/name
        if not p.is_file():raise ValueError('MISSING_OSLO_ORIGINAL:'+name)
        observed=digest(p)
        if observed != expected:raise ValueError('OSLO_SHA_MISMATCH:'+name)
        hashes[name]=observed
    return hashes

def interval(chrom,lo,hi,label):
    if chrom!='1A' or not (1<=lo<=hi<=72438334):
        raise ValueError('INVALID_INTERVAL_1A:'+str(label))
    return {'chrom':chrom,'start':lo,'end':hi,'label':label}

def internal_controls():
    out=[]
    for key,(chrom,a,b) in GENES.items():
        size=b-a+1
        out.extend([interval(chrom,a,b,key+'_GENE_BODY'),
                    interval(chrom,a-size,a-1,key+'_LEFT_EQUAL_WIDTH'),
                    interval(chrom,b+1,b+size,key+'_RIGHT_EQUAL_WIDTH')])
    return out

def load_official_intervals(path, source_pdf_path=None):
    """A manifest must contain a source PDF SHA and exact manually verified Data S2 rows.
    Never silently convert gene bodies to Rubin haploblocks.
    """
    if path is None:raise ValueError('AUTHENTIC_DATA_S2_NOT_AVAILABLE')
    m=json.loads(Path(path).read_text(encoding='utf-8'))
    # Reject a manifest that merely *asserts* a PDF hash without the source bytes.
    if source_pdf_path is None:
        raise ValueError('DATA_S2_SOURCE_PDF_BYTES_REQUIRED')
    pdf=Path(source_pdf_path)
    if not pdf.is_file() or pdf.stat().st_size < 1024:
        raise ValueError('DATA_S2_SOURCE_PDF_MISSING_OR_SHORT')
    with pdf.open('rb') as fh:
        if fh.read(5)!=b'%PDF-':raise ValueError('DATA_S2_NOT_PDF')
    for key,val in {'source_doi':'10.1126/sciadv.abm5982','assembly':ASSEMBLY,
                    'coordinate_convention':'1-based-inclusive','evidence_kind':'author_supplement_Data_S2'}.items():
        if m.get(key)!=val:raise ValueError('DATA_S2_METADATA_UNVERIFIED:'+key)
    sha=m.get('source_pdf_sha256')
    if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):
        raise ValueError('DATA_S2_PDF_HASH_MISSING')
    if digest(pdf)!=sha:raise ValueError('DATA_S2_SOURCE_PDF_SHA_MISMATCH')
    source=m.get('source_pdf_url','')
    if not source.startswith(('https://pmc.ncbi.nlm.nih.gov/articles/PMC9269886/bin/',
                              'https://www.science.org/doi/suppl/10.1126/sciadv.abm5982/')):
        raise ValueError('DATA_S2_OFFICIAL_SOURCE_URL_MISSING')
    entries=m.get('intervals')
    if not isinstance(entries,list) or len(entries)<2:raise ValueError('DATA_S2_INTERVALS_MISSING')
    out=[]
    for x in entries:
        if not isinstance(x,dict) or not isinstance(x.get('locus'),(str,int)):
            raise ValueError('DATA_S2_BAD_LOCUS')
        chrom=str(x.get('chrom'))
        if chrom not in ('1A','chr1A'):raise ValueError('NOT_CHR_1A')
        try:a=int(x['start']);b=int(x['end'])
        except (TypeError,KeyError,ValueError):raise ValueError('DATA_S2_COORDINATES_MISSING')
        out.append(interval('1A',a,b,str(x['locus'])))
    names=[x['label'] for x in out]
    if len(set(names))!=len(names):raise ValueError('DATA_S2_DUPLICATE_LOCI')
    return out

def find_oslo_pairs(folder,header_samples):
    pca={}
    with open(Path(folder)/'pPCAeigen.txt',newline='') as f:
        for x in csv.DictReader(f,delimiter='\t'):
            key=x['SampleID']
            if key in pca:raise ValueError('DUPLICATE_PCA_SAMPLE')
            pca[key]=x
    morph={}
    with open(Path(folder)/'Morphometrics.txt',newline='') as f:
        for x in csv.DictReader(f,delimiter='\t'):
            key=x['AccNo']
            if key in morph:raise ValueError('DUPLICATE_MORPH_ACCNO')
            morph[key]=x
    if set(pca)!=set(header_samples) or len(header_samples)!=64:
        raise ValueError('PCA_VCF_SAMPLES_MISMATCH')
    pairs=[]
    for i,s in enumerate(header_samples):
        m=re.fullmatch(r'(\d{6})_(?:S\d+|sub\d*)',s)
        if not m:continue
        a=m.group(1)
        if a not in morph:raise ValueError('NO_AUTHORIZED_MORPH:'+a)
        for col in ['Beak_length','Beak_height','Beak_width']:
            if float(morph[a][col])<=0:raise ValueError('INVALID_MORPH')
        pairs.append(i)
    if len(pairs)!=50:raise ValueError('PAIRED_SAMPLES_NOT_50')
    return pairs

def score_variant(samples,format_,pair_indices):
    keys=format_.split(':')
    if 'GT' not in keys:return False,False
    k=keys.index('GT');dosages=[]
    for i in pair_indices:
        parts=samples[i].split(':')
        if k>=len(parts):continue
        gt=parts[k].replace('|','/').split('/')
        if len(gt)!=2 or any(t not in ('0','1') for t in gt):continue
        dosages.append(int(gt[0])+int(gt[1]))
    if len(dosages)<40:return True,False
    maf=min(sum(dosages)/(2*len(dosages)),1-sum(dosages)/(2*len(dosages)))
    return True,maf>=0.05

def scan(folder,blocks=None):
    folder=Path(folder); hashes=checked_originals(folder)
    ctrls=internal_controls(); all_iv=ctrls+(blocks or [])
    counts={x['label']:{'all_records':0,'biallelic_snp':0,'paired_50_pass_maf05_call80':0}
            for x in all_iv}
    n_all=0;n_chr1a=0;n_samples=0;paired=[]
    p=folder/'Prun64_3miss2mafNoZ_1.vcf.gz'
    with gzip.open(p,'rt',encoding='utf-8') as fh:
        for line in fh:
            if line.startswith('##'):continue
            if line.startswith('#CHROM'):
                h=line.rstrip('\n').split('\t');n_samples=len(h)-9
                paired=find_oslo_pairs(folder,h[9:])
                continue
            if line.startswith('#'):continue
            cells=line.rstrip('\n').split('\t');n_all+=1
            if cells[0]!='1A':continue
            n_chr1a+=1;pos=int(cells[1]);ref=cells[3];alt=cells[4]
            candidates=[x for x in all_iv if x['start']<=pos<=x['end']]
            if not candidates:continue
            good_snp=(len(ref)==1 and len(alt)==1 and ref in 'ACGT' and alt in 'ACGT')
            if good_snp:
                _,pass_filter=score_variant(cells[9:],cells[8],paired)
            else: pass_filter=False
            for x in candidates:
                y=counts[x['label']];y['all_records']+=1
                if good_snp:y['biallelic_snp']+=1
                if pass_filter:y['paired_50_pass_maf05_call80']+=1
    if n_all!=261754 or n_chr1a!=21809 or n_samples!=64 or len(paired)!=50:
        raise ValueError('VCF_COHORT_REFERENCE_GATE_FAILED')
    return {'schema':'astra.dino.rubin2022_oslo_intersect.v1',
      'source_doi_oslo':'10.5061/dryad.3ffbg79w8',
      'source_doi_rubin':'10.1126/sciadv.abm5982',
      'reference_assembly':ASSEMBLY,'reference_fasta_verified_in_previous_run_not_reloaded':True,
      'originals_sha256':hashes,'records_all':n_all,'records_chr1a':n_chr1a,
      'samples_vcf':n_samples,'paired_oslo_samples':len(paired),
      'controls':counts,
      'rubin_data_s2':{'status':'PASS_VERIFIED_INTERVAL_INTERSECTION' if blocks is not None else 'BLOCKED_AUTHENTIC_INTERVAL_BOUNDS_UNAVAILABLE',
        'rows':len(blocks or []),
        'note':'Rubin loci not defined by gene body or equal-width flank; Data S2 source coordinates required'},
      'scope':'Authentic Oslo VCF scan; no novel statistical association, no causality or independent validation'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--oslo-dir',required=True)
    p.add_argument('--data-s2-manifest');p.add_argument('--data-s2-source-pdf');p.add_argument('--output',required=True)
    args=p.parse_args()
    if args.data_s2_manifest:
        blocks=load_official_intervals(args.data_s2_manifest,args.data_s2_source_pdf)
    else:blocks=None
    result=scan(args.oslo_dir,blocks)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['rubin_data_s2']['status'],
                      'n_all':result['records_all'],'n_chr1a':result['records_chr1a'],
                      'paired':result['paired_oslo_samples'],'gene_body_counts':{
                      key:result['controls'][key]['all_records'] for key in ['ALX1_GENE_BODY','HMGA2_GENE_BODY']}},ensure_ascii=False))

if __name__=='__main__':main()