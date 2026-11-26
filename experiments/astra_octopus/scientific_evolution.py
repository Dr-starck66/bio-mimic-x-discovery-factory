"""Bounded strategy evolution; no self-modifying source or automatic deployment."""
from dataclasses import dataclass, asdict, replace
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from metascience import features, split, rmse

@dataclass(frozen=True)
class Policy:
    rolling: bool=False
    conservative: bool=False
    refit: bool=False
    expanded: bool=False

PARENT=Policy()

def mutations(parent=PARENT):
    fields=list(asdict(parent)); out={parent}
    for mask in range(1,1<<len(fields)):
        out.add(replace(parent,**{k:not getattr(parent,k) for i,k in enumerate(fields) if mask&(1<<i)}))
    return sorted(out,key=lambda p:tuple(asdict(p).values()))

def model_features(X,tr,temporal,expanded):
    f=features(X,tr,temporal)
    if expanded and temporal:
        # One-step forecasting only, all inputs at t-1 or earlier.
        z=X[:,0];lags=[np.r_[np.zeros(k),z[:-k]] for k in (1,2,3,4,5,7,10,11,12,15)]
        f['expanded_lags']=np.column_stack([f['linear'],*lags])
    return f

def candidates(X,y,tr,va,temporal,period,expanded=False,reference=False):
    f=model_features(X,tr,temporal,expanded); out={}
    families=('linear','expanded_lags') if reference and temporal else ('linear',) if reference else tuple(f)
    for name in families:
        for alpha in (.1,1.,10.,100.):
            F=f[name];mod=make_pipeline(StandardScaler(),Ridge(alpha=alpha)).fit(F[tr],y[tr]);out[f'{name}:{alpha:g}']=(mod,F)
    if reference and not temporal:
        mod=HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=15,min_samples_leaf=10,random_state=0).fit(X[tr],y[tr]);out['hist_gradient']=(mod,X)
    if temporal:
        out['persistence']=(None,X[:,0]);
        if period and reference:
            k=period-1;out['seasonal']=(None,np.r_[np.zeros(k),X[:-k,0]] if k else X[:,0])
    out['mean']=(None,np.full(len(X),np.mean(y[tr])))
    return out

def forecast(pair,idx):
    m,F=pair;return m.predict(F[idx]) if m is not None else F[idx]

def predict_policy(X,y,temporal,period,policy,reference=False,seed=610):
    X=np.asarray(X,float);y=np.asarray(y,float)
    if X.ndim!=2 or y.shape!=(len(X),) or not np.isfinite(X).all() or not np.isfinite(y).all():raise ValueError('bad data')
    tr,va,te=split(len(y),temporal,seed);dev=np.r_[tr,va];n=len(y)
    # Hide the evaluation labels even from fitting functions, not just scoring.
    visible=y.copy();visible[te]=np.nan
    folds=[(tr,va)]
    if policy.rolling:
        folds=[]
        for lo,hi in ((.35,.45),(.45,.55),(.6,.8)):
            a,b=int(n*lo),int(n*hi); folds.append((dev[:a],dev[a:b]))
    scores={};last={}
    for a,b in folds:
        models=candidates(X,visible,a,b,temporal,period,policy.expanded or reference,reference)
        last=models;vals={k:rmse(visible[b],forecast(v,b)) for k,v in models.items()}
        norm=max(min(v for k,v in vals.items() if k.startswith('linear:')),1e-12)
        for k,v in vals.items():scores.setdefault(k,[]).append(v/norm)
    linear=min((k for k in scores if k.startswith('linear:')),key=lambda k:np.mean(scores[k]))
    eligible=list(scores)
    if policy.conservative:eligible=[k for k in eligible if k.startswith('linear:') or max(scores[k])<.99]
    best=min(eligible,key=lambda k:np.mean(scores[k]))
    if policy.refit:last=candidates(X,visible,dev,va,temporal,period,policy.expanded or reference,reference)
    return {'method':best,'test_idx':te,'prediction':forecast(last[best],te),'linear':forecast(last[linear],te),'causal_claim':'abstain_observational'}

def gate(rows,tolerance=0.,min_gain=.01):
    """Strict empirical no-regression vs both comparators on EVERY held-out task.
    Also require positive simultaneous lower bound on mean normalized improvement.
    CIs are descriptive block-bootstrap approximations, not formal universal guarantees.
    """
    if not rows or len({r['task'] for r in rows})!=len(rows):return {'decision':'REJECT','reason':'missing_or_duplicate_task'}
    if any(not np.isfinite([r[k] for k in ('candidate','parent','reference','lower_parent','lower_reference')]).all() or min(r['parent'],r['reference'])<=0 for r in rows):return {'decision':'REJECT','reason':'invalid_metrics'}
    regressions=[r['task'] for r in rows if r['candidate']>min(r['parent'],r['reference'])*(1+tolerance)]
    gains=[r for r in rows if r['candidate']<=min(r['parent'],r['reference'])*(1-min_gain) and min(r['lower_parent'],r['lower_reference'])>0]
    return {'decision':'PROMOTE' if not regressions and gains else 'REJECT','regressions':regressions,'confirmed_gain_tasks':[r['task'] for r in gains], 'reason':'regression' if regressions else 'no_confirmed_gain' if not gains else 'gate_pass'}

def lower_gain(y,p,c,block,seed,alpha):
    """Paired circular block bootstrap of MSE improvement, scaled by comparator MSE."""
    a=(y-p)**2;b=(y-c)**2;n=len(a);rng=np.random.default_rng(seed);block=min(n,block)
    starts=rng.integers(0,n,(2000,int(np.ceil(n/block))))
    idx=((starts[:,:,None]+np.arange(block))%n).reshape(2000,-1)[:,:n]
    base=np.mean(a[idx],axis=1);g=np.mean((a-b)[idx],axis=1)/np.maximum(base,1e-15)
    return float(np.quantile(g,alpha))
