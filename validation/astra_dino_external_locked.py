#!/usr/bin/env python3
"""ASTRA DINO Ω. Freeze Oslo-only transfer model, then apply only to an independent paired cohort.
No external outcomes are read in freeze mode; no external information can tune this model.
Individual source data/model are not suitable for public GitHub; public report contains aggregates only.
"""
import argparse, csv, gzip, hashlib, json, math, sys
from pathlib import Path
from collections import Counter
import numpy as np

BASE=Path(__file__).resolve().parents[1]
_basecode=BASE/'validation' if (BASE/'validation'/'astra_dino_rubin_block_profiles.py').exists() else BASE/'baseline'/'validation'
sys.path.insert(0,str(_basecode))
from astra_dino_rubin2022_vcf_intersection import checked_originals
from astra_dino_data_s2_author_intersect import load_author_loci
from astra_dino_rubin_block_profiles import extract,group_indices

ASSEMBLY='GCA_902806625.1'
LOCUS={'HMGA2':3,'ALX1':7}
LOCK={'ridge_lambda':10.0,'genotype_pcs_per_block':2,'maf_train_min':0.05,
      'call_train_min':0.8,'minimum_independent_n':30,'minimum_clusters':5,
      'minimum_marker_coverage_each_block':0.8,'minimum_external_gt_call_rate':0.8,
      'permutation_count':20000,'permutation_seed':20261115,
      'primary_target':'log_beak_size','primary_model':'JOINT_HMGA2_ALX1',
      'primary_success':'paired_MSE_relative_gain_positive_and_within_cluster_perm_p_le_0.05',
      'baseline':'OSLO_TRAIN_MEAN','endpoints':['log_beak_size','log_beak_shape'],
      'secondary_correction':'Holm FWER over 6 model-outcome comparisons (exploratory)'}

class GateError(ValueError):pass

def sha(data):return hashlib.sha256(data).hexdigest()
def sha_file(path):
    d=hashlib.sha256()
    with Path(path).open('rb') as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b''):d.update(chunk)
    return d.hexdigest()

def model_samples(folder):
    with gzip.open(Path(folder)/'Prun64_3miss2mafNoZ_1.vcf.gz','rt') as fh:
        for line in fh:
            if line.startswith('#CHROM'):return line.rstrip('\n').split('\t')[9:]
    raise GateError('OSLO_VCF_HEADER_MISSING')

def source_alleles(folder, marker_positions):
    found={}; duplicates=set()
    with gzip.open(Path(folder)/'Prun64_3miss2mafNoZ_1.vcf.gz','rt') as fh:
        for s in fh:
            if s.startswith('#'):continue
            col=s.split('\t',5)
            if col[0].removeprefix('chr')!='1A':continue
            pos=int(col[1]);
            if pos not in marker_positions:continue
            if pos in found:duplicates.add(pos)
            found[pos]=(col[3],col[4])
    if duplicates:raise GateError('MULTIPLE_SOURCE_ALLELES_AT_POSITION')
    if set(found)!=set(marker_positions):raise GateError('TRAIN_VARIANT_UNRESOLVED')
    return found

def deterministic_pca(train_dose,n_pc=2):
    A=np.array(train_dose,dtype=float)
    means=np.nanmean(A,axis=0)
    A=np.where(np.isfinite(A),A,means)
    scales=np.sqrt(np.mean((A-means)**2,axis=0))
    if np.any(~np.isfinite(scales)) or np.any(scales<=1e-10):raise GateError('ZERO_VARIANCE_SNP')
    Z=(A-means)/scales
    U,S,V=np.linalg.svd(Z,full_matrices=False)
    if S[n_pc-1]<1e-8:raise GateError('RANK_DEFICIENT_PCA')
    load=V[:n_pc].T.copy()
    for j in range(n_pc):
        i=int(np.argmax(np.abs(load[:,j])))
        if load[i,j]<0:load[:,j]*=-1
    return means,scales,load,Z@load

def ridge_predictor(X,Y,lam=10):
    x_mean=np.mean(X,axis=0); y_mean=np.mean(Y,axis=0)
    beta=np.linalg.solve((X-x_mean).T@(X-x_mean)+lam*np.eye(X.shape[1]),
                         (X-x_mean).T@(Y-y_mean))
    intercept=y_mean-x_mean@beta
    return intercept,beta

