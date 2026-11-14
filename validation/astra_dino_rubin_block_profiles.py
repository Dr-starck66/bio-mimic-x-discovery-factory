#!/usr/bin/env python3
"""ASTRA DINO Ω — phenotype-blind, whole-block genotype PCA + corrected permutation tests.

Requires private authentic Oslo originals and Rubin's exact published 28-locus TSV.
28 individual block tests and the ALX1+HMGA2 joint test, two outcomes, are
corrected *jointly* by max-T over all 58 predeclared hypotheses. Loci 3 and 7
contain HMGA2 and ALX1. SNPs are unphased; PCA scores are NOT phased haplotypes.
No genotype/sample IDs or raw genotype matrix are persisted in evidence.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

# Reuse the published, audited source-identity and specimen-crosswalk gates.
_REUSE = Path(__file__).resolve().parent
if str(_REUSE) not in sys.path:
    sys.path.insert(0, str(_REUSE))
from astra_dino_rubin2022_vcf_intersection import checked_originals
from astra_dino_data_s2_author_intersect import (
    load_author_loci, checked_source_csv, SOURCE_GIT_BLOB_SHA,
    SOURCE_CSV_GIT_BLOB_SHA,
)

SCHEMA = 'astra.dino.rubin2022.block_pca_permutation.v1'
N_EXPECTED = 50
ALL_RECORDS = 261754
GENOME = 'GCA_902806625.1'
PRIMARY_BLOCKS = {'HMGA2': 3, 'ALX1': 7}
N_PERM_DEFAULT = 20000
SEED_DEFAULT = 20261114


class GateError(ValueError):
    pass


def read_matched(folder: Path, samples: list[str]):
    """Verify exact 50 individual identities without ever exposing them in output."""
    pca={}
    with (folder/'pPCAeigen.txt').open(encoding='utf-8', newline='') as fh:
        for row in csv.DictReader(fh, delimiter='\t'):
            if row['SampleID'] in pca:raise GateError('DUPLICATE_SAMPLE_IN_PCA')
            pca[row['SampleID']]=row
    morph={}
    with (folder/'Morphometrics.txt').open(encoding='utf-8', newline='') as fh:
        for row in csv.DictReader(fh, delimiter='\t'):
            if row['AccNo'] in morph:raise GateError('DUPLICATE_ACCNO')
            morph[row['AccNo']]=row
    if len(samples)!=64 or len(set(samples))!=64 or set(samples)!=set(pca):
        raise GateError('SAMPLES_PCA_VCF_MISMATCH')
    indices=[];groups=[];length=[];height=[];width=[]
    for i,s in enumerate(samples):
        m=re.fullmatch(r'(\d{6})_(?:S\d+|sub\d*)', s)
        if not m:continue
        acc=m.group(1)
        if acc not in morph:raise GateError('UNAUTHORIZED_OR_MISSING_ID_JOIN')
        v=[]
        for col in ('Beak_length','Beak_height','Beak_width'):
            try: x=float(morph[acc][col])
            except (ValueError,KeyError):raise GateError('INVALID_BEAK_TRAIT')
            if not math.isfinite(x) or x<=0:raise GateError('INVALID_BEAK_TRAIT')
            v.append(x)
        group=pca[s].get('Population','').strip()
        if not group:raise GateError('MISSING_POPULATION')
        indices.append(i);groups.append(group)
        length.append(v[0]);height.append(v[1]);width.append(v[2])
    if len(indices)!=N_EXPECTED or len({samples[x].split('_')[0] for x in indices})!=N_EXPECTED:
        raise GateError('EXPECTED_50_DISTINCT_PAIRED')
    if len(set(groups))<2:raise GateError('INSUFFICIENT_POPULATION_STRATA')
    y=np.column_stack((np.log(np.array(height)/np.array(length)),
                       (np.log(length)+np.log(height)+np.log(width))/3))
    return indices,groups,y


def variant_dosages(fields: list[str], format_string: str, pair_indices: list[int]):
    """Return None if SNP fails 80%-call and 5%-MAF thresholds."""
    format_keys=format_string.split(':')
    if 'GT' not in format_keys:return None
    j=format_keys.index('GT')
    v=np.full(len(pair_indices),np.nan,dtype=float)
    for k,i in enumerate(pair_indices):
        data=fields[i].split(':')
        if j>=len(data):continue
        alleles=data[j].replace('|','/').split('/')
        if len(alleles)!=2 or not all(a in ('0','1') for a in alleles):continue
        v[k]=int(alleles[0])+int(alleles[1])
    good=np.isfinite(v)
    if good.sum()<40:return None
    mean=float(v[good].mean())
    maf=min(mean/2.0,1.0-mean/2.0)
    if maf<.05:return None
    return v


def extract(folder: Path, loci: list[dict]):
    loc={x['author_locus_number']:[] for x in loci}
    sorted_by_chrom={}
    for chrom in sorted({x['chrom'] for x in loci}):
        arr=sorted((x for x in loci if x['chrom']==chrom),key=lambda x:x['start_as_published'])
        sorted_by_chrom[chrom]=(arr,[x['start_as_published'] for x in arr])
    group_names=None;indices=None;y=None;rows_total=0;rows_chr1a=0;counts=Counter()
    with gzip.open(folder/'Prun64_3miss2mafNoZ_1.vcf.gz','rt',encoding='utf-8') as fh:
        for line in fh:
            if line.startswith('##'):continue
            if line.startswith('#CHROM'):
                samples=line.rstrip('\n').split('\t')[9:]
                indices,group_names,y=read_matched(folder,samples)
                continue
            if line.startswith('#'):continue
            row=line.rstrip('\n').split('\t');rows_total+=1
            chrom=row[0].removeprefix('chr')
            pos=int(row[1])
            if chrom=='1A':rows_chr1a+=1
            indexed=sorted_by_chrom.get(chrom)
            if indexed is None: continue
            blocks,starts=indexed
            idx=bisect_right(starts,pos)-1
            if idx<0 or pos>blocks[idx]['end_as_published']:continue
            locus=blocks[idx]['author_locus_number']
            counts[locus]+=1
            if len(row)!=9+64:raise GateError('TRUNCATED_VCF_ROW')
            if not(len(row[3])==len(row[4])==1 and row[3] in 'ACGT' and row[4] in 'ACGT'):
                continue
            vec=variant_dosages(row[9:],row[8],indices)
            if vec is not None:loc[locus].append((pos,vec))
    if rows_total!=ALL_RECORDS or rows_chr1a!=21809 or indices is None or y is None:
        raise GateError('AUTHENTIC_OSLO_FILE_COUNTS_MISMATCH')
    return loc, counts, group_names, y, rows_total


def genotype_pca(markers: list[tuple[int,np.ndarray]], n_pcs=2):
    """Unsupervised PCA fitted only on genotype dosage, with mean imputation."""
    if len(markers)<n_pcs:raise GateError('INSUFFICIENT_SNP_FOR_PCA')
    M=np.column_stack([x[1] for x in markers])
    means=np.nanmean(M,axis=0)
    if not np.isfinite(means).all():raise GateError('ALL_MISSING_SNP')
    M=np.where(np.isfinite(M),M,means)
    M=M-means
    std=np.sqrt((M*M).mean(axis=0))
    if (std<=1e-10).any():raise GateError('ZERO_VARIANCE_AFTER_MAF_FILTER')
    M/=std
    # N x SNP; SVD yields N x PC scores. No phenotypes enter this call.
    U,S,_=np.linalg.svd(M,full_matrices=False)
    if np.sum(S>1e-8)<n_pcs:raise GateError('GENOTYPE_PCA_RANK_DEFICIENT')
    pc=U[:,:n_pcs]*S[:n_pcs]
    explained=(S[:n_pcs]**2/(S**2).sum()).tolist()
    return pc,explained


def group_indices(group_names):
    groups=defaultdict(list)
    for i,g in enumerate(group_names):groups[g].append(i)
    return [np.array(ids,dtype=int) for ids in groups.values()]


def residualize_by_group(matrix, groups):
    arr=np.asarray(matrix,dtype=float).copy()
    for ids in groups:arr[ids]-=arr[ids].mean(axis=0)
    return arr


def orthonormal_design(x,groups):
    centered=residualize_by_group(x,groups)
    U,S,_=np.linalg.svd(centered,full_matrices=False)
    rank=int(np.sum(S>1e-9))
    if rank!=centered.shape[1]:raise GateError('MODEL_LOST_RANK_WITHIN_POPULATION')
    return U[:,:rank]


def r2(Q,y):
    denom=np.einsum('no,no->o',y,y)
    if np.any(denom<1e-12):raise GateError('NO_WITHIN_POPULATION_VARIANCE')
    projection=Q.T@y
    return np.einsum('ko,ko->o',projection,projection)/denom


def permutation_maxT(models, y, groups, nperm:int, seed:int):
    """Shared within-pop permutations of both correlated traits, max-R2 across 58 tests."""
    if nperm<99:raise GateError('NEED_AT_LEAST_99_PERMUTATIONS')
    model_keys=list(models)
    projections=[models[k] for k in model_keys]
    obs=np.array([r2(q,y) for q in projections]) # M x 2
    flat_obs=obs.reshape(-1)
    exceed=np.zeros_like(flat_obs,dtype=int)
    family=np.zeros_like(flat_obs,dtype=int)
    n=len(y);rng=np.random.default_rng(seed)
    perm_max=np.empty(nperm,dtype=float)
    for p in range(nperm):
        perm=np.arange(n)
        for ids in groups:
            perm[ids]=rng.permutation(ids)
        yp=y[perm] # group-centered y stays centered when permuted within groups
        vals=np.array([r2(q,yp) for q in projections]).reshape(-1)
        exceed+=(vals>=flat_obs-1e-12)
        m=float(vals.max());perm_max[p]=m
        family+=(m>=flat_obs-1e-12)
    raw=(exceed+1)/(nperm+1)
    adj=(family+1)/(nperm+1)
    return model_keys,obs,raw.reshape(-1,2),adj.reshape(-1,2),perm_max


def sensitivity_by_pop(models,y,groups,group_names):
    out={}
    n=len(y)
    for name in ('LOCUS_03_HMGA2','LOCUS_07_ALX1','JOINT_03_07'):
        arr=[]
        for pop,ids in sorted({p:np.flatnonzero(np.array(group_names)==p) for p in set(group_names)}.items()):
            keep=np.ones(n,dtype=bool);keep[ids]=False
            subgroups=group_indices([v for i,v in enumerate(group_names) if keep[i]])
            try:
                q=orthonormal_design(models[name][keep,:],subgroups)
                yy=residualize_by_group(y[keep],subgroups)
                vals=r2(q,yy)
                arr.append({'excluded_pop':pop,'excluded_n':len(ids),'shape_r2':round(float(vals[0]),6),'size_r2':round(float(vals[1]),6)})
            except GateError as e:arr.append({'excluded_pop':pop,'reason':str(e)})
        out[name]={'n_deletions':len(arr),'all_numeric':all('shape_r2' in x for x in arr),
                    'size_r2_min':round(min(x['size_r2'] for x in arr if 'size_r2' in x),6) if any('size_r2' in x for x in arr) else None,
                    'size_r2_max':round(max(x['size_r2'] for x in arr if 'size_r2' in x),6) if any('size_r2' in x for x in arr) else None,
                    'folds':arr}
    return out


def run(folder,source_loci,nperm=N_PERM_DEFAULT,seed=SEED_DEFAULT,source_csv=None):
    folder=Path(folder);originals=checked_originals(folder)
    loci,named,tsv_sha=load_author_loci(source_loci)
    csv_status=checked_source_csv(source_csv,loci)
    if named!=PRIMARY_BLOCKS:raise GateError('WRONG_ALX1_HMGA2_MAPPING')
    if len(loci)!=28:raise GateError('28_LOCI_REQUIRED')
    markers,counts,labels,y,nrows=extract(folder,loci)
    groupmap=group_indices(labels)
    Y=residualize_by_group(y,groupmap)
    models={};raw={};pcs={};explained={}
    for loc in sorted(markers):
        tag=f'LOCUS_{loc:02d}'+('_HMGA2' if loc==3 else '_ALX1' if loc==7 else '')
        score,ev=genotype_pca(markers[loc]);pcs[loc]=score
        raw[tag]=score;models[tag]=orthonormal_design(score,groupmap)
        explained[tag]=ev
    joint=np.column_stack((pcs[3],pcs[7]))
    raw['JOINT_03_07']=joint;models['JOINT_03_07']=orthonormal_design(joint,groupmap)
    keys,observed,praw,padj,nullmax=permutation_maxT(models,Y,groupmap,nperm,seed)
    # Secondary, separately labeled, focused-family and 1-PC sensitivity.
    focal=['LOCUS_03_HMGA2','LOCUS_07_ALX1','JOINT_03_07']
    focused={name:models[name] for name in focal}
    _,secondary_obs,secondary_raw,secondary_adj,_=permutation_maxT(focused,Y,groupmap,nperm,seed)
    one_pc_raw={name:pcs[loc][:,:1] for loc,name in [(3,'LOCUS_03_HMGA2'),(7,'LOCUS_07_ALX1')]}
    one_pc_raw['JOINT_03_07']=np.column_stack([pcs[3][:,:1],pcs[7][:,:1]])
    one_pc={name:orthonormal_design(val,groupmap) for name,val in one_pc_raw.items()}
    _,one_obs,one_raw,one_adj,_=permutation_maxT(one_pc,Y,groupmap,nperm,seed)
    # This guards against cherry-picking the best of 1-PC vs 2-PC configurations.
    both_family={**{name+'__2PC':focused[name] for name in focal},
                 **{name+'__1PC':one_pc[name] for name in focal}}
    _,twelve_obs,twelve_raw,twelve_adj,_=permutation_maxT(both_family,Y,groupmap,nperm,seed)
    secondary=[]
    for j,name in enumerate(focal):
        secondary.append({'model':name,
                          'two_pc_focal_family6':{'shape_r2':round(float(secondary_obs[j,0]),8),'size_r2':round(float(secondary_obs[j,1]),8),
                              'shape_p_maxR2_fwer6':round(float(secondary_adj[j,0]),8),'size_p_maxR2_fwer6':round(float(secondary_adj[j,1]),8)},
                          'one_pc_exploratory_fwer6':{'shape_r2':round(float(one_obs[j,0]),8),'size_r2':round(float(one_obs[j,1]),8),
                              'shape_p_maxR2_fwer6':round(float(one_adj[j,0]),8),'size_p_maxR2_fwer6':round(float(one_adj[j,1]),8)},
                          'across_both_pc_choices_family12':{
                              'twoPC_shape_p_maxR2_fwer12':round(float(twelve_adj[j,0]),8),
                              'twoPC_size_p_maxR2_fwer12':round(float(twelve_adj[j,1]),8),
                              'onePC_shape_p_maxR2_fwer12':round(float(twelve_adj[j+3,0]),8),
                              'onePC_size_p_maxR2_fwer12':round(float(twelve_adj[j+3,1]),8)}})
    # A single predeclared sham crosswalk, generated by a different seed,
    # *not* used to choose the primary result. Its raw/max-T p is descriptive.
    sham_rng=np.random.default_rng(seed+17);perm=np.arange(N_EXPECTED)
    for ids in groupmap:perm[ids]=sham_rng.permutation(ids)
    shamY=Y[perm]
    sham=[{'model':key,'shape_r2':round(float(r2(models[key],shamY)[0]),6),
          'size_r2':round(float(r2(models[key],shamY)[1]),6)} for key in ('LOCUS_03_HMGA2','LOCUS_07_ALX1','JOINT_03_07')]
    tests=[]
    for i,name in enumerate(keys):
        tests.append({'model':name,'block_locus':int(name[6:8]) if name.startswith('LOCUS_') else None,
                      'n_predictors':int(models[name].shape[1]),
                      'n_pass_filtered_snp':len(markers[int(name[6:8])]) if name.startswith('LOCUS_') else len(markers[3])+len(markers[7]),
                      'pc_variance_ratios_genotype_only': [round(float(v),6) for v in explained[name]] if name in explained else None,
                      'shape_within_pop_r2':round(float(observed[i,0]),8),
                      'size_within_pop_r2':round(float(observed[i,1]),8),
                      'p_shape_uncorrected':round(float(praw[i,0]),8),
                      'p_size_uncorrected':round(float(praw[i,1]),8),
                      'p_shape_maxT_58':round(float(padj[i,0]),8),
                      'p_size_maxT_58':round(float(padj[i,1]),8)})
    # Strict comparison to prior VCF audit: counts on the 28 loci must match.
    checkpoint={3:(706,394),7:(410,238)}
    for idx,(expected_total,expected_pass) in checkpoint.items():
        if counts[idx]!=expected_total or len(markers[idx])!=expected_pass:
            raise GateError(f'PREVIOUS_VCF_COUNT_MISMATCH:{idx}')
    n_pass=sum(map(len,markers.values()))
    if n_pass!=3570 or sum(counts.values())!=6928:
        raise GateError('PREVIOUS_GLOBAL_COUNTS_MISMATCH')
    out={'schema':SCHEMA,'status':'PASS_LOCAL_EXECUTION__EXPLORATORY_SCIENTIFIC_RESULTS',
         'source':{'rubin_2022_doi':'10.1126/sciadv.abm5982','rubin_loci_git_blob_sha1':SOURCE_GIT_BLOB_SHA,
                   'rubin_source_sha256':tsv_sha,'rubin_csv_git_blob_sha1':SOURCE_CSV_GIT_BLOB_SHA,
                   'rubin_csv_qc':csv_status,'oslo_dataset_doi':'10.5061/dryad.3ffbg79w8',
                   'oslo_originals_sha256':originals,'assembly':GENOME},
         'cohort':{'vcf_records':nrows,'vcf_total_samples':64,'paired_samples':N_EXPECTED,
                   'groups_count':len(groupmap),'group_sizes_sorted':sorted([len(x) for x in groupmap]),
                   'phenotypes':['log(beak_height/beak_length)','(log(length)+log(height)+log(width))/3']},
         'primary_analysis':{'method':'Unphased genotype-dose PCA, 2 PCs per block; population fixed-effect residualization; shared 2-phenotype within-population permutation; maxT across 28 blocks and joint ALX1+HMGA2 = 58 tests',
                             'blocks':[3,7],'n_predeclared_models':29,'n_outcomes':2,'n_total_hypotheses':58,
                             'n_permutations':nperm,'seed':seed,'maxT_null_p95':round(float(np.quantile(nullmax,.95)),8),
                             'all_28_variant_count':int(sum(counts.values())),'all_28_passing_count':int(n_pass),
                             'tested_models':tests},
         'secondary_sensitivity_exploratory_NOT_CONFIRMATORY':{'scope':'Focused 3 models x 2 endpoints, plus one-PC alternative; additional 12-test correction over model choice. Examined after broad 58-test primary family; not independent validation', 'results':secondary},
         'negative_controls':{'within_pop_permutation_null':'PASS_COMPUTED','sham_crosswalk':'PERMUTED_PHENOTYPES_NON_INDEPENDENT_SANITY_CHECK',
                              'sham_profiles':sham,
                              'other_26_author_selected_blocks':'COMPARATORS_NOT_NULL_REGIONS',
                              'source_digest_mutant_rejection':'TESTED_SEPARATELY_IN_UNIT_TESTS'},
         'leave_one_population_out_descriptive':sensitivity_by_pop(raw,Y,groupmap,labels),
         'scientific_scope':{'phased_haplotypes':False,'genotype_PCs_are_true_haplotypes':False,
                              'genetic_ancestry_modules_causal':False,'independent_validation':False,
                              'population_relatedness_fully_controlled':False,
                              'notes':'R² descriptive within training cohort, not held-out predictions. Population stratification and kinship remain possible. 28 blocks were discovered with another species comparison; selected panel is not genome-wide. Marker data SNPs do not prove whole-block LD/haplotype phase.'}}
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--oslo-dir',required=True);p.add_argument('--loci-tsv',required=True)
    p.add_argument('--author-data-s2-csv');p.add_argument('--output',required=True)
    p.add_argument('--nperm',type=int,default=N_PERM_DEFAULT)
    p.add_argument('--seed',type=int,default=SEED_DEFAULT)
    args=p.parse_args()
    out=run(args.oslo_dir,args.loci_tsv,args.nperm,args.seed,args.author_data_s2_csv)
    dest=Path(args.output);dest.parent.mkdir(exist_ok=True,parents=True)
    dest.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    x=[m for m in out['primary_analysis']['tested_models'] if m['model'] in ('LOCUS_03_HMGA2','LOCUS_07_ALX1','JOINT_03_07')]
    print(json.dumps({'status':out['status'],'nperm':args.nperm,'n_models':len(out['primary_analysis']['tested_models']),
                       'focal':x},ensure_ascii=False))

if __name__=='__main__': main()
