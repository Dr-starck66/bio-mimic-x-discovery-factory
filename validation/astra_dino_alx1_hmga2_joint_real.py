#!/usr/bin/env python3
"""ASTRA DINO Ω: exact-assembly joint ALX1/HMGA2 audit; no causal inference.
Reference: Ensembl release 116 GCA_902806625.1, chromosome 1A.
Input originals: Lifjeld et al. 2025 / Dryad doi:10.5061/dryad.3ffbg79w8.
All coordinates are 1-based inclusive, gene bodies rather than published haplotypes.
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED = {
    'Morphometrics.txt': ('4722f565feeda8290d3985b4a65d9e0c4e91690270264cfc931d26f24cc51555', 5295),
    'pPCAeigen.txt': ('d615bd8dd3fd22091b971b20f18a49832d1f2afaf390a30ea3465f6a276b5bff', 6421),
    'Prun64_3miss2mafNoZ_1.vcf.gz': ('471db73a5eb65a8bb6af8f25872a5a2d0bc0115556203250f69eb61988163d34', 59719262),
}
ASSEMBLY='GCA_902806625.1'
CHROM_SIZE=72438334
CHROM_SHA='8f718d54d008f90f3d5075919a35a55354757d0b761d3a6313ae7b2772ed5803'
GENES={
 'ALX1':{'gene_id':'ENSCPVG00000017961','protein_id':'ENSCPVP00000027391.1','start':40877644,'end':40920855,
         'identity_to_Geospiza_ALX1':'326/328', 'annotation':'unnamed gene; orthology verified by 37 protein 14-mers and 326/328 amino acids'},
 'HMGA2':{'gene_id':'ENSCPVG00000006117','protein_id':'ENSCPVP00000008382.1','start':33408202,'end':33520236,
          'annotation':'named HMGA2 in Ensembl 116 GTF'}
}
class GateError(Exception): pass

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def check_inputs(folder):
    hashes={}
    for fn,(h,n) in EXPECTED.items():
        p=Path(folder)/fn
        if not p.is_file() or p.stat().st_size!=n or digest(p)!=h:
            raise GateError('ORIGINAL_SIZE_OR_SHA_MISMATCH:'+fn)
        hashes[fn]=h
    return hashes

def reference_sequence(path):
    with open(path,'rb') as f:
        first=f.readline().decode('ascii').strip()
        if not first.startswith('>1A dna_sm:primary_assembly primary_assembly:Camarhynchus_parvulus_V1.1:1A:1:72438334:1'):
            raise GateError('REFERENCE_HEADER_MISMATCH')
        seq=b''.join(l.strip() for l in f).upper()
    if len(seq)!=CHROM_SIZE or hashlib.sha256(seq).hexdigest()!=CHROM_SHA:
        raise GateError('CHROM_1A_SEQUENCE_SHA_MISMATCH')
    return seq

def rows(path,key):
    out={}
    with open(path,newline='',encoding='utf8') as f:
        r=csv.DictReader(f,delimiter='\t')
        if not r.fieldnames or key not in r.fieldnames:raise GateError('TABLE_KEY_MISSING:'+key)
        for x in r:
            k=x[key].strip()
            if not k or k in out:raise GateError('DUPLICATE_OR_EMPTY_KEY:'+key)
            out[k]=x
    return out

def checked_pairs(samples, morph, pca):
    if len(samples)!=64 or len(set(samples))!=64 or set(samples)!=set(pca):
        raise GateError('SAMPLE_HEADER_PCA_MISMATCH')
    pairs=[]
    for idx,s in enumerate(samples):
        match=re.fullmatch(r'(\d{6})_(?:S\d+|sub\d*)',s)
        if not match:continue  # 14 SRA accessions have no authorized phenotype join
        acc=match.group(1)
        if acc not in morph:raise GateError('MORPHOMETRY_MISSING:'+acc)
        row=morph[acc]
        v={}
        for k in ('Beak_length','Beak_height','Beak_width'):
            try:v[k]=float(row[k])
            except (ValueError,TypeError,KeyError):raise GateError('PHENOTYPE_INVALID:'+k)
            if not math.isfinite(v[k]) or v[k]<=0:raise GateError('PHENOTYPE_INVALID:'+k)
        if not pca[s].get('Population'):raise GateError('POPULATION_MISSING')
        pairs.append({'index':idx,'sample':s,'AccNo':acc,'population':pca[s]['Population'],**v})
    if len(pairs)!=50 or len({x['AccNo'] for x in pairs})!=50:
        raise GateError('CROSSWALK_50_UNIQUE_FAILED')
    return pairs

def fields(gt_field,format_field):
    keys=format_field.split(':')
    if 'GT' not in keys:return None
    i=keys.index('GT')
    parts=gt_field.split(':')
    if i>=len(parts):return None
    gt=parts[i].replace('|','/').split('/')
    if len(gt)!=2 or not all(x in ('0','1') for x in gt):return None
    return sum(int(x) for x in gt)

def regions():
    out={}
    for gene,g in GENES.items():
        a,b=g['start'],g['end'];n=b-a+1
        out[gene]=(a,b)
        out[gene+'_LEFT']=(a-n,a-1)
        out[gene+'_RIGHT']=(b+1,b+n)
    return out

def parse_vcf(path,ref,morph,pca):
    counts=Counter();ref_checked=0;ref_mismatch=0;shift_hits=0;total=0
    variants={x:[] for x in GENES};p=[];samples=[];ctg_len=None;reference_name=None
    iv=regions();paired=None
    with gzip.open(path,'rt') as f:
        for l in f:
            if l.startswith('##reference='):reference_name=l.strip().split('=',1)[1]
            if l.startswith('##contig=<ID=1A,'):
                z=re.search(r'length=(\d+)',l)
                if z:ctg_len=int(z.group(1))
            if l.startswith('#CHROM\t'):
                samples=l.rstrip('\n').split('\t')[9:]
                paired=checked_pairs(samples,morph,pca)
                continue
            if l.startswith('#'):continue
            if paired is None:raise GateError('VCF_SAMPLES_NOT_FOUND')
            parts=l.rstrip('\n').split('\t')
            if len(parts)!=9+len(samples):raise GateError('TRUNCATED_VARIANT_RECORD')
            total+=1
            if parts[0]!='1A':continue
            try:pos=int(parts[1])
            except ValueError:raise GateError('BAD_VCF_POSITION')
            vref=parts[3].upper().encode()
            if pos<1 or pos+len(vref)-1>len(ref):raise GateError('VCF_OUTSIDE_CHROM')
            ref_checked+=1
            if ref[pos-1:pos-1+len(vref)]!=vref:ref_mismatch+=1
            if ref[pos:pos+len(vref)]==vref:shift_hits+=1
            for region,(a,b) in iv.items():
                if a<=pos<=b:
                    counts[region]+=1
                    if region in GENES:
                        if len(vref)!=1 or len(parts[4])!=1 or vref.decode() not in 'ACGT' or parts[4] not in 'ACGT':continue
                        dosages=[fields(parts[9+x['index']],parts[8]) for x in paired]
                        variants[region].append({'pos':pos,'dosages':dosages})
    if reference_name!='file://C_parvulus_sm.fa':raise GateError('UNEXPECTED_VCF_REFERENCE_NAME')
    if ctg_len!=len(ref):raise GateError('CONTIG_1A_SIZE_MISMATCH')
    if total!=261754 or ref_checked!=21809:raise GateError('UNEXPECTED_RECORD_COUNTS')
    if ref_mismatch:raise GateError('VCF_REF_FASTA_MISMATCH:'+str(ref_mismatch))
    return {'total':total,'chrom_1a':ref_checked,'ref_mismatches':ref_mismatch,'plus_one_shift_ref_matches':shift_hits,
            'counts':dict(counts),'variants':variants,'paired':paired,'vcf_reference_header':reference_name}

def gene_score(snps,n):
    cols=[];qc=[]
    for snp in snps:
        observed=[float(z) for z in snp['dosages'] if z is not None]
        if len(observed)<int(0.8*n):continue
        mean=sum(observed)/len(observed)
        maf=min(mean/2,1-mean/2)
        if maf < .05:continue
        vals=[mean if z is None else float(z) for z in snp['dosages']]
        v=math.sqrt(sum((x-mean)**2 for x in vals)/n)
        if v<1e-10:continue
        cols.append([(x-mean)/v for x in vals])
        qc.append({'pos':snp['pos'],'maf':round(maf,6),'call_rate':round(len(observed)/n,6)})
    if len(cols)<2:raise GateError('INSUFFICIENT_POLYMORPHIC_LOCI')
    # Leading genotype PC, phenotype-blind. Power iteration on G=XXt.
    vec=[float((i%7)+1) for i in range(n)]
    vec=[v-sum(vec)/n for v in vec]
    for iteration in range(250):
        w=[0.]*n
        for col in cols:
            t=sum(x*y for x,y in zip(col,vec))
            for i in range(n):w[i]+=col[i]*t
        norm=math.sqrt(sum(x*x for x in w))
        if norm<1e-12:raise GateError('DEGENERATE_GENE_PC')
        w=[x/norm for x in w]
        if min(sum((w[i]-vec[i])**2 for i in range(n)),sum((w[i]+vec[i])**2 for i in range(n)))<1e-18:vec=w;break
        vec=w
    if vec[next(i for i,v in enumerate(vec) if abs(v)>1e-6)]<0:vec=[-x for x in vec]
    return vec,qc

def demean(a,groups):
    out=list(a)
    for ids in groups.values():
        avg=sum(a[i] for i in ids)/len(ids)
        for i in ids:out[i]-=avg
    return out

def r2(y,x,z):
    d11=sum(a*a for a in x);d12=sum(a*b for a,b in zip(x,z));d22=sum(b*b for b in z)
    det=d11*d22-d12*d12
    if det<1e-12:raise GateError('JOINT_MODEL_COLLINEAR')
    v1=sum(a*b for a,b in zip(x,y));v2=sum(a*b for a,b in zip(z,y))
    b1=(v1*d22-v2*d12)/det;b2=(v2*d11-v1*d12)/det
    denom=sum(k*k for k in y)
    if denom<1e-15:raise GateError('NO_WITHIN_POP_PHENOTYPE_VARIATION')
    score=(b1*v1+b2*v2)/denom
    return {'within_population_r2':max(0.0,min(1.0,score)),'coefficients':[b1,b2]}

def permutation_test(pairs,g1,g2,nperm=2000,seed=20261114):
    if len(pairs)!=50:raise GateError('N_50_REQUIRED')
    groups=defaultdict(list)
    for i,x in enumerate(pairs):groups[x['population']].append(i)
    # Prespecified descriptive endpoints: shape and geometric-mean beak size
    outcome={
     'shape_log_height_over_length':[math.log(x['Beak_height']/x['Beak_length']) for x in pairs],
     'size_log_geometric_mean_3d':[math.log((x['Beak_length']*x['Beak_height']*x['Beak_width'])**(1./3.)) for x in pairs]
    }
    x=demean(g1,groups);z=demean(g2,groups)
    obs={name:r2(demean(y,groups),x,z) for name,y in outcome.items()}
    max_obs=max(v['within_population_r2'] for v in obs.values())
    exceed={k:0 for k in outcome}; exceed_family={k:0 for k in outcome}
    rng=random.Random(seed);null_max=[]
    for it in range(nperm):
        vals={}
        # One shared within-population permutation across both phenotypes:
        # preserves individual-level shape/size correlation under the joint null.
        perm_idx=list(range(len(pairs)))
        for indices in groups.values():
            shuffled=list(indices);rng.shuffle(shuffled)
            for target,source in zip(indices,shuffled):perm_idx[target]=source
        for name,y in outcome.items():
            yp=[y[j] for j in perm_idx]
            vals[name]=r2(demean(yp,groups),x,z)['within_population_r2']
            if vals[name]>=obs[name]['within_population_r2']-1e-12:exceed[name]+=1
        maxi=max(vals.values());null_max.append(maxi)
        for k in outcome:
            if maxi>=obs[k]['within_population_r2']-1e-12:exceed_family[k]+=1
    return {'method':f'Genotype-only PC1 per locus; joint two-covariate OLS after 11-population demeaning; shared within-population permutation for both endpoints; two-outcome familywise max-R2',
            'exploratory_no_causal_claim':True,'population_group_sizes':dict(Counter(x['population'] for x in pairs)),
            'permutations':nperm,'seed':seed,'endpoints':{
                k:{'within_population_r2':round(v['within_population_r2'],8),
                   'coefficients_PC1_ALX1_HMGA2':[round(t,8) for t in v['coefficients']],
                   'empirical_p_global_null':(exceed[k]+1)/(nperm+1),
                   'familywise_empirical_p':(exceed_family[k]+1)/(nperm+1)} for k,v in obs.items()},
            'permuted_null_max_r2_p95':sorted(null_max)[int(0.95*len(null_max))-1],
            'limits':'No independent holdout; unadjusted for gene-wide LD or other genomic loci, environment, pedigree or developmental stage; 50 nonrandom individuals'}

def audit(folder,reference,nperm):
    hashes=check_inputs(folder)
    ref=reference_sequence(reference)
    morph=rows(Path(folder)/'Morphometrics.txt','AccNo')
    pca=rows(Path(folder)/'pPCAeigen.txt','SampleID')
    a=parse_vcf(Path(folder)/'Prun64_3miss2mafNoZ_1.vcf.gz',ref,morph,pca)
    x,qc1=gene_score(a['variants']['ALX1'],50)
    z,qc2=gene_score(a['variants']['HMGA2'],50)
    model=permutation_test(a['paired'],x,z,nperm)
    return {
      'status':'PARTIAL_SCIENTIFIC_EXPLORATORY','test_execution':'PASS',
      'assembly':ASSEMBLY,'annotation_source':'Ensembl release 116 GTF; ALX1 orthology verified by protein ENSCPVP00000027391.1 vs Geospiza RefSeq XP_005421635.1 (326/328 aa)',
      'dataset_doi':'10.5061/dryad.3ffbg79w8','source_sha256':hashes,'reference_chromosome_1a_sequence_sha256':CHROM_SHA,
      'reference_evidence':{'vcf_ref_matches_chromosome_1a':a['chrom_1a'],'mismatches':a['ref_mismatches'],
                            'shift_by_one_negative_control_matches':a['plus_one_shift_ref_matches'],
                            'vcf_local_reference_label':a['vcf_reference_header'],
                            'whole_1756_contig_fasta_identity':'UNVERIFIED'},
      'genes':GENES,'vcf_records':a['total'],'vcf_chromosome_1a_records':a['chrom_1a'],
      'variants_in_gene_bodies':{k:len(v) for k,v in a['variants'].items()},
      'flanking_windows_equal_width_counts':{k:v for k,v in a['counts'].items() if k not in GENES},
      'paired_individuals':len(a['paired']),'historical_sra_samples_without_authorized_crosswalk':14,
      'crosswalk_provenance':'Lifjeld email 2026-11-14 confirms sample ID matching for 50 newly sequenced genomes; independent per-specimen replication unavailable',
      'genotype_PC1_QC':{'ALX1':qc1,'HMGA2':qc2},
      'joint_exploratory_model':model,
      'scientific_conclusion':'SNP positions and exploratory associations only; no causal inference, no proven fossil prediction, no genome-wide multiple-testing inference'
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--originals',required=True);p.add_argument('--reference-1a',required=True)
    p.add_argument('--output',required=True);p.add_argument('--permutations',type=int,default=2000)
    o=p.parse_args()
    try:
        if not 100<=o.permutations<=10000:raise GateError('INVALID_PERMUTATION_COUNT')
        result=audit(o.originals,o.reference_1a,o.permutations)
        Path(o.output).write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
        print(json.dumps({'status':'PASS_EXECUTION_PARTIAL_SCIENCE','out':o.output,
                          'observed':result['joint_exploratory_model']['endpoints'],
                          'markers':{k:len(v) for k,v in result['genotype_PC1_QC'].items()},
                          'variant_counts':result['variants_in_gene_bodies']},ensure_ascii=False))
    except (GateError,OSError,ValueError,EOFError,KeyError,IndexError) as e:
        print(json.dumps({'status':'FAIL_CLOSED','error':str(e)}))
        raise SystemExit(2)
if __name__=='__main__':main()
