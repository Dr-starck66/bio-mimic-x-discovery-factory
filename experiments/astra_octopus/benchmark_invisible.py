"""Virtual prescribed-trajectory force response; no physical motion or permission claim."""
import argparse,json
from statistics import mean
import numpy as np
from invisible import *
SCENARIOS=('instantaneous','delay','memory_u','memory_x','hysteresis','latent_offset','delay+memory_x','white_hidden','switch_hidden')
N=220

def protocol(kind,phase=0.):
    t=np.arange(N)*DT
    if kind==0:x=.07*np.sin(2*t+phase);u=.12*np.sin(2.4*t+phase)
    elif kind==1:x=.25*np.sin(3*t+phase);u=.45*np.sign(np.sin(5*t+phase))
    elif kind==2:x=.25*(2/np.pi)*np.arcsin(np.sin(2.8*t+phase));u=.45*np.sin(3.2*t+phase)
    elif kind==3:x=.20*np.sin(1.7*t+phase)+.05*np.sin(6*t);u=.45*np.sign(np.sin(12*t+phase))
    elif kind==4:x=.23*np.sin(5*t+phase);u=.45*np.sin(1.8*t+phase)
    elif kind==5:x=.20*np.tanh(3*np.sin(2*t+phase));u=.45*np.sin(6*t+phase)
    elif kind==6:x=.24*np.sin(2.3*t+phase);u=.4*np.tanh(4*np.sin(1.7*t+phase))
    elif kind==7:x=.19*np.sin(3.7*t+phase)+.04*np.sin(7*t);u=.4*np.sin(8*t+phase)
    else:raise ValueError(kind)
    v=np.gradient(x,DT);return Trial(x,v,u,np.zeros_like(x))

def simulate(t,s,seed,trialseed):
    r=np.random.default_rng(seed);q=np.random.default_rng(trialseed);x,v,u=t.x,t.v,t.u
    y=r.uniform(.9,1.1)*u-r.uniform(.7,1.2)*x-r.uniform(.2,.4)*v+.12*np.sin(12*x)
    if s in ('delay','delay+memory_x'):y+=r.uniform(.6,.9)*history(x,v,u,'delay',int(r.choice(LAGS)))
    if s in ('memory_u',):y+=r.uniform(.6,.9)*history(x,v,u,'memory_u',float(r.choice(TAUS)))
    if s in ('memory_x','delay+memory_x'):y+=r.uniform(1.1,1.5)*history(x,v,u,'memory_x',float(r.choice(TAUS)))
    if s=='hysteresis':y+=r.uniform(1.4,1.8)*history(x,v,u,'hysteresis',float(r.choice(WIDTHS[:5])))
    if s=='latent_offset':y+=q.choice([-1,1])*q.uniform(.18,.36)
    if s=='white_hidden':y+=q.normal(0,.15,N)
    if s=='switch_hidden':y+=q.choice([-1,1])*.24*np.where(np.arange(N)<N//2,1,-1)
    return Trial(x,v,u,y+q.normal(0,.018,N))

def run(s,seed):
    def obs(k,p,j):return simulate(protocol(k,p),s,seed,seed*100+j)
    train=[obs(0,p,j) for j,p in enumerate((0,.7,1.4,2.1))]
    hold=[obs(k,p,50+j) for j,(k,p) in enumerate(((6,.4),(7,1.2),(2,2.3),(4,.9)))];initial=fit(train);out={}
    for strategy in ('fixed','adaptive'):
        data=train.copy();models=initial;pool=[(k,p) for k in range(1,6) for p in (0.,1.2)];chosen=[]
        for j in range(2):
            idx=select(models,[protocol(*e) for e in pool]) if strategy=='adaptive' else 0
            k,p=pool.pop(idx);chosen.append([k,p]);data.append(obs(k,p,20+j));models=fit(data)
        m=models[0];base=next(z for z in models if z.family=='instantaneous');out[strategy]={'model':m.describe(),'audit':audit(m,hold),'baseline':audit(base,hold),'chosen':chosen,'exact':m.family==s}
    return out

def benchmark(seeds,start):
    rows={s:[run(s,seed) for seed in range(start,start+seeds)] for s in SCENARIOS};summary={}
    for s,rr in rows.items():
        summary[s]={}
        for mode in ('fixed','adaptive'):
            z=[a[mode] for a in rr];summary[s][mode]={'correct':sum(a['exact'] and a['audit']['accepted'] for a in z),'accepted':sum(a['audit']['accepted'] for a in z),'rmse':mean(a['audit']['rmse'] for a in z),'baseline_rmse':mean(a['baseline']['rmse'] for a in z),'families':{f:sum(a['model']['family']==f for a in z) for f in sorted({a['model']['family'] for a in z})}}
    return {'seeds':seeds,'start':start,'summary':summary,'runs':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=10);p.add_argument('--start',type=int,default=11000);a=p.parse_args();print(json.dumps(benchmark(a.seeds,a.start),indent=2))
