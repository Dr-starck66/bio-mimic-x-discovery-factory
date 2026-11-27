import json,argparse
import numpy as np
from genesis import *
from discovery import fit,DT
from active_doubt import Permit
SCENARIOS=('linear','sine','tanh','gaussian','modulated','hidden_memory')
P=Permit(True,True,0.,.40,.08,3.,1.4)
GRID=[Experiment(x,v,a,k) for x in (-.28,-.14,0,.14,.28) for v in (-.07,.07) for a in (.3,.6) for k in ('balanced','bipolar')]
FIXED=(Experiment(-.23,-.07,.6,'balanced'),Experiment(.23,.07,.6,'bipolar'))
def plant(s,seed):
    r=np.random.default_rng(seed);c=r.uniform([.95,-1.2,-.45],[1.05,-.8,-.25]);k=r.uniform(22,34) if s=='sine' else r.uniform(8,16)
    return c,k
def simulate(s,c,k,e,seed):
    if not e.authorized(P):raise ValueError('not permitted')
    r=np.random.default_rng(seed);x,v=e.x0,e.v0;rows=[];memory=r.choice([-1.,1.])
    for u in e.signal():
        z={'linear':0.,'sine':.3*np.sin(k*x),'tanh':.35*np.tanh(k*x),'gaussian':.4*np.exp(-(k*x)**2),'modulated':2.8*v*np.sin(k*x),'hidden_memory':.23*memory}[s]
        a=c@[u,x,v]+z;rows.append((x+r.normal(0,.0003),v+r.normal(0,.0005),u,a+r.normal(0,.015)))
        v+=DT*a;x+=DT*v
    return np.array(rows)
def run(s,seed):
    c,k=plant(s,seed);r=np.random.default_rng(seed+100000)
    starts=np.linspace(-.19,.19,10)+r.uniform(-.012,.012,10)
    train=np.concatenate([simulate(s,c,k,Experiment(float(x),float(v),.3,'balanced'),seed*100+j) for j,(x,v) in enumerate(zip(starts,r.uniform(-.06,.06,10)))])
    hold=np.concatenate([simulate(s,c,k,e,seed*100+60+j) for j,e in enumerate([Experiment(-.26,-.06,.6,'bipolar'),Experiment(.25,.06,.6,'balanced'),Experiment(.09,-.07,.3,'bipolar'),Experiment(-.16,.07,.6,'balanced')])])
    fixed=np.vstack([train,*[simulate(s,c,k,e,seed*100+40+j) for j,e in enumerate(FIXED)]])
    sparse=fit(fixed)[0];models,n=search(fixed);best=models[0];initial,_=search(train)
    data=train.copy();chosen=[];candidates=GRID.copy();mod=initial;refuted=False
    for j in range(2):
        e=select_probe(mod,candidates,P)
        if e is None:break
        chosen.append(e.__dict__);candidates.remove(e);rows=simulate(s,c,k,e,seed*100+40+j);refuted|=not audit(initial[0],rows)['accepted'];data=np.vstack([data,rows]);mod,_=search(data)
    active=mod[0];truth={'sine':('sin','x','1'),'tanh':('tanh','x','1'),'gaussian':('gaussian','x','1'),'modulated':('sin','x','v')}.get(s)
    def report(m):
        a=m.atom;result=audit(m,hold);result.update(eq=m.equation(),atom=None if a is None else [a.op,a.arg,a.env],frequency=m.k,structure=(a is None if s=='linear' else (a is not None and (a.op,a.arg,a.env)==truth)),frequency_error=abs(m.k-k) if truth else None);return result
    return {'truth_frequency':k,'sparse':audit(sparse,hold),'fixed':report(best),'adaptive':report(active),'candidates':n,'chosen':chosen,'initial_refuted':refuted}
def benchmark(seeds,start):return {'seeds':seeds,'start':start,'results':{s:[run(s,seed) for seed in range(start,start+seeds)] for s in SCENARIOS}}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=10);p.add_argument('--start',type=int,default=7000);a=p.parse_args();print(json.dumps(benchmark(a.seeds,a.start),indent=2))
