import json,argparse
import numpy as np
from paradigm import *
SCENARIOS=('nominal','interaction','nonlinear','memory','two_latents','random_hidden','outside_grammar','coherent_alias')

def context(seed,kind=0):
    r=np.random.default_rng(seed);t=np.arange(80)/20
    if kind==0:return np.column_stack([.32*np.sin(2*t+r.uniform(0,6)),.32*np.cos(2.4*t+r.uniform(0,6))])
    if kind==1:return np.column_stack([np.sin(3*t+r.uniform(0,6)),np.sign(np.sin(5*t+r.uniform(0,6)))])
    if kind==2:return np.column_stack([.8*np.sign(np.sin(2*t+r.uniform(0,6))),np.sin(7*t+r.uniform(0,6))])
    if kind==3:return r.uniform(-1,1,(80,2))
    if kind==4:return np.column_stack([np.sin(6*t+r.uniform(0,6)),np.cos(3*t+r.uniform(0,6))])
    return np.column_stack([np.sin(1.7*t+r.uniform(0,6)),np.sin(9*t+r.uniform(0,6))])

def simulate(s,seed,x,noise_seed):
    r=np.random.default_rng(seed);q=np.random.default_rng(noise_seed);f=grammar(x);a,b=x.T
    theta=np.column_stack([.3*a,.2*b,.1*np.ones(len(a)),.12*a*b,.15*b,.1*a]);y=theta@A.T
    # Simulator loadings are generated independently from a random seed; never supplied to learner.
    w=P@r.normal(size=len(A));w=w/np.linalg.norm(w);v=P@r.normal(size=len(A));v-=w*(v@w);v/=np.linalg.norm(v)
    if s=='interaction':y+=np.outer(.9*f['x*u'],w)
    if s=='nonlinear':y+=np.outer(.7*f['sin(3*x)'],w)
    if s=='memory':y+=np.outer(.9*f['memory(0.65)'],w)
    if s=='two_latents':y+=np.outer(.8*f['x*u'],w)+np.outer(.7*f['lag(u)'],v)
    if s=='random_hidden':y+=np.outer(q.normal(0,.35,len(a)),w)
    if s=='outside_grammar':y+=np.outer(.7*np.sin(19*a+11*b),w)
    if s=='coherent_alias':y+=np.outer(.5*f['x*u'],A[:,0])
    return Trial(x,y+q.normal(0,.015,y.shape))

def run(s,seed):
    def obs(k,j):return simulate(s,seed,context(seed*100+j,k),seed*100+j+900000)
    train=[obs(0,j) for j in range(3)];hold=[obs(k,50+j) for j,k in enumerate((2,3,4,5))]; initial=fit(train)
    out={}
    for strategy in ('adaptive','fixed','random'):
        data=train.copy();pool=[(k,20+j) for j,k in enumerate((1,2,3,4,5))];chosen=[];m=initial
        rng=np.random.default_rng(seed+80000)
        for j in range(2):
            idx=choose(m,[context(seed*100+i,k) for k,i in pool]) if strategy=='adaptive' else 0 if strategy=='fixed' else int(rng.integers(len(pool)))
            k,i=pool.pop(idx);chosen.append(k);data.append(obs(k,i));m=fit(data)
        out[strategy]=diagnose(data,hold);out[strategy]['chosen']=chosen
    return out

def bench(seeds,start):
    rows={s:[run(s,i) for i in range(start,start+seeds)] for s in SCENARIOS};summary={}
    for s,rr in rows.items():
        summary[s]={}
        for m in ('adaptive','fixed','random'):
            z=[r[m] for r in rr];summary[s][m]={'labels':{k:sum(a['label']==k for a in z) for k in ('no_residual_detected','candidate_extension','unexplained')},'rmse':float(np.mean([a['candidate']['rmse'] for a in z])),'baseline_rmse':float(np.mean([a['baseline']['rmse'] for a in z])),'structure':sum(set(a['terms'])==set({'nominal':[],'interaction':['x*u'],'nonlinear':['sin(3*x)'],'memory':['memory(0.65)'],'two_latents':['x*u','lag(u)']}.get(s,[])) and a['rank']==(2 if s=='two_latents' else 0 if s=='nominal' else 1) for a in z)}
    return {'seeds':seeds,'start':start,'summary':summary,'rows':rows,'alias_certificate':alias_certificate()}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=20);p.add_argument('--start',type=int,default=74000);a=p.parse_args();print(json.dumps(bench(a.seeds,a.start),indent=2,sort_keys=True))
