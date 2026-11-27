#!/usr/bin/env python3
"""SYNTHETIC adversarial fixture. Never qualifies as biological external evidence."""
from pathlib import Path
import json,csv,gzip,numpy as np
root=Path(__file__).resolve().parents[1]
b=json.loads((root/'private'/'frozen_oslo_transfer_v1.json').read_text())
sim=root/'tests'/'synthetic_only';sim.mkdir(exist_ok=True)
n=30; rng=np.random.default_rng(83)
samples=[f'SYNTHETIC_EXTERNAL_{x:04d}' for x in range(n)]
with gzip.open(sim/'mock_external.vcf.gz','wt') as f:
 f.write('##fileformat=VCFv4.2\n##reference=GCA_902806625.1\n')
 f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t'+'\t'.join(samples)+'\n')
 markers=[m for g in ('HMGA2','ALX1') for m in b['components'][g]['markers']]
 for m in sorted(markers,key=lambda x:x['pos']):
  freq=min(.95,max(.05,m['mean']/2))
  d=rng.binomial(2,freq,size=n)
  gts={0:'0/0',1:'0/1',2:'1/1'}
  f.write('\t'.join(['1A',str(m['pos']),'.',m['ref'],m['alt'],'.','PASS','.','GT']+[gts[i] for i in d])+'\n')
with (sim/'mock_pheno.tsv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['sample_id','specimen_id','species','beak_length','beak_height','beak_width','validation_cluster'],delimiter='\t');w.writeheader()
 for i,s in enumerate(samples):w.writerow({'sample_id':s,'specimen_id':f'MOCK_{i:04d}','species':'SYNTHETIC_ONLY',
  'beak_length':10+rng.normal(), 'beak_height':5+rng.normal(scale=.5),
  'beak_width':3+rng.normal(scale=.2),'validation_cluster':f'mock_group_{i//6}'})
(sim/'mock_source.json').write_text(json.dumps({'assembly':'GCA_902806625.1','dataset_doi':'10.0000/synthetic-fixture-not-a-real-doi',
 'source_url':'https://example.org/synthetic-fixture-only','id_crosswalk_evidence_url':'https://example.org/synthetic-crosswalk-only',
 'sample_level_genotype_phenotype_join_verified':True,'specimens_disjoint_from_oslo_verified':True}))
print(json.dumps({'fixture':'SYNTHETIC_ONLY','n':n,'markers':len(markers)}))
