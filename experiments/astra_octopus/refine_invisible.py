"""Continuous parameter refinement of single-history hypotheses; no actuator interface."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.signal import lfilter
from invisible import DT,CAL,BASE,SPEC,design,fit,audit,history

def continuous(t,kind,p):
    if kind=='delay':
        n=int(np.floor(p/DT));f=p/DT-n
        a=history(t.x,t.v,t.u,'delay',n);b=history(t.x,t.v,t.u,'delay',n+1)
        z=(1-f)*a+f*b
        # No prehistory; samples before the time origin are zero (not extrapolated).
        z[np.arange(len(z))*DT<p-1e-12]=0.
        return z
    if kind in ('memory_u','memory_x'):
        a=np.exp(-DT/p);return lfilter([1-a],[1,-a],t.u if kind=='memory_u' else t.x)
    return history(t.x,t.v,t.u,kind,p)

@dataclass
class Refined:
    family:str
    param:float
    coef:np.ndarray
    score:float
    def predict(self,t):return design(t)[:,:len(BASE)]@self.coef[:-1]+self.coef[-1]*continuous(t,self.family,self.param)
    def describe(self):return {'family':self.family,'terms':list(BASE)+[[self.family,self.param]],'coef':self.coef.tolist(),'bic':float(self.score),'parameter_unit':'seconds' if self.family!='hysteresis' else 'normalized position'}

def refine(trials,models=None):
    """Revisit each single mechanism across its whole grid; compare against original joint hypotheses."""
    models=fit(trials) if models is None else models
    X=np.vstack([design(t)[:,:len(BASE)] for t in trials]);y=np.concatenate([t.y for t in trials]);n=len(y)
    Q,_=np.linalg.qr(X,mode='reduced');r=y-Q@(Q.T@y)
    def optimize(kind,grid):
        def objective(p):
            z=np.concatenate([continuous(t,kind,p) for t in trials]);z=z-Q@(Q.T@z);den=z@z
            return float(r@r-(r@z)**2/den) if den>1e-10 else float('inf')
        # Sample endpoints and optimize each bracket rather than assuming a unimodal profile.
        options=[(objective(p),p) for p in grid]
        for a,b in zip(grid,grid[1:]):
            opt=minimize_scalar(objective,bounds=(a,b),method='bounded',options={'xatol':1e-6});options.append((opt.fun,opt.x))
        _,p=min(options);A=np.column_stack([X,np.concatenate([continuous(t,kind,p) for t in trials])]);c=np.linalg.lstsq(A,y,rcond=None)[0];rss=max(float(np.sum((y-A@c)**2)),1e-12)
        return Refined(kind,float(p),c,n*np.log(rss/n)+(len(BASE)+2)*np.log(n))
    rr=[]
    for kind in ('delay','memory_u','memory_x','hysteresis'):
        g=[float(p)*DT if kind=='delay' else float(p) for f,p in SPEC if f==kind]
        # Delay response can change at integer sample boundaries; include every sample.
        if kind=='delay':g=list(np.arange(2,21)*DT)
        rr.append(optimize(kind,g))
    return min([models[0],*rr],key=lambda m:m.score)
