#!/usr/bin/env python3
"""ASTRA DINO Ω: adverse flanking-window, grouping and leave-population-out controls.

Runs on exactly the same source-hashed Dryad 2025 originals and Ensembl
GCA_902806625.1 chromosome 1A sequence as joint_real.py.
Flank comparisons are NOT independent negative loci: linkage may persist.
"""
import argparse
import gzip
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import astra_dino_alx1_hmga2_joint_real as a

def sensitivity(folder,reference_path,nperm):
    hashes=a.check_inputs(folder)
    ref=a.reference_sequence(reference_path)
    morph=a.rows(Path(folder)/'Morphometrics.txt','AccNo')
    pca=a.rows(Path(folder)/'pPCAeigen.txt','SampleID')
    d=a.parse_vcf(Path(folder)/'Prun64_3miss2mafNoZ_1.vcf.gz',ref,morph,pca)
    pairs=d['paired']
    scores={}
    qcs={}
    for gene in a.GENES:
        scores[gene],qc=a.gene_score(d['variants'][gene],len(pairs))
        qcs[gene]={'observed_variants':len(d['variants'][gene]),'markers_maf_ge_005':len(qc)}
    # Populate exact equal-width adjacent windows using the same VCF.
    regions={k:v for k,v in a.regions().items() if k not in a.GENES}
    flanks={k:[] for k in regions}
    with gzip.open(Path(folder)/'Prun64_3miss2mafNoZ_1.vcf.gz','rt') as f:
        for line in f:
            if line.startswith('#'):continue
            col=line.rstrip('\n').split('\t')
            if col[0]!='1A':continue
            pos=int(col[1])
            if not (len(col[3])==len(col[4])==1 and col[3] in 'ACGT' and col[4] in 'ACGT'):continue
            for name,(lo,hi) in regions.items():
                if lo<=pos<=hi:
                    flanks[name].append({'pos':pos,'dosages':[a.fields(col[9+x['index']],col[8]) for x in pairs]})
    for k,rows in flanks.items():
        scores[k],qc=a.gene_score(rows,len(pairs))
        qcs[k]={'observed_variants':len(rows),'markers_maf_ge_005':len(qc),
                'window_1based_inclusive':list(regions[k])}
    models={}
    combinations={'primary':['ALX1','HMGA2'],'left':['ALX1_LEFT','HMGA2_LEFT'],
                  'right':['ALX1_RIGHT','HMGA2_RIGHT'],'mixed':['ALX1_LEFT','HMGA2_RIGHT']}
    for name,(x,y) in combinations.items():
        models[name]=a.permutation_test(pairs,scores[x],scores[y],nperm,20261114)
    # Pre-specified alternate stratification (actual source Species).
    alternative=[dict(row,population=morph[row['AccNo']]['Species']) for row in pairs]
    species=a.permutation_test(alternative,scores['ALX1'],scores['HMGA2'],nperm,20261114)
    # Leave-one-population-out is stability only; it is not external validation.
    populations=sorted(set(row['population'] for row in pairs))
    lopo=[]
    for excluded in populations:
        indices=[i for i,row in enumerate(pairs) if row['population']!=excluded]
        sub=[pairs[i] for i in indices]
        groups=defaultdict(list)
        for i,row in enumerate(sub):groups[row['population']].append(i)
        phenotype=[math.log((row['Beak_length']*row['Beak_height']*row['Beak_width'])**(1./3.)) for row in sub]
        x=a.demean([scores['ALX1'][i] for i in indices],groups)
        z=a.demean([scores['HMGA2'][i] for i in indices],groups)
        m=a.r2(a.demean(phenotype,groups),x,z)
        lopo.append({'excluded_population':excluded,'n':len(sub),
                    'within_population_r2':round(m['within_population_r2'],8),
                    'coefficients':list(map(lambda v:round(v,8),m['coefficients']))})
    # An actual REF substitution is rejected, even with unchanged contig length.
    altered=bytearray(ref);at=33414363-1
    altered[at]=ord('A') if altered[at]!=ord('A') else ord('C')
    try:
        a.parse_vcf(Path(folder)/'Prun64_3miss2mafNoZ_1.vcf.gz',bytes(altered),morph,pca)
    except a.GateError as err:
        mutation={'status':'PASS_MUTATED_REF_REJECTED','failure_code':str(err)}
    else:
        raise a.GateError('FAIL_MUTATED_REFERENCE_ACCEPTED')
    return {
        'status':'PASS_EXECUTION_PARTIAL_SCIENTIFIC_INTERPRETATION',
        'sample_count':50,'assembly':a.ASSEMBLY,'original_file_hashes':hashes,
        'markers':qcs,'flanking_comparators_not_independent_negative_controls':True,
        'permutations':nperm,'seed':20261114,
        'comparative_models':models,'alternate_species_fixed_effects':species,
        'leave_one_population_out':lopo,'real_reference_mutant':mutation,
        'interpretation':'A stronger adjacent-window association does not prove gene-specificity. Flanking SNPs may be in LD with target loci. Neither model proves causal effects, clinical outcomes or fossil phenotype prediction.'
    }

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--originals',required=True)
    parser.add_argument('--reference-1a',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--permutations',type=int,default=10000)
    args=parser.parse_args()
    if args.permutations<100 or args.permutations>10000:raise SystemExit('FAIL_CLOSED: PERMUTATION_BOUNDS')
    report=sensitivity(args.originals,args.reference_1a,args.permutations)
    Path(args.output).write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'mutant':report['real_reference_mutant'],
        'size_fwer':{k:v['endpoints']['size_log_geometric_mean_3d']['familywise_empirical_p'] for k,v in report['comparative_models'].items()},
        'lopo_n':len(report['leave_one_population_out'])}))
