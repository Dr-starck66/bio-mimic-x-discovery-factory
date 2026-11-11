#!/usr/bin/env python3
"""Fail-closed GEO DNAm/RNA metadata matching; no same-aliquot inference."""
import argparse,csv,gzip,hashlib,json,re
from pathlib import Path
def read_matrix(path):
    opener=gzip.open if str(path).endswith('.gz') else open
    tags={}
    with opener(path,'rt',encoding='utf-8',errors='replace') as f:
        for line in f:
            if line.startswith('!Sample_'):
                row=next(csv.reader([line.rstrip('\n')],delimiter='\t',quotechar='"'))
                tags[row[0]]=row[1:]
    ids=tags.get('!Sample_geo_accession',[]);titles=tags.get('!Sample_title',[])
    if not ids or len(ids)!=len(titles):raise ValueError('GEO sample accessions/titles absent or unequal')
    if len(set(ids))!=len(ids):raise ValueError('duplicate GSM')
    return [{'gsm':a,'title':b} for a,b in zip(ids,titles)]
def parse_human(title):
    t=title.replace('Methylation_','')
    m=re.fullmatch(r'(HC\d+|SURF1_\d+)_sp(\d+)_(?:Normal|SURF1_Mutation)_(.+)_ox(\d+)_p(\d+)',t,re.I)
    if not m:return None
    donor,series,treatment,oxygen,passage=m.groups()
    return {'donor':donor,'series':series,'treatment':treatment,'oxygen':oxygen,'passage':int(passage)}
def audit(a,b,parser=parse_human):
    def index(samples):
        out={};unparsed=[];dups=[]
        for s in samples:
            key=parser(s['title'])
            if key is None:unparsed.append(s);continue
            k=tuple(sorted(key.items()))
            if k in out:dups.append((out[k]['gsm'],s['gsm'],key))
            else:out[k]=s
        return out,unparsed,dups
    ai,au,ad=index(a);bi,bu,bd=index(b)
    ambiguous={tuple(sorted(key.items())) for _,_,key in ad+bd}
    shared=sorted((set(ai)&set(bi))-ambiguous)
    pairs=[{'dnam_gsm':ai[k]['gsm'],'rna_gsm':bi[k]['gsm'],'key':dict(k),'pair_level':'matched_metadata_only_NOT_same_aliquot'} for k in shared]
    return {'status':'PARTIAL_METADATA_MATCH_NOT_BIOLOGICAL_REPLICATION' if pairs else 'UNVERIFIED_NO_EXACT_METADATA_PAIRS',
      'n_dnam':len(a),'n_rna':len(b),'n_exact_metadata_pairs':len(pairs),'pairs':pairs,
      'unparsed_dnam':au,'unparsed_rna':bu,'duplicates_dnam':ad,'duplicates_rna':bd,
      'unmatched_dnam':len(ai)-len(shared),'unmatched_rna':len(bi)-len(shared),
      'same_aliquot':'UNVERIFIED','donor_biological_replicates':'UNVERIFIED','dnam_rna_value_analysis':'NOT_RUN'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--dnam',required=True);p.add_argument('--rna',required=True);p.add_argument('--out',required=True);args=p.parse_args()
    result=audit(read_matrix(args.dnam),read_matrix(args.rna))
    result['source_sha256']={x:hashlib.sha256(Path(x).read_bytes()).hexdigest() for x in (args.dnam,args.rna)}
    Path(args.out).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k.startswith('n_') or k=='status'}))
if __name__=='__main__':main()
