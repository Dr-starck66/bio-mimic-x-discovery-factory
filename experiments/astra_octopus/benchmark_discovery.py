"""Independent seed/trajectory benchmark; ground truth used only by simulator and scorer."""
import argparse,json
from collections import Counter
from statistics import mean
import numpy as np
from discovery import *
SCENARIOS=('linear','mild_gain','cubic','quadratic','drag','interaction','mixed','hidden_sine')
TRUTH={'linear':(1,2,3),'mild_gain':(1,2,3),'cubic':(1,2,3,5),'quadratic':(1,2,3,4),'drag':(1,2,3,6),'interaction':(1,2,3,8),'mixed':(1,2,3,5,8)}
P=Permit(True,True,0.,.40,.08,3.,1.4)
GRID=[Experiment(x,v,a,k) for x in (-.28,-.15,0.,.15,.28) for v in (-.07,.07) for a in (.3,.6) for k in ('balanced','bipolar')]
FIXED=(Experiment(.15,.07,.6,'balanced'),Experiment(-.15,-.07,.6,'bipolar'))

def plant(s,seed):
    rng=np.random.default_rng(seed); c=np.zeros(9);c[1]=rng.uniform(.95,1.05)*(.8 if s=='mild_gain' else 1);c[2]=-rng.uniform(.8,1.2);c[3]=-rng.uniform(.25,.45)
    if s in ('cubic','mixed'):c[5]=-rng.uniform(7,11)
    if s=='quadratic':c[4]=rng.uniform(2.5,4)
    if s=='drag':c[6]=-rng.uniform(2,3)
    if s in ('interaction','mixed'):c[8]=rng.uniform(1,1.5)
    return c

def simulate(s,c,e,seed):
    if not e.authorized(P):raise ValueError('unauthorized')
    rng=np.random.default_rng(seed); x,v=e.x0,e.v0; rows=[];mx=mv=ma=0.
    for u in e.signal():
        a=float(c[0]+c[1]*u+c[2]*x+c[3]*v+c[4]*x*x+c[5]*x**3+c[6]*v*abs(v)+c[7]*u*abs(u)+c[8]*x*u)+(0.3*np.sin(29*x) if s=='hidden_sine' else 0.)
        rows.append((x+rng.normal(0,.0003),v+rng.normal(0,.0005),u,a+rng.normal(0,.015)))
        v+=DT*a;x+=DT*v;mx=max(mx,abs(x-e.x0));mv=max(mv,abs(v));ma=max(ma,abs(a))
    return np.array(rows), (mx,mv,ma)

def run(s,seed):
    c=plant(s,seed); rng=np.random.default_rng(seed+100000)
    train=np.concatenate([simulate(s,c,Experiment(float(x),float(v),(.2 if j%2 else .3),'balanced'),seed*100+j)[0] for j,(x,v) in enumerate(zip(rng.uniform(-.045,.045,12),rng.uniform(-.05,.05,12)))])
    initial=fit(train)
    # Test data entirely separate, same for all policies, not used in fit or experiment selection.
    hold=np.concatenate([simulate(s,c,e,seed*100+60+j)[0] for j,e in enumerate([Experiment(-.26,-.06,.6,'bipolar'),Experiment(.24,.06,.6,'balanced'),Experiment(.1,-.07,.3,'bipolar'),Experiment(-.18,.07,.6,'balanced')])])
    out={};bounds=[]
    for name in ('active','fixed','random'):
        data=train.copy();models=initial;available=GRID.copy();chosen=[];refuted=False
        for j in range(2):
            if name=='active':e,_=choose(models,available,P)
            elif name=='fixed':e=FIXED[j]
            else:e=available[int(rng.integers(len(available))) ]
            available.remove(e);chosen.append(e.__dict__)
            probe,b=simulate(s,c,e,seed*100+40+j);bounds.append(b)
            refuted |= not audit(initial[0],probe)['accepted']
            data=np.vstack((data,probe));models=fit(data)
        post=models[0];test=audit(post,hold)
        out[name]={'initial_refuted':refuted,'test_accepted':test['accepted'],'test_rmse':test['rmse'],'support':list(post.support),'support_exact':set(post.support)==set(TRUTH.get(s,())),'estimated_gain':float(post.coefficients[1]),'gain_error':abs(float(post.coefficients[1]-c[1])),'chosen':chosen,'equation':post.equation(),'coefficient_error':float(np.linalg.norm((post.coefficients-c)*SCALES))}
    return {'baseline':audit(linear(train),hold),'initial':audit(initial[0],hold),'truth':c.tolist(),'modes':out,'bounds':np.max(bounds,axis=0).tolist()}

def benchmark(seeds,start):
    raw={s:[run(s,seed) for seed in range(start,start+seeds)] for s in SCENARIOS}; summary={}
    for s,runs in raw.items():
        summary[s]={'initial_rmse':mean(r['initial']['rmse'] for r in runs),'linear_rmse':mean(r['baseline']['rmse'] for r in runs)}
        for name in ('active','fixed','random'):
            vals=[r['modes'][name] for r in runs];summary[s][name]={k:mean(r[k] for r in vals) for k in ('initial_refuted','test_accepted','test_rmse','support_exact','gain_error','coefficient_error')};summary[s][name]['example']=vals[0]['equation']
    bounds=np.max([r['bounds'] for runs in raw.values() for r in runs],axis=0).tolist()
    return {'seeds':seeds,'start':start,'summary':summary,'bounds':bounds,'raw':raw}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=20);p.add_argument('--start',type=int,default=5000);a=p.parse_args();print(json.dumps(benchmark(a.seeds,a.start),indent=2))
