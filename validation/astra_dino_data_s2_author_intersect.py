#!/usr/bin/env python3
"""ASTRA DINO Ω — intersections des 28 régions Rubin 2022 avec le VCF authentique Oslo.

Entrées : fichier 28Loci_start_stop.txt de la branche publique des auteurs,
           fichiers privés Oslo originaux déjà archivés.
Aucun mapping arbitraire d'identifiants ou haplotype causal allégué.
Les deux conventions de bord des intervalles sont testées séparément.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
from collections import defaultdict
import csv, gzip, hashlib, json, re
from pathlib import Path
from astra_dino_rubin2022_vcf_intersection import checked_originals, find_oslo_pairs, score_variant

SOURCE_GIT_BLOB_SHA = 'dc6ec1da23aa6426fcc16dc5b5d1124d55699616'
SOURCE_CSV_GIT_BLOB_SHA = '383cebcfa21ec5bc898ddd5e3c2c2ab0560f2b21'
SOURCE_PDF_SHA256 = '5fabf42bbd0ab7df31e067ec36a1c4db60937c81ed0524b0cd64c638767aa8dc'
SOURCE_PDF_SIZE = 7409153
SOURCE_PDF_URL = 'https://pmc-oa-opendata.s3.amazonaws.com/PMC9269886.1/sciadv.abm5982_sm.pdf'
SOURCE_LOCI_URL = 'https://github.com/erikenbody/Darwins_finch_comparative_genomics/blob/master/XX_twisst_topology_weighting/28Loci_start_stop.txt'
SOURCE_CSV_URL = 'https://github.com/erikenbody/Darwins_finch_comparative_genomics/blob/master/supplementary_data_for_github/Supplementary_data_2_all_peaks_median_diversity_stat.csv'
GENES = {'HMGA2': ('1A',33408202,33520236), 'ALX1': ('1A',40877644,40920855)}

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def load_author_loci(path):
    raw=Path(path).read_bytes()
    if git_blob_sha(raw)!=SOURCE_GIT_BLOB_SHA:
        raise ValueError('AUTHOR_INTERVAL_SOURCE_GIT_BLOB_MISMATCH')
    rows=list(csv.DictReader(raw.decode('utf8').splitlines(),delimiter='\t'))
    if len(rows)!=28: raise ValueError('AUTHOR_28_LOCI_REQUIRED')
    loci=[]
    for r in rows:
        if set(r) != {'chr','start.pos','end.pos','loci.no'}:raise ValueError('AUTHOR_HEADER_INVALID')
        chrom=r['chr'].removeprefix('chr')
        start=int(r['start.pos']);end=int(r['end.pos']);number=int(r['loci.no'])
        if not (0<start<end):raise ValueError('AUTHOR_INTERVAL_INVALID')
        loci.append({'author_locus_number':number,'chrom':chrom,'start_as_published':start,'end_as_published':end,
                     'width_end_minus_start':end-start,'source':'28Loci_start_stop.txt'})
    if {r['author_locus_number'] for r in loci}!=set(range(1,29)):
        raise ValueError('AUTHOR_LOCUS_DUPLICATED_OR_MISSING')
    for chrom in set(r['chrom'] for r in loci):
        arr=sorted((r['start_as_published'],r['end_as_published']) for r in loci if r['chrom']==chrom)
        if any(a[1]>b[0] for a,b in zip(arr,arr[1:])):
            raise ValueError('AUTHOR_LOCI_OVERLAP')
    named={}
    for name,(chrom,start,end) in GENES.items():
        matches=[r for r in loci if chrom==r['chrom'] and r['start_as_published']<=start and r['end_as_published']>=end]
        if len(matches)!=1:raise ValueError('AUTHOR_GENE_LOCUS_AMBIGUOUS:'+name)
        named[name]=matches[0]['author_locus_number']
    if named != {'HMGA2':3,'ALX1':7}:
        raise ValueError('AUTHOR_GENOMIC_MAPPING_CHANGED')
    return loci,named,hashlib.sha256(raw).hexdigest()

def checked_source_csv(path,loci):
    """Optional exact author Data S2 CSV, when binary copied locally.
    Git blob SHA asserts byte-for-byte identity, then region-bound crosscheck.
    """
    if path is None: return 'ALREADY_CROSSCHECKED_BY_GITHUB_CONNECTOR_NOT_LOCAL'
    raw=Path(path).read_bytes()
    if git_blob_sha(raw)!=SOURCE_CSV_GIT_BLOB_SHA:raise ValueError('AUTHOR_DATA_S2_CSV_GIT_BLOB_MISMATCH')
    rows=list(csv.DictReader(raw.decode('utf8').splitlines()))
    if len(rows)!=84:raise ValueError('DATA_S2_84_ROWS_REQUIRED')
    got=defaultdict(list)
    for r in rows:
        m=re.fullmatch(r'chr([^:]+):(\d+)_(\d+)',r['region'])
        if not m:raise ValueError('DATA_S2_REGION_FORMAT')
        got[int(r['peak'])].append((m.group(1),int(m.group(2)),int(m.group(3)),r['contrast']))
    if len(got)!=28:raise ValueError('DATA_S2_28_PEAKS_REQUIRED')
    for interval in loci:
        entries=got[interval['author_locus_number']]
        if len(entries)!=3:raise ValueError('DATA_S2_3_CONTRASTS_REQUIRED')
        expected=(interval['chrom'],interval['start_as_published'],interval['end_as_published'])
        if any(e[:3]!=expected for e in entries):raise ValueError('DATA_S2_INTERVALS_DIFFER')
    return 'PASS_AUTHOR_GITHUB_BLOB_28_REGIONS_84_CONTRASTS'

def find_interval(loci_by_chrom,starts,chrom,pos):
    items=loci_by_chrom.get(chrom)
    if not items:return None
    i=bisect_right(starts[chrom],pos)-1
    if i<0:return None
    interval=items[i]
    if pos>interval['end_as_published']:return None
    return interval

def score(vcf_parts,paired):
    ref=vcf_parts[3];alt=vcf_parts[4]
    if not (len(ref)==len(alt)==1 and ref in 'ACGT' and alt in 'ACGT'):
        return False,False
    _,passes=score_variant(vcf_parts[9:],vcf_parts[8],paired)
    return True,passes

def scan_oslo(folder,source_loci,source_csv=None):
    originals=checked_originals(folder)
    loci,named,source_sha=load_author_loci(source_loci)
    csv_status=checked_source_csv(source_csv,loci)
    by_chrom={};starts={}
    for chrom in {x['chrom'] for x in loci}:
        by_chrom[chrom]=sorted([x for x in loci if x['chrom']==chrom],key=lambda r:r['start_as_published'])
        starts[chrom]=[x['start_as_published'] for x in by_chrom[chrom]]
    counters={r['author_locus_number']:dict(all_variants=0,biallelic_snp=0,passed_maf05_call80=0,
                                             boundary_start_variant=0,boundary_end_variant=0)
              for r in loci}
    genecounters={n:0 for n in GENES};total=chr1a=0;paired=[];nheader=0;vcfref=None
    with gzip.open(Path(folder)/'Prun64_3miss2mafNoZ_1.vcf.gz','rt',encoding='utf8') as f:
        for line in f:
            if line.startswith('##reference='):vcfref=line.strip().split('=',1)[1]
            if line.startswith('##'):continue
            if line.startswith('#CHROM'):
                h=line.rstrip('\n').split('\t');nheader=len(h)-9
                paired=find_oslo_pairs(folder,h[9:])
                continue
            if line.startswith('#'):continue
            p=line.rstrip('\n').split('\t');total+=1
            chrom=p[0].removeprefix('chr');pos=int(p[1])
            if chrom=='1A':chr1a+=1
            for name,(c,a,b) in GENES.items():
                if chrom==c and a<=pos<=b:genecounters[name]+=1
            interval=find_interval(by_chrom,starts,chrom,pos)
            if not interval:continue
            n=interval['author_locus_number'];entry=counters[n]
            entry['all_variants']+=1
            snp,passed=score(p,paired)
            if snp:entry['biallelic_snp']+=1
            if passed:entry['passed_maf05_call80']+=1
            if pos==interval['start_as_published']:entry['boundary_start_variant']+=1
            if pos==interval['end_as_published']:entry['boundary_end_variant']+=1
    if not (total==261754 and chr1a==21809 and nheader==64 and len(paired)==50):
        raise ValueError('OSLO_VCF_COUNTS_OR_CROSSWALK_MISMATCH')
    if genecounters!={'HMGA2':36,'ALX1':9}:raise ValueError('OSLO_GENE_BODY_COUNTER_MISMATCH')
    enriched=[]
    for r in loci:
        c=counters[r['author_locus_number']]
        variant_delta_halfopen=c['boundary_start_variant']
        enriched.append({**r,**c,'zero_based_half_open_variant_count_if_that_is_author_convention':c['all_variants']-variant_delta_halfopen,
                         'coordinate_boundary_sensitive':variant_delta_halfopen>0})
    return {'schema':'astra.dino.rubin2022_author_data_s2_oslo_vcf.v1',
            'status':'PASS_AUTHENTIC_SOURCE_28_LOCI_AND_REAL_OSLO_VCF','scientific_causal_status':'UNVERIFIED',
            'pdf_provenance':{'url':SOURCE_PDF_URL,'sha256_cloud_verified':SOURCE_PDF_SHA256,'bytes':SOURCE_PDF_SIZE,'pdf_page_4': 'Data S2 lists 28 divergent loci; Dryad deposit DOI link is not currently publicly available'},
            'author_provenance':{'github_loci_url':SOURCE_LOCI_URL,'github_loci_blob_sha':SOURCE_GIT_BLOB_SHA,'github_loci_sha256':source_sha,
                                  'github_data_s2_csv_url':SOURCE_CSV_URL,'github_data_s2_csv_blob_sha':SOURCE_CSV_GIT_BLOB_SHA,'csv_crosscheck':csv_status,
                                  'original_data_s2_dryad_doi':'10.5061/dryad.p2ngf1vsk','dryad_status':'404 / no public dataset version as of 2026-11-14'},
            'genome_assembly':'GCA_902806625.1','vcf_reference_header':vcfref,
            'oslo_originals_sha256':originals,'vcf_variants':total,'chr1a_variants':chr1a,'n_samples':nheader,'n_paired':len(paired),
            'locus_containing_genes_by_direct_genomic_overlap':named,'gene_body_variant_count_control':genecounters,
            'coordinate_convention':'AS_PUBLISHED_end_minus_start_equal_size__BOTH_BOUNDARY_INTERPRETATIONS_REPORTED',
            'loci':enriched,'all_loci_variant_count':sum(c['all_variants'] for c in counters.values()),
            'all_loci_passing_count':sum(c['passed_maf05_call80'] for c in counters.values()),
            'boundary_variant_count':sum(c['boundary_start_variant']+c['boundary_end_variant'] for c in counters.values()),
            'note':'No p-values recomputed, no independent cohort, no causal proof. No individual-level genotypes published.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--oslo-dir',required=True);ap.add_argument('--loci-tsv',required=True)
    ap.add_argument('--data-s2-csv');ap.add_argument('--output',required=True);a=ap.parse_args()
    x=scan_oslo(a.oslo_dir,a.loci_tsv,a.data_s2_csv)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:x[k] for k in ['status','vcf_variants','chr1a_variants','n_paired','all_loci_variant_count','all_loci_passing_count','boundary_variant_count','locus_containing_genes_by_direct_genomic_overlap']},ensure_ascii=False))
if __name__=='__main__':main()