def freeze(oslo,loci_path,private_model,public_manifest):
    p=Path(oslo);originals=checked_originals(p)
    loci, named, author_sha=load_author_loci(loci_path)
    if named!=LOCUS or len(loci)!=28:raise GateError('SOURCE_LOCI_INVALID')
    samples=model_samples(p)
    blockmarkers,counts,groups,Y,_=extract(p,loci)
    # Earlier Oslo auditor emits [shape, size]. External predictive protocol is [size, shape].
    Y=Y[:,[1,0]]
    if (counts[3],counts[7],len(blockmarkers[3]),len(blockmarkers[7]))!=(706,410,394,238):
        raise GateError('OSLO_FROZEN_COUNT_MISMATCH')
    ordered=[]
    for loc in [3,7]:ordered.extend(blockmarkers[loc])
    positions=[pos for pos,_ in ordered]
    alleles=source_alleles(p,set(positions))
    if len(set(positions))!=len(positions):raise GateError('DUPLICATE_FOCAL_POSITIONS')
    y_mean=np.mean(Y,axis=0)
    # Model is unconditional so population structure is *not* claimed controlled in transfer.
    components={};scores={}
    for gene,loc in LOCUS.items():
        markers=blockmarkers[loc]
        dose=np.column_stack([v for _,v in markers])
        means,scales,loads,pc=deterministic_pca(dose)
        components[gene]={'markers':[{'chrom':'1A','pos':int(pos),'ref':alleles[pos][0],
                                     'alt':alleles[pos][1],'mean':float(means[i]),
                                     'scale':float(scales[i]),'loadings':[float(v) for v in loads[i]]}
                                    for i,(pos,_) in enumerate(markers)]}
        scores[gene]=pc
    features={'HMGA2':scores['HMGA2'],'ALX1':scores['ALX1'],
              'JOINT_HMGA2_ALX1':np.column_stack((scores['HMGA2'],scores['ALX1']))}
    fitted={}
    for name,X in features.items():
        a,b=ridge_predictor(X,Y,LOCK['ridge_lambda'])
        fitted[name]={'intercept':a.tolist(),'beta':b.tolist()}
    training_id_hashes=sorted({sha(s.encode()) for s in samples})
    specimen_ids={s.split('_')[0] for s in samples if s.split('_')[0].isdigit()}
    training_specimen_hashes=sorted({sha(s.encode()) for s in specimen_ids})
    bundle={'schema':'astra_dino_oslo_frozen_transfer_v1','source_assembly':ASSEMBLY,
            'author_interval_sha256':author_sha,'oslo_originals_sha256':originals,
            'training_count':len(Y),'training_population_count':len(set(groups)),
            'training_mean_outcomes':y_mean.tolist(),
            'training_sample_id_hashes':training_id_hashes,
            'training_specimen_id_hashes':training_specimen_hashes,
            'lock':LOCK,'components':components,'trained_models':fitted,
            'traits_formula':['(log(length)+log(height)+log(width))/3','log(height/length)'],
            'note':'Frozen on Oslo only. No external features or phenotypes seen. Genotype PCs NOT phased haplotypes. Population structure not solved.'}
    dest=Path(private_model);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(bundle,sort_keys=True,separators=(',',':'))+'\n',encoding='utf8')
    public={'schema':'astra_dino_external_pre_registration_v1','status':'MODEL_FROZEN__EXTERNAL_COHORT_NOT_YET_VERIFIED',
            'private_model_sha256':sha_file(dest),'private_model_bytes':dest.stat().st_size,
            'source_assembly':ASSEMBLY,'transfer_script_sha256':sha_file(__file__),
            'baseline_train_script_sha256':sha_file(_basecode/'astra_dino_rubin_block_profiles.py'),
            'author_intervals_sha256':author_sha,
            'sample_count_oslo':len(Y),'population_count_oslo':len(set(groups)),
            'training_markers':{'HMGA2':394,'ALX1':238},'frozen_lock':LOCK,
            'exclusions':['OSLO_SAMPLES_AND_DUPLICATE_ACCESSIONS','NON_MATCHING_REFERENCE_ASSEMBLY',
                          'UNVERIFIED_SAMPLE_CROSSWALK','PHENOTYPE_ONLY_MUSEUM_SAMPLES',
                          'LESS_THAN_80_PERCENT_MARKER_COVERAGE', 'PHENOTYPE_IN_TRAINING']}
    Path(public_manifest).parent.mkdir(parents=True,exist_ok=True)
    Path(public_manifest).write_text(json.dumps(public,sort_keys=True,indent=2)+'\n',encoding='utf8')
    return public

