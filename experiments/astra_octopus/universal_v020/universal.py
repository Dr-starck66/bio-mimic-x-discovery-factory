"""Sparse composite first-integral discovery from dimensionless state/velocity pairs.
No physical or causal validity is inferred outside the audited domain.
"""
from itertools import combinations
from fractions import Fraction
import numpy as np
import sympy as sp

x,y=sp.symbols('x y',real=True)

def grammar(composite=True):
    p=[x**i*y**(d-i) for d in range(1,5) for i in range(d+1)]
    if composite:
        # Compose primitives with sums/differences, then multiply by envelopes.
        for z in (x,y,x+y,x-y):
            p.extend([sp.cos(z),sp.sin(z),1/(1+z*z),sp.log(1+z*z)])
        for z,w in ((x,y),(y,x)):
            for f in (sp.cos(z),1/(1+z*z),sp.log(1+z*z)):
                p.extend([w*f,w*w*f])
    return tuple(p)

class Library:
    def __init__(self,composite=True):
        self.expr=grammar(composite);self.grad=[(sp.lambdify((x,y),sp.diff(e,x),'numpy'),sp.lambdify((x,y),sp.diff(e,y),'numpy')) for e in self.expr]
        self.subsets=[np.array(list(combinations(range(len(self.expr)),k))) for k in (1,2,3)]
    def matrix(self,X):
        X=np.asarray(X,float)
        if X.ndim!=2 or X.shape[1]!=2 or not np.isfinite(X).all():raise ValueError('invalid state')
        return np.stack([np.column_stack([np.broadcast_to(f(*X.T),(len(X),)) for f in g]) for g in self.grad],axis=1)

def residual(G,V,c):
    grad=np.einsum('nid,i->nd',G,c);z=np.sum(grad*V,axis=1)
    den=np.sqrt(np.mean(np.sum(grad**2,axis=1))*np.mean(np.sum(V**2,axis=1)))
    return float(np.sqrt(np.mean(z*z))/den) if den>1e-12 else float('inf')

def discover(lib,X,V,Xv,Vv,tol=.012):
    G=lib.matrix(X);A=lib.matrix(Xv);V=np.asarray(V,float);Vv=np.asarray(Vv,float)
    if V.shape!=np.shape(X) or Vv.shape!=np.shape(Xv) or not np.isfinite(V).all() or not np.isfinite(Vv).all():raise ValueError('invalid derivatives')
    if np.mean(V*V)<1e-10: return None
    norm=np.sqrt(np.mean(np.sum(G*G,axis=2),axis=0));Gn=G/norm[None,:,None];D=np.einsum('nid,nd->ni',Gn,V);K=D.T@D/len(X)
    Q=np.einsum('nid,njd->ij',Gn,Gn)/len(X);vscale=np.mean(np.sum(V*V,axis=1))
    for inds in lib.subsets:
        k=inds.shape[1];m=K[inds[:,:,None],inds[:,None,:]];q=Q[inds[:,:,None],inds[:,None,:]]
        # Skip near-dependent gradients (identities or numerically constant functions).
        ok=np.linalg.eigvalsh(q)[:,0]>.005
        ev,U=np.linalg.eigh(m);cs=U[:,:,0];gn=np.einsum('ni,nij,nj->n',cs,q,cs)
        tr=np.sqrt(np.maximum(ev[:,0],0)/np.maximum(gn*vscale,1e-30));order=np.argsort(tr,kind='stable')
        eligible=[]
        for j in order:
            if tr[j]>tol:break
            if not ok[j]:continue
            idx=inds[j];c=cs[j]/norm[idx];c=c/c[np.argmax(abs(c))]
            # Snap to rational coefficients only when both data partitions support it.
            snap=np.array([float(Fraction(float(t)).limit_denominator(24)) for t in c]);t=residual(G[:,idx],V,snap);v=residual(A[:,idx],Vv,snap)
            if max(t,v)<=tol: eligible.append((max(t,v),idx,snap,True))
            else:
                t=residual(G[:,idx],V,c);v=residual(A[:,idx],Vv,c)
                if max(t,v)<=tol:eligible.append((max(t,v),idx,c,False))
        if eligible:
            score,idx,c,snapped=min(eligible,key=lambda a:a[0]);full=np.zeros(len(lib.expr));full[idx]=c
            expr=sp.Add(*( (sp.Rational(str(Fraction(float(t)).limit_denominator(24))) if snapped else sp.Float(t,8))*lib.expr[i] for i,t in zip(idx,c)))
            return {'coef':full,'expression':str(expr),'terms':k,'validation':score,'rational':snapped}
    return None

def audit(lib,model,X,V,tol=.012):
    if model is None:return {'accepted':False,'residual':None}
    r=residual(lib.matrix(X),V,model['coef']);return {'accepted':bool(r<=tol),'residual':r}

def symbolic_certificate(model,field):
    if model is None or not model['rational']:return False
    e=sp.sympify(model['expression'],locals={'x':x,'y':y});return sp.simplify(sp.diff(e,x)*field[0]+sp.diff(e,y)*field[1])==0
