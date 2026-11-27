"""PARADIGM: generated latent response structures outside AXIOM's column space.
Offline advisory research. No actuator interface. The residual is not a causal identity.
"""
from dataclasses import dataclass
from itertools import combinations
import numpy as np
from axiom import CATALOG, PARAMS, audit, TARGETS
from epistemic import knowledge

CHANNELS=tuple(CATALOG)
A=np.array([CATALOG[k].row for k in CHANNELS],float)
P=np.eye(len(A))-A@np.linalg.pinv(A)
# Projected output is identifiable, but a loading's component in col(A) is not.

def check_context(x):
    x=np.asarray(x,float)
    if x.ndim!=2 or x.shape[1]!=2 or not len(x) or not np.isfinite(x).all():raise ValueError('bad context')
    return x

def grammar(x):
    x=check_context(x); a,b=x.T
    # Each trajectory starts from zero memory. No use of future samples.
    lag=np.r_[0.,b[:-1]]
    memories={}
    for rho in (.3,.65,.85):
        z=0.;out=[]
        for q in b:z=rho*z+(1-rho)*q;out.append(z)
        memories[f'memory({rho})']=np.array(out)
    return {'1':np.ones(len(a)), 'x':a,'u':b,'x*x':a*a,'u*u':b*b,'x*u':a*b,
            'sin(3*x)':np.sin(3*a),'tanh(3*u)':np.tanh(3*b),'lag(u)':lag,**memories}

@dataclass(frozen=True)
class Trial:
    context:np.ndarray
    response:np.ndarray

@dataclass
class Model:
    terms:tuple
    coef:np.ndarray
    bic:float
    rank:int
    def predict(self,x):
        f=grammar(x)
        if not self.terms:return np.zeros((len(x),len(CHANNELS)))
        return np.column_stack([f[k] for k in self.terms])@self.coef
    def factors(self):
        if not self.rank:return []
        u,s,v=np.linalg.svd(self.coef,full_matrices=False)
        return [{'latent':{k:float(q) for k,q in zip(self.terms,u[:,i]*s[i])},'loading':dict(zip(CHANNELS,map(float,v[i])))} for i in range(self.rank)]

def residual(t):
    x=check_context(t.context); y=np.asarray(t.response,float)
    if y.shape!=(len(x),len(CHANNELS)) or not np.isfinite(y).all():raise ValueError('bad response')
    return y@P

def fit(trials):
    if not trials:raise ValueError('empty training')
    y=np.vstack([residual(t) for t in trials]); d=[grammar(t.context) for t in trials]
    names=tuple(d[0]); X=np.vstack([np.column_stack([f[k] for k in names]) for f in d]); n=len(y)*round(np.trace(P))
    def score(rss,k):return n*np.log(max(rss/n,1e-14))+k*np.log(n)
    out=[Model((),np.zeros((0,len(CHANNELS))),score(np.sum(y*y),0),0)]
    # Generate structures, then estimate their latent loadings rather than prescribing them.
    for size in (1,2):
        for cols in combinations(range(len(names)),size):
            x=X[:,cols]
            if np.linalg.cond(x)>1e5:continue
            q,r=np.linalg.qr(x,mode='reduced');u,s,v=np.linalg.svd(q.T@y,full_matrices=False)
            for rank in range(1,size+1):
                c=np.linalg.solve(r,(u[:,:rank]*s[:rank])@v[:rank]);err=y-x@c
                k=rank*(size+round(np.trace(P))-rank)
                out.append(Model(tuple(names[i] for i in cols),c,score(np.sum(err*err),k),rank))
    return sorted(out,key=lambda m:m.bic)

def validate(model,trials,threshold=.025):
    err=np.vstack([residual(t)-model.predict(t.context) for t in trials]);r=float(np.sqrt(np.mean(err*err)))
    return {'rmse':r,'accepted':bool(np.isfinite(r) and r<=threshold)}

def choose(models,contexts):
    if not contexts or len(models)<2:return None
    # Use competing structures, not future observed responses.
    top=models[:5]
    return max(range(len(contexts)),key=lambda i:float(np.mean(np.var([m.predict(contexts[i]) for m in top],axis=0))))

def diagnose(train,holdout):
    models=fit(train);base=next(m for m in models if not m.rank);best=models[0]
    b=validate(base,holdout);v=validate(best,holdout)
    label='no_residual_detected' if b['accepted'] else 'candidate_extension' if v['accepted'] and best.rank else 'unexplained'
    return {'label':label,'baseline':b,'candidate':v,'terms':list(best.terms),'rank':best.rank,'factors':best.factors(),'physical_identity':'unverified'}

def alias_certificate():
    # An added source with exactly the force signature is algebraically indistinguishable.
    rows=[tuple(map(int,r))+(int(r[0]),) for r in A]
    return knowledge(rows,{'physical_force':(1,0,0,0,0,0,0),'new_source':(0,0,0,0,0,0,1)})

def missing_measurement():
    """Hypothetical design only: an isolated channel with distinct source response.
    Reuses exact EPISTEMIC planner. Availability is not a physical assertion.
    """
    from epistemic import Measurement, plan
    m={k:Measurement(tuple(map(int,r))+(int(r[0]),),0) for k,r in zip(CHANNELS,A)}
    m['repeat']=Measurement(m[CHANNELS[0]].row,1,('ordinary',))
    m['isolated_physical']=Measurement((1,0,0,0,0,0,0),4,('verified_isolation',))
    t={'physical_force':(1,0,0,0,0,0,0),'new_source':(0,0,0,0,0,0,1)}
    return {'ordinary_only':plan(list(CHANNELS),m,t,('ordinary',),10),
            'hypothetical_isolation':plan(list(CHANNELS),m,t,('ordinary','verified_isolation'),10)}