def check_crosswalk(rows,samples,bundle):
    """Require exact join; reject overlap with Oslo and duplicated specimens."""
    if len(rows)<LOCK['minimum_independent_n']:raise GateError('EXTERNAL_N_TOO_SMALL')
    required={'sample_id','specimen_id','species','beak_length','beak_height','beak_width','validation_cluster'}
    if not rows or not required.issubset(rows[0]):raise GateError('MISSING_REQUIRED_PHENOTYPE_COLUMNS')
    ids=[r['sample_id'].strip() for r in rows]
    specimens=[r['specimen_id'].strip() for r in rows]
    if len(set(ids))!=len(ids) or any(not x for x in ids):raise GateError('DUPLICATE_OR_EMPTY_IDS')
    if len(set(specimens))!=len(specimens) or any(not x for x in specimens):raise GateError('DUPLICATE_OR_EMPTY_SPECIMEN_IDS')
    if not set(ids).issubset(set(samples)):raise GateError('GENOTYPE_PHENOTYPE_ID_NOT_MATCHED')
    if {sha(s.encode()) for s in ids}&set(bundle['training_sample_id_hashes']):
        raise GateError('OSLO_SAMPLE_LEAKAGE')
    if {sha(s.encode()) for s in specimens}&set(bundle['training_specimen_id_hashes']):
        raise GateError('OSLO_SPECIMEN_LEAKAGE')
    clusters=[r['validation_cluster'].strip() for r in rows]
    if len(set(clusters))<LOCK['minimum_clusters'] or any(not c for c in clusters):
        raise GateError('INSUFFICIENT_INDEPENDENT_CLUSTERS')
    if any(not r['species'].strip() for r in rows):raise GateError('MISSING_SPECIES')
    traits=[]
    for row in rows:
        try:v=np.array([float(row['beak_length']),float(row['beak_height']),float(row['beak_width'])])
        except (ValueError,KeyError):raise GateError('INVALID_PHENOTYPE')
        if not (np.isfinite(v).all() and (v>0).all()):raise GateError('INVALID_PHENOTYPE')
        L,H,W=v
        traits.append([(np.log(L)+np.log(H)+np.log(W))/3,np.log(H/L)])
    return ids,clusters,np.array(traits)

