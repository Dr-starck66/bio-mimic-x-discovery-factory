"""Finite latent-state search in a prescribed-trajectory virtual test rig, not robot control."""
from dataclasses import dataclass
import numpy as np
from genesis import Atom
DT=.02
CAL=25
LAGS=(2,4,6,8,10,12,16,20)
TAUS=(.08,.12,.20,.30,.45,.65,.90)
WIDTHS=(.025,.05,.08,.12,.16,.22)
BASE=('1','u','x','v','x²','v|v|','xu','sin(12x)')
SPEC=[('delay',k) for k in LAGS]+[(f,k) for f in ('memory_u','memory_x') for k in TAUS]+[('hysteresis',k) for k in WIDTHS]
@dataclass(frozen=True)
class Trial:
    x:np.ndarray
    v:np.ndarray
    u:np.ndarray
    y:np.ndarray

def history(x,v,u,kind,param):
    if kind=='delay':
        k=int(param);return np.r_[np.zeros(k),u[:-k]]
    if kind in ('memory_u','memory_x'):
        src=u if kind=='memory_u' else x; z=0.; out=[]; a=np.exp(-DT/param)
        for q in src:
            z=a*z+(1-a)*q;out.append(z)
        return np.array(out)
    if kind=='hysteresis':
        z=0.;out=[]
        for q in x:
            z=min(max(z,q-param),q+param);out.append(z)
        return np.array(out)
    raise ValueError(kind)

def design(t):
    x,v,u=t.x,t.v,t.u
    return np.column_stack([np.ones_like(x),u,x,v,x*x,v*abs(v),x*u,Atom('sin','x').evaluate(x,v,u,12),*[history(x,v,u,*s) for s in SPEC]])
@dataclass
class Model:
    cols:tuple
    coef:np.ndarray
    offset:bool
    score:float
    @property
    def family(self):
        f=tuple(sorted(SPEC[i-len(BASE)][0] for i in self.cols if i>=len(BASE)))
        return '+'.join(f+ (('latent_offset',) if self.offset else ())) or 'instantaneous'
    def predict(self,t,calibrate=True):
        p=design(t)[:,self.cols]@self.coef
        if self.offset and calibrate:p=p+np.mean(t.y[:CAL]-p[:CAL])
        return p
    def describe(self):return {'family':self.family,'terms':[BASE[i] if i<len(BASE) else list(SPEC[i-len(BASE)]) for i in self.cols],'coef':self.coef.tolist(),'bic':float(self.score)}

def fit(trials):
    if not trials or any(len(t.y)<=CAL or not np.isfinite(np.column_stack([t.x,t.v,t.u,t.y])).all() for t in trials):raise ValueError('invalid trial')
    Ds=[design(t) for t in trials]; ys=[t.y for t in trials];X=np.vstack(Ds); y=np.concatenate(ys); n=len(y); nb=len(BASE); models=[]
    # Group intercepts estimated only on training groups. For new groups use a separate calibration prefix.
    Xc=np.vstack([d-d.mean(0) for d in Ds]);yc=np.concatenate([a-a.mean() for a in ys])
    candidates=[tuple(range(nb))]+[tuple(range(nb))+(i,) for i in range(nb,X.shape[1])]
    # Joint mechanisms of different families, only one parameter per family.
    candidates += [tuple(range(nb))+(i,j) for i in range(nb,X.shape[1]) for j in range(i+1,X.shape[1]) if SPEC[i-nb][0]!=SPEC[j-nb][0]]
    for latent in (False,True):
        A,b=(Xc,yc) if latent else (X,y);G=A.T@A;h=A.T@b;yy=b@b
        for size in (nb,nb+1,nb+2):
            cc=[c for c in candidates if len(c)==size];ix=np.array([c[1:] if latent else c for c in cc]);g=G[ix[:,:,None],ix[:,None,:]];rhs=h[ix]
            ok=np.linalg.cond(g)<1e10
            if not np.any(ok):continue
            cs=np.linalg.solve(g[ok],rhs[ok,:,None])[:,:,0]
            rss=np.maximum(yy-2*np.einsum('ij,ij->i',cs,rhs[ok])+np.einsum('ij,ijk,ik->i',cs,g[ok],cs),1e-12)
            k=size+(size-nb)+(len(trials)-1 if latent else 0)
            for cols,c,r in zip([c for c,valid in zip(cc,ok) if valid],cs,rss):
                if latent:c=np.r_[np.mean(y-X[:,cols[1:]]@c),c]
                models.append(Model(cols,c,latent,n*np.log(r/n)+k*np.log(n)))
    return sorted(models,key=lambda m:m.score)

def select(models,probes):
    """Disagreement among best distinct structures; advisory, no actuator interface."""
    reps={}
    for m in models:
        if m.family not in reps:reps[m.family]=m
        if len(reps)>=5:break
    if not probes or len(reps)<2:return None
    # A future latent offset is unknowable before the calibration measurements.
    def score(t):
        D=design(t);preds=np.array([(D[:,m.cols]@m.coef)[CAL:] for m in reps.values()]);return float(np.mean(np.var(preds,axis=0)))
    return max(range(len(probes)),key=lambda i:score(probes[i]))

def audit(m,trials,threshold=.055):
    errors=np.concatenate([(t.y-m.predict(t))[CAL:] for t in trials]);rmse=float(np.sqrt(np.mean(errors**2)))
    return {'rmse':rmse,'accepted':bool(np.isfinite(rmse) and rmse<=threshold)}
