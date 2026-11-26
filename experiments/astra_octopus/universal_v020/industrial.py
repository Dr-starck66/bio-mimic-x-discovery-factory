"""Window-averaged invariant search without numerical differentiation."""
import numpy as np
import sympy as sp
from universal import Library,x,y
class IntegralLibrary(Library):
    def __init__(self,width=.35):
        super().__init__();self.width=width;self.func=[sp.lambdify((x,y),e,'numpy') for e in self.expr]
    def windows(self,t,z,width=None):
        width=self.width if width is None else width
        if width<=0 or not np.isfinite(width):raise ValueError('invalid width')
        t=np.asarray(t,float);z=np.asarray(z,float)
        if t.ndim!=1 or z.shape!=(len(t),2) or not np.isfinite(t).all() or np.any(np.diff(t)<=0):raise ValueError('invalid timestamps')
        good=np.isfinite(z).all(1);t,z=t[good],z[good];bins=np.floor(t/width).astype(int)
        v=np.column_stack([np.broadcast_to(f(*z.T),(len(z),)) for f in self.func]);ts=[];a=[]
        for b in np.unique(bins):
            m=bins==b
            if m.sum()>=5:ts.append((b+1)*width);a.append(v[m].mean(0))
        return np.array(ts),np.array(a).reshape(-1,len(self.expr))
def matrices(lib,traces):
    a=[lib.windows(t,z)[1] for t,z in traces];a=[v for v in a if len(v)>=5]
    if len(a)<3:raise ValueError('insufficient trajectories')
    A=np.vstack(a);return A-A.mean(0),np.vstack([v-v.mean(0) for v in a])
def ratio(A,D,c):
    den=np.linalg.norm(A@c);return float(np.linalg.norm(D@c)/den) if den>1e-10 else float('inf')
def discover_integral(lib,train,validation,tol=.045):
    A,D=matrices(lib,train);B,E=matrices(lib,validation)
    s=np.maximum(np.sqrt(np.mean(A*A,axis=0)),1e-10);N=A/s;M=D/s;Q=N.T@N/len(N);K=M.T@M/len(M)
    for inds in lib.subsets:
        q=Q[inds[:,:,None],inds[:,None,:]];k=K[inds[:,:,None],inds[:,None,:]];ev,U=np.linalg.eigh(q);ok=ev[:,0]>.005
        if not ok.any():continue
        ids=inds[ok];W=U[ok]/np.sqrt(ev[ok,None,:]);e,u=np.linalg.eigh(W.transpose(0,2,1)@k[ok]@W);cs=(W@u[:,:,:1])[:,:,0];eligible=[]
        for j in np.argsort(e[:,0],kind='stable'):
            if e[j,0]>tol**2:break
            ix=ids[j];c=cs[j]/s[ix];c/=np.max(abs(c));r=max(ratio(A[:,ix],D[:,ix],c),ratio(B[:,ix],E[:,ix],c))
            if r<=tol:eligible.append((r,ix,c))
        if eligible:
            r,ix,v=min(eligible,key=lambda a:a[0]);c=np.zeros(len(lib.expr));c[ix]=v
            return {'coef':c,'expression':str(sp.Add(*(sp.Float(float(k),6)*lib.expr[i] for i,k in zip(ix,v)))),'validation':r}
    return None
def audit_integral(lib,model,traces,tol=.045):
    if model is None:return {'accepted':False,'ratio':None}
    A,D=matrices(lib,traces);r=ratio(A,D,model['coef']);return {'accepted':r<=tol,'ratio':r}
def monitor(lib,coef,t,z,baseline=2.1):
    ts,a=lib.windows(t,z);v=a@coef;base=ts<=baseline+1e-10
    if base.sum()<3:raise ValueError('insufficient baseline')
    return ts[~base],np.abs(v[~base]-np.median(v[base]))
