"""Variable projection of per-feature power transforms on the training set.
A known mathematical family, an extension of ASTRA's shared-exponent search.
"""
import numpy as np
from scipy.optimize import minimize
from breakthrough import power,rmse

def basis(Z,p):
    return np.column_stack([power(Z[:,i],q) for i,q in enumerate(p)])

def fit_mixed(X,y,tr,va,te):
    X=np.asarray(X,float);y=np.asarray(y,float)
    if np.any(X<=0) or not np.isfinite(X).all() or np.any(y[tr]<=0):raise ValueError('positive domain required')
    g=np.exp(np.mean(np.log(X[tr]),axis=0));Z=X/g;d=X.shape[1];variants=[]
    for link in ('identity','log'):
        t=y[tr] if link=='identity' else np.log(y[tr]);mu=t.mean();s=max(float(t.std()),1e-12);t=(t-mu)/s
        for alpha in (.01,1.,100.):
            def profile(p,ret=False):
                F=basis(Z[tr],p);m=F.mean(0);sd=np.maximum(F.std(0),1e-12);A=(F-m)/sd
                c=np.linalg.solve(A.T@A+alpha*np.eye(d),A.T@t);r=t-A@c
                return (m,sd,c) if ret else float((r@r+alpha*(c@c))/len(t))
            opts=[minimize(profile,np.full(d,p),bounds=[(-1.,2.)]*d,method='L-BFGS-B',options={'maxiter':100,'ftol':1e-11}) for p in (0.,1.,-.5)]
            opt=min(opts,key=lambda o:o.fun);p=opt.x;m,sd,c=profile(p,True);coef=c*s/sd;intercept=float(mu-m@coef)
            pred=lambda idx: basis(Z[idx],p)@coef+intercept
            smear=1. if link=='identity' else np.mean(np.exp(np.clip(np.log(y[tr])-pred(tr),-50,50)))
            transform=lambda v:v if link=='identity' else smear*np.exp(np.clip(v,-50,50))
            v=rmse(y[va],transform(pred(va)));variants.append({'method':f'mixed:{link}:{alpha:g}','validation':v,'prediction':transform(pred(te)),'powers':p.tolist(),'coef':coef.tolist(),'intercept':intercept,'scale':g.tolist(),'smear':float(smear),'optimization_success':bool(opt.success)})
    return min(variants,key=lambda v:v['validation'])
