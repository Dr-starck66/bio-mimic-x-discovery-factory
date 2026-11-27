#!/usr/bin/env python3
"""Reproducible exploratory sex-stratified lifespan analysis of DrugAge (stdlib only).
Data are published study-level percentage changes, not individual lifespans.
Not clinical evidence or proof of a new longevity intervention.
"""
import argparse, csv, hashlib, json, math, random
from collections import defaultdict
from pathlib import Path

KEY=('compound_name','species','strain','dosage','age_at_initiation','treatment_duration','pubmed_id')
NEEDED=KEY+('gender','avg_lifespan_change_percent')

def load(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(NEEDED).issubset(reader.fieldnames):
            raise ValueError('Incomplete DrugAge fields')
        return list(reader)

def pairs(rows):
    groups=defaultdict(lambda:defaultdict(list))
    for r in rows:
        if r.get('gender') not in ('Female','Male'): continue
        try: v=float(r['avg_lifespan_change_percent'])
        except (ValueError,TypeError): continue
        if not math.isfinite(v): continue
        groups[tuple(r[k] for k in KEY)][r['gender']].append(v)
    answer=[]
    for key, sexes in groups.items():
        if not sexes['Female'] or not sexes['Male']: continue
        f=sum(sexes['Female'])/len(sexes['Female'])
        m=sum(sexes['Male'])/len(sexes['Male'])
        answer.append(dict(zip(KEY,key), female_percent=f,male_percent=m,
                         delta_female_minus_male=f-m, n_female=len(sexes['Female']),n_male=len(sexes['Male'])))
    return sorted(answer,key=lambda x:tuple(x[k] for k in KEY))

def studies(rows):
    grouped=defaultdict(list)
    for row in rows:
        if not row['pubmed_id']: continue
        grouped[row['pubmed_id']].append(row['delta_female_minus_male'])
    return {k:sum(v)/len(v) for k,v in sorted(grouped.items())}

def audit(rows,seed=20261118,n_perm=20000,n_boot=10000):
    ss=list(studies(rows).values())
    if not ss: return {'status':'UNVERIFIED_NO_PUBMED'}
    n=len(ss); obs=sum(ss)/n; rnd=random.Random(seed)
    extreme=0
    for _ in range(n_perm):
        null=sum(v if rnd.getrandbits(1) else -v for v in ss)/n
        extreme+=abs(null)+1e-12>=abs(obs)
    boots=sorted(sum(ss[rnd.randrange(n)] for _ in range(n))/n for _ in range(n_boot))
    return {'status':'EXPLORATORY','matched_conditions':len(rows),'distinct_pubmed':n,
            'mean_study_delta_percentage_points':obs,
            'mean_matched_row_delta_percentage_points':sum(x['delta_female_minus_male'] for x in rows)/len(rows),
            'n_studies_female_higher':sum(v>0 for v in ss),'n_studies_male_higher':sum(v<0 for v in ss),
            'p_two_sided_study_sign_flip':(extreme+1)/(n_perm+1),
            'bootstrap_95pct_CI_over_study_means':[boots[int(.025*n_boot)],boots[int(.975*n_boot)]],
            'warning':'This is study-level sampling variation, not an animal-level lifespan CI'}

def bh(ps):
    n=len(ps);res=[0]*n;prev=1.0
    for rank,index in reversed(list(enumerate(sorted(range(n),key=lambda j:ps[j]),1))):
        prev=min(prev,ps[index]*n/rank);res[index]=prev
    return res

def run(rows,n_perm=20000,n_boot=10000):
    pp=pairs(rows)
    out={'source_rows':len(rows),'matched_conditions':len(pp),'distinct_pubmed':len(studies(pp)),
         'all_species':audit(pp,n_perm=n_perm,n_boot=n_boot),'species':[],'mouse_repeated_compounds':[],
         'limitations':['Publication/selection bias: DrugAge includes curated longevity interventions',
         'Experimental animal counts, survival curves, and effect variances unavailable',
         'No causal inference, no human lifespan implication, no quantum advantage',
         'Publication identifier groups multiple experimental conditions; not equivalent to study replication']}
    for sp in sorted({x['species'] for x in pp}):
        subset=[x for x in pp if x['species']==sp]
        if len(studies(subset))<5: continue
        out['species'].append({'species':sp,**audit(subset,n_perm=n_perm,n_boot=n_boot)})
    qs=bh([x['p_two_sided_study_sign_flip'] for x in out['species']])
    for x,q in zip(out['species'],qs):x['BH_FDR_q_exploratory']=q
    cm=defaultdict(list)
    for x in pp:
        if x['species']=='Mus musculus': cm[x['compound_name']].append(x)
    for drug,c in cm.items():
        if len(studies(c))<2: continue
        ss=studies(c)
        out['mouse_repeated_compounds'].append({'compound':drug,'matched_conditions':len(c),
         'distinct_pubmed':len(ss),'average_study_delta_percentage_points':sum(ss.values())/len(ss),
         'per_pubmed':ss,'all_studies_male_higher':all(v<0 for v in ss.values())})
    out['mouse_repeated_compounds'].sort(key=lambda x:(-x['distinct_pubmed'],x['compound']))
    return out

def main():
    a=argparse.ArgumentParser();a.add_argument('csv',type=Path);a.add_argument('--output',type=Path,default=Path('sex_audit.json'))
    a.add_argument('--permutations',type=int,default=20000);a.add_argument('--bootstraps',type=int,default=10000)
    args=a.parse_args();assert args.permutations>=100 and args.bootstraps>=100
    result=run(load(args.csv),args.permutations,args.bootstraps)
    result['source_sha256']=hashlib.sha256(args.csv.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'source_rows':result['source_rows'],'matched_conditions':result['matched_conditions'],
     'distinct_pubmed':result['distinct_pubmed'],'all':result['all_species'],
     'species':[(r['species'],r['p_two_sided_study_sign_flip'],r['BH_FDR_q_exploratory']) for r in result['species']]},ensure_ascii=False))

if __name__=='__main__':main()