def build_external_predictors(vcf,phenotype_tsv,model,source_manifest):
    b=json.loads(Path(model).read_text())
    source=json.loads(Path(source_manifest).read_text())
    if source.get('assembly')!=ASSEMBLY:raise GateError('ASSEMBLY_MISMATCH')
    if source.get('dataset_doi') in (None,'','10.5061/dryad.3ffbg79w8'):
        raise GateError('EXTERNAL_SOURCE_NOT_INDEPENDENT')
    if not all(source.get(x) for x in ('source_url','id_crosswalk_evidence_url')):
        raise GateError('EXTERNAL_SOURCE_PROVENANCE_INCOMPLETE')
    if source.get('sample_level_genotype_phenotype_join_verified') is not True:
        raise GateError('EXTERNAL_CROSSWALK_UNVERIFIED')
    if source.get('specimens_disjoint_from_oslo_verified') is not True:
        raise GateError('OVERLAP_UNVERIFIED')
    with Path(phenotype_tsv).open(newline='',encoding='utf8') as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    # Never read any phenotype values before the source and crosswalk gates above.
    wanted={m['pos']:m for gene in ('HMGA2','ALX1') for m in b['components'][gene]['markers']}
    external_samples=None;variants={};seen=set();external_reference=None
    with gzip.open(vcf,'rt') if str(vcf).endswith('.gz') else open(vcf,encoding='utf8') as fh:
        for line in fh:
            if line.startswith('##reference='):
                external_reference=line.strip().split('=',1)[1]
                continue
            if line.startswith('##'):continue
            if line.startswith('#CHROM'):
                external_samples=line.rstrip('\n').split('\t')[9:];continue
            if line.startswith('#'):continue
            x=line.rstrip('\n').split('\t')
            if x[0].removeprefix('chr')!='1A':continue
            pos=int(x[1]);
            if pos not in wanted:continue
            if pos in seen:raise GateError('DUPLICATED_POSITIONS_EXTERNAL_VCF')
            seen.add(pos)
            m=wanted[pos]
            if x[3]!=m['ref'] or x[4]!=m['alt']:continue
            fmt=x[8].split(':')
            if 'GT' not in fmt:continue
            gtidx=fmt.index('GT');v=[]
            for data in x[9:]:
                d=data.split(':');gt=d[gtidx] if gtidx<len(d) else './.'
                a=gt.replace('|','/').split('/')
                v.append(sum(map(int,a)) if len(a)==2 and set(a)<=set('01') else np.nan)
            variants[pos]=np.array(v)
    if external_reference is None or not any(v in external_reference for v in (ASSEMBLY,'Camarhynchus_parvulus_V1.1','C_parvulus_sm.fa')):
        raise GateError('EXTERNAL_VCF_REFERENCE_UNVERIFIED')
    if external_samples is None or len(set(external_samples))!=len(external_samples):raise GateError('EXTERNAL_VCF_HEADER_INVALID')
    ids,clusters,Y=check_crosswalk(rows,external_samples,b)
    idx={s:i for i,s in enumerate(external_samples)};positions=[idx[x] for x in ids]
    PC={}
    for gene in ('HMGA2','ALX1'):
        markers=b['components'][gene]['markers']
        if len([m for m in markers if m['pos'] in variants])/len(markers)<LOCK['minimum_marker_coverage_each_block']:
            raise GateError('INSUFFICIENT_EXACT_VARIANT_COVERAGE_'+gene)
        z=[]
        for m in markers:
            v=variants.get(m['pos'])
            if v is None:v=np.full(len(external_samples),np.nan)
            w=v[positions]
            if m['pos'] in variants and np.isfinite(w).mean()<LOCK['minimum_external_gt_call_rate']:
                raise GateError('INSUFFICIENT_SAMPLE_CALL_RATE_AT_SNP')
            imputed=np.where(np.isfinite(w),w,m['mean'])
            z.append((imputed-m['mean'])/m['scale'])
        X=np.array(z).T;load=np.array([m['loadings'] for m in markers])
        PC[gene]=X@load
    X={'HMGA2':PC['HMGA2'],'ALX1':PC['ALX1'],
       'JOINT_HMGA2_ALX1':np.column_stack((PC['HMGA2'],PC['ALX1']))}
    P={name:np.array(b['trained_models'][name]['intercept'])+
              v@np.array(b['trained_models'][name]['beta']) for name,v in X.items()}
    return clusters,Y,P,{'external_n':len(ids),'clusters_count':len(set(clusters)),
                          'external_dataset_doi':source['dataset_doi'],'source_url':source.get('source_url')}

