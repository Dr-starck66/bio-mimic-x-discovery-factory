"""Paired synthetic experiment summaries with independently drawn nuisance bias.
Reuse INVISIBLE's prediction interface with a supplied clean model; no target calibration or response leakage.
"""
import argparse,json
from collections import Counter
import numpy as np
from causal import *
from invisible import Trial, Model, CAL, DT

SCENARIOS=('neither','force','bias','both','reference_biased','weak_force','no_external','no_motion','passive_only','intervention_violation','coherent_deception','nonstationary')
P=Permit(True,True,0.,.40,.08,3.,1.4)

def case(s,seed,repeat=0):
    rng=np.random.default_rng(seed); F=rng.choice([-1,1])*rng.uniform(.16,.36); B=rng.choice([-1,1])*rng.uniform(.16,.36); R=rng.uniform(-.04,.04)
    if s in ('neither','bias','reference_biased','coherent_deception'):F=0.
    if s in ('neither','force','reference_biased','weak_force','coherent_deception'):B=0.
    if s=='reference_biased':R=.3
    if s=='weak_force':F=.06
    truth='both' if F and B else 'force' if F else 'bias' if B else 'neither'
    external=s not in ('no_external','passive_only');permit=P if s not in ('no_motion','passive_only') else Permit(False,True,0.,.40,.08,3.,1.4)
    # Prescribed virtual rig: clean response model supplied by trusted calibration, not learned from target data.
    t=np.arange(CAL+N)*DT;x=.15*np.sin(3*t);v=.45*np.cos(3*t);u=.4*np.sin(5*t)
    model=Model((0,1,2,3),np.array([0.,1.,-.9,-.3]),True,0.)
    template=Trial(x,v,u,np.zeros_like(x));base=model.predict(template,calibrate=False)
    obs={}
    for name,a in ACTIONS.items():
        offset=np.dot(a.row,[F,B,R]);q=np.random.default_rng(seed*101+list(ACTIONS).index(name)+repeat*10000019)
        if s=='intervention_violation' and name=='primary_zero':offset+=.27
        if s=='coherent_deception':offset+=.24*a.row[0] # exactly mimics physical force on ALL actions
        if s=='nonstationary':offset+=q.choice([-1,1])*.28
        trial=Trial(x,v,u,base+offset+q.normal(0,.02,len(x)))
        obs[name]=(trial.y-base)[CAL:]
    return truth,obs,permit,external,F,B

def run(s,seed,policy,budget=5):
    truth,obs,p,external,F,B=case(s,seed);names=['passive'];cost=0
    if policy=='adaptive':
        while (n:=choose(names,p,external,budget-cost)) is not None:
            names.append(n);cost+=ACTIONS[n].cost
    elif policy!='passive':
        order=('reference','reference_zero','primary_zero','reverse') if policy=='fixed_reference' else ('primary_zero','reverse','reference','reference_zero')
        for n in order:
            if eligible(n,p,external) and cost+ACTIONS[n].cost<=budget:names.append(n);cost+=ACTIONS[n].cost
            if redundant(names):break
    r=infer({n:obs[n] for n in names});r.update(cost=cost,truth=truth,force=F,bias=B,seed=seed,motion=sum(ACTIONS[n].motion for n in names));return r

def benchmark(seeds,start):
    out={};raw={}
    for s in SCENARIOS:
        raw[s]={};out[s]={}
        for policy in ('passive','fixed_reference','fixed_motion','adaptive'):
            rr=[run(s,i,policy) for i in range(start,start+seeds)];raw[s][policy]=rr
            out[s][policy]={'verdicts':dict(Counter(r['verdict'] for r in rr)),'correct':sum(r['verdict']==r['truth'] for r in rr),'mean_cost':float(np.mean([r['cost'] for r in rr])),'mean_motion':float(np.mean([r['motion'] for r in rr])),'interval_coverage':int(sum(all(r['intervals'].get(k,[-np.inf,np.inf])[0]<=r[k]<=r['intervals'].get(k,[-np.inf,np.inf])[1] for k in ('force','bias')) for r in rr))}
    return {'seeds':seeds,'start':start,'summary':out,'runs':raw}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=100);p.add_argument('--start',type=int,default=23000);a=p.parse_args();print(json.dumps(benchmark(a.seeds,a.start),indent=2))
