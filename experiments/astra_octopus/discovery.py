"""Sparse structural discovery and experiment design. Simulation only; no actuator API."""
from dataclasses import dataclass
from itertools import combinations
import numpy as np
from active_doubt import Permit, permitted, DT, COUNT, AMP

TERMS=('1','u','x','v','x²','x³','v|v|','u|u|','xu')
SCALES=np.array([1.,1.,.3,.3,.09,.027,.09,1.,.3])
SUBSETS=[(1,)+s for n in range(5) for s in combinations((0,2,3,4,5,6,7,8),n)]

def features(x,v,u):
    x,v,u=np.broadcast_arrays(x,v,u)
    return np.stack((np.ones_like(x),u,x,v,x*x,x**3,v*abs(v),u*abs(u),x*u),axis=-1)

@dataclass(frozen=True)
class Model:
    coefficients: np.ndarray
    support: tuple
    bic: float
    rmse: float
    def predict(self,x,v,u): return features(x,v,u)@self.coefficients
    def equation(self):return ' '.join(f'{self.coefficients[i]:+.4f}·{TERMS[i]}' for i in self.support)

def fit(data, max_terms=5):
    data=np.asarray(data,float)
    if data.ndim!=2 or data.shape[1]!=4 or len(data)<30 or not np.isfinite(data).all():raise ValueError('invalid observations')
    X=features(*data[:,:3].T)/SCALES; y=data[:,3]; n=len(y)
    G=X.T@X; b=X.T@y; yy=y@y; models=[]
    for s in SUBSETS:
        if len(s)>max_terms:continue
        idx=np.array(s);g=G[np.ix_(idx,idx)]
        if np.linalg.cond(g)>1e8:continue
        c=np.linalg.solve(g,b[idx]);rss=max(float(yy-2*c@b[idx]+c@g@c),1e-12)
        full=np.zeros(len(TERMS));full[idx]=c/SCALES[idx]
        models.append(Model(full,s,n*np.log(rss/n)+len(s)*np.log(n),np.sqrt(rss/n)))
    return sorted(models,key=lambda m:m.bic)

def linear(data):return min((m for m in fit(data,3) if m.support==(1,2,3)),key=lambda m:m.bic)

@dataclass(frozen=True)
class Experiment:
    x0: float
    v0: float
    amplitude: float
    kind: str
    def signal(self):
        k=np.arange(COUNT)
        return self.amplitude*np.where((k<10)|(k>=30),1.,-1.) if self.kind=='balanced' else self.amplitude*np.where(k<20,1.,-1.)
    def authorized(self,p):
        # External supervisor must certify actual initial state and bounds; no authorization inferred from models.
        return (self.kind in ('balanced','bipolar') and np.isfinite([self.x0,self.v0,self.amplitude]).all()
                and abs(self.amplitude)<=AMP and abs(self.v0)<=p.speed_bound and permitted(p,COUNT*DT))

def rollout(model,e):
    x,v=e.x0,e.v0; out=[]
    for u in e.signal():
        a=float(model.predict(x,v,u));out.append(a);v+=DT*a;x+=DT*v
        if not np.isfinite([x,v]).all() or abs(x)>3 or abs(v)>5:return None
    return np.array(out)

def choose(models,experiments,permit):
    if len(models)<2:return None,{}
    # Deliberately include competing sparse structures even when BIC strongly favors the leading model.
    candidates=models[:8]; scores={}
    allowed=[e for e in experiments if e.authorized(permit)]
    if not allowed:return None,{}
    x=np.broadcast_to([e.x0 for e in allowed],(len(candidates),len(allowed))).copy()
    v=np.broadcast_to([e.v0 for e in allowed],x.shape).copy()
    coeff=np.array([m.coefficients for m in candidates]);signals=np.array([e.signal() for e in allowed]);pred=[];valid=np.ones(len(allowed),dtype=bool)
    for k in range(COUNT):
        u=signals[:,k];a=np.einsum('mei,mi->me',features(x,v,u),coeff);pred.append(a)
        v+=DT*a;x+=DT*v;valid &= np.all(np.isfinite(x)&np.isfinite(v)&(abs(x)<=3)&(abs(v)<=5),axis=0)
        x=np.clip(np.nan_to_num(x),-3,3);v=np.clip(np.nan_to_num(v),-5,5)
    variance=np.mean(np.var(np.array(pred),axis=1),axis=0)
    scores={e:float(value) for e,value,ok in zip(allowed,variance,valid) if ok}
    return (max(scores,key=scores.get),scores) if scores else (None,{})

def audit(model, data, threshold=.035):
    if not np.isfinite(data).all():return {'rmse':None,'accepted':False}
    r=data[:,3]-model.predict(*data[:,:3].T);rmse=float(np.sqrt(np.mean(r*r)))
    return {'rmse':rmse,'accepted':rmse<=threshold}