def assess(clusters,Y,P,meta,train_mean,seed=LOCK['permutation_seed'],nperm=LOCK['permutation_count']):
    """Permutations only within externally supplied biological/time strata.

    Fixed Oslo mean baseline, no refitting or threshold selection on external outcomes.
    The genotype model has no controls for kinship; so even a positive result
    would require an independent kinship-aware replication before causal claims.
    """
    if nperm<999:raise GateError('INSUFFICIENT_PERMUTATION_COUNT')
    y=np.asarray(Y,float);train_mean=np.asarray(train_mean,float)
    if y.shape[1]!=2 or train_mean.shape!=(2,):raise GateError('INVALID_TRAIT_DIMENSION')
    grouped={label:np.array([i for i,c in enumerate(clusters) if c==label],int)
             for label in sorted(set(clusters))}
    if not any(len(g)>1 for g in grouped.values()):raise GateError('NO_WITHIN_CLUSTER_PERMUTATIONS')
    sse0=np.sum((y-train_mean)**2,axis=0)
    if np.any(sse0<1e-10):raise GateError('BASELINE_VARIANCE_ZERO')
    modelnames=['HMGA2','ALX1','JOINT_HMGA2_ALX1']
    observed=np.array([(sse0-np.sum((y-P[name])**2,axis=0))/sse0 for name in modelnames])
    exceeded=np.zeros((3,2),int)
    rng=np.random.default_rng(seed)
    for _ in range(nperm):
        perm=np.arange(len(y))
        for ids in grouped.values():perm[ids]=rng.permutation(ids)
        yp=y[perm]
        sse0p=np.sum((yp-train_mean)**2,axis=0)
        test=np.array([(sse0p-np.sum((yp-P[name])**2,axis=0))/sse0p for name in modelnames])
        exceeded+=(test>=observed-1e-12)
    raw=(exceeded+1)/(nperm+1)
    # Holm across all 6 secondary tests, including the registered primary test.
    flat=raw.ravel();order=np.argsort(flat);corrected=np.zeros_like(flat)
    last=0
    for i,j in enumerate(order):
        last=max(last,(len(flat)-i)*flat[j]);corrected[j]=min(1,last)
    results=[]
    for i,name in enumerate(modelnames):
        results.append({'model':name,'size_mse_gain':round(float(observed[i,0]),7),
                        'shape_mse_gain':round(float(observed[i,1]),7),
                        'size_p_raw':round(float(raw[i,0]),7),
                        'shape_p_raw':round(float(raw[i,1]),7),
                        'size_p_holm6':round(float(corrected.reshape(3,2)[i,0]),7),
                        'shape_p_holm6':round(float(corrected.reshape(3,2)[i,1]),7)})
    primary=results[2]
    return {'schema':'astra_dino_external_validation_v1',
            'status':'PASS_EXTERNAL_EXECUTION__SUCCESS' if (primary['size_mse_gain']>0 and primary['size_p_raw']<=0.05)
                            else 'PASS_EXTERNAL_EXECUTION__PRIMARY_HYPOTHESIS_NOT_CONFIRMED',
            'primary_hypothesis_confirmed':bool(primary['size_mse_gain']>0 and primary['size_p_raw']<=0.05),
            'n_external_samples':int(len(y)),'n_independent_clusters':len(grouped),
            'n_permutations':nperm,'seed':seed,'source':meta,
            'training_only_baseline':train_mean.tolist(),'models':results,
            'note':'A PASS result is statistical predictive association, not biological causality or true haplotype phasing. Random within-cluster permutations need exchangeability and do not model bird kinship.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['freeze','validate'],required=True)
    p.add_argument('--oslo-dir');p.add_argument('--loci-tsv');p.add_argument('--model');p.add_argument('--public-manifest')
    p.add_argument('--external-vcf');p.add_argument('--phenotypes');p.add_argument('--provenance');p.add_argument('--preregistration')
    args=p.parse_args()
    if args.mode=='freeze':
        if not all([args.oslo_dir,args.loci_tsv,args.model,args.public_manifest]):p.error('freeze requires oslo-dir, loci-tsv, model and public-manifest')
        print(json.dumps(freeze(args.oslo_dir,args.loci_tsv,args.model,args.public_manifest),indent=2))
    else:
        if not all([args.model,args.external_vcf,args.phenotypes,args.provenance,args.preregistration]):p.error('validate requires model, external-vcf, phenotypes, provenance and preregistration')
        model_bytes=Path(args.model).read_bytes(); b=json.loads(model_bytes)
        frozen=json.loads(Path(args.preregistration).read_text())
        if sha(model_bytes)!=frozen.get('private_model_sha256') or b.get('lock')!=LOCK or \
           sha_file(__file__)!=frozen.get('transfer_script_sha256') or \
           sha_file(_basecode/'astra_dino_rubin_block_profiles.py')!=frozen.get('baseline_train_script_sha256'):
            raise GateError('FROZEN_MODEL_OR_PROTOCOL_TAMPERED')
        clusters,Y,P,meta=build_external_predictors(args.external_vcf,args.phenotypes,args.model,args.provenance)
        out=assess(clusters,Y,P,meta,b['training_mean_outcomes'])
        out['locked_model_sha256']=sha(model_bytes)
        out['external_file_digests']={'vcf_sha256':sha_file(args.external_vcf),
            'phenotypes_sha256':sha_file(args.phenotypes),
            'source_manifest_sha256':sha_file(args.provenance)}
        print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
