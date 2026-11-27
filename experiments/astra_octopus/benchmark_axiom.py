"""Synthetic, paired bounded-error benchmark. No physical independence claim."""
import argparse,json
from collections import Counter
import numpy as np
from axiom import *
SCENARIOS={
 'nominal':(.24,0,0,0), 'ordinary_artifact':(0,.24,0,0),
 'isolated_artifact':(0,0,.24,0), 'both_artifacts':(0,.24,.24,0),
 'late_change':(.24,0,0,.24), 'force_and_artifacts':(.24,.24,-.24,.24),
 'near_threshold':(.06,0,0,0), 'outside_model':(.24,0,0,0),
 'unmodelled_coherent':(0,0,0,0),
}
INITIAL=('passive','reference','reference_zero','primary_zero','isolated','late')
CHECKS=('artifact_check','isolation_check','late_isolated','reverse')

def case(name,seed):
    rng=np.random.default_rng(seed);f,c,d,t=SCENARIOS[name];sign=rng.choice([-1,1]);theta=np.array([f*sign,rng.choice([-.24,0,.24]),rng.uniform(-.2,.2),c*sign,d*sign,t*sign]);
    obs={k:(float(np.dot(m.row,theta)+rng.uniform(-.008,.008)),.01) for k,m in CATALOG.items()}
    if name=='outside_model':obs['late_isolated']=(obs['late_isolated'][0]+.5,.01)
    if name=='unmodelled_coherent':
        # An omitted artifact mimics physical force in every experiment, including checks.
        obs={k:(y+.24*sign*CATALOG[k].row[0],r) for k,(y,r) in obs.items()}
    initial={k:obs[k] for k in INITIAL};full={k:obs[k] for k in (*INITIAL,*CHECKS)}
    strict=audit(initial,worlds=(WORLDS[0],));before=audit(initial);after=audit(full)
    def label(r):return r['targets'].get('force',{}).get('label',r['status'])
    truth='all_refuted' if name=='outside_model' else 'present' if abs(f)>.06 else 'absent' if abs(f)<.06 else 'uncertain'
    flags={k:v for k,v in zip(('C','D','T'),(c,d,t))}
    coverage=all((v['interval'][0] is None or v['interval'][0]-1e-8<=theta[PARAMS.index(p)]) and (v['interval'][1] is None or theta[PARAMS.index(p)]<=v['interval'][1]+1e-8) for p,v in [(('F' if k=='force' else 'B'),x) for k,x in after['targets'].items()]) if after['status']=='compatible' else None
    return {'seed':seed,'truth':truth,'strict':label(strict),'before':label(before),'after':label(after),'assumptions':after['assumptions'],'expected_violations':[k for k,v in flags.items() if v], 'covered':coverage}

def bench(seeds=20,start=65000):
    rows={s:[case(s,i) for i in range(start,start+seeds)] for s in SCENARIOS};summary={}
    for s,rr in rows.items():
        summary[s]={k:dict(Counter(r[k] for r in rr)) for k in ('strict','before','after')}
        summary[s]['correct_after']=sum(r['after']==r['truth'] for r in rr)
        summary[s]['violations_correct']=sum(bool(r['assumptions']) and set(k for k,v in r['assumptions'].items() if v=='refuted')==set(r['expected_violations']) for r in rr)
        summary[s]['coverage']=sum(r['covered'] is True for r in rr)
    return {'seeds':seeds,'start':start,'summary':summary,'rows':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=20);p.add_argument('--start',type=int,default=65000);a=p.parse_args();print(json.dumps(bench(a.seeds,a.start),indent=2,sort_keys=True))
