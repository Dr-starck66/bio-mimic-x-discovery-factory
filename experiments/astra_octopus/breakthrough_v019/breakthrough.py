"""Scale-law discovery: positive-domain power models, no causal claim."""
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures, SplineTransformer
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.svm import SVR
from metascience import features, rmse

POWERS=(-1.,-.5,0.,.5,1.,2.)

def power(z,p):
    return np.log(z) if p==0 else np.expm1(p*np.log(z))/p

def fit_scale(X,y,tr,va,te):
    X=np.asarray(X,float);y=np.asarray(y,float)
    if np.any(X<=0) or np.any(y[tr]<=0) or not np.isfinite(X).all():raise ValueError('positive domain required')
    g=np.exp(np.mean(np.log(X[tr]),axis=0));Z=X/g
    variants=[]
    for p in POWERS:
        F=power(Z,p)
        for link in ('identity','log'):
            t=y[tr] if link=='identity' else np.log(y[tr])
            for alpha in (.01,1.,100.):
                m=make_pipeline(StandardScaler(),Ridge(alpha=alpha)).fit(F[tr],t)
                smear=1. if link=='identity' else np.mean(np.exp(np.clip(t-m.predict(F[tr]),-50,50)))
                def pred(i):
                    v=m.predict(F[i]);return v if link=='identity' else smear*np.exp(np.clip(v,-50,50))
                a,b=pred(va),pred(te);v=rmse(y[va],a)
                sc,r=m.steps[0][1],m.steps[1][1];coef=r.coef_/sc.scale_;intercept=float(r.intercept_-coef@sc.mean_)
                variants.append((v,{'method':f'power={p:g},link={link},alpha={alpha:g}','prediction':b,'validation':v,'power':p,'link':link,'scale':g.tolist(),'coef':coef.tolist(),'intercept':intercept,'smear':float(smear)}))
    return min(variants,key=lambda a:a[0])[1]

def compare(X,y,tr,va,te):
    X=np.asarray(X,float);y=np.asarray(y,float);tr,va,te=map(np.asarray,(tr,va,te))
    if any(len(i)==0 for i in (tr,va,te)) or len(set(np.r_[tr,va,te]))!=sum(map(len,(tr,va,te))):raise ValueError('invalid split')
    visible=y.copy();visible[te]=np.nan
    scale=fit_scale(X,visible,tr,va,te);rows={'scale':scale};F=features(X,tr,False)
    def fit(name,models):
        results=[]
        for k,m,A in models:
            m.fit(A[tr],visible[tr]);v=rmse(visible[va],m.predict(A[va]));results.append((v,k,m.predict(A[te])))
        v,k,p=min(results,key=lambda z:z[0]);rows[name]={'method':k,'prediction':p,'validation':v}
    fit('parent',[(f'{k}:{a}',make_pipeline(StandardScaler(),Ridge(alpha=a)),A) for k,A in F.items() for a in (.1,1.,10.,100.)])
    fit('ridge',[(str(a),make_pipeline(StandardScaler(),Ridge(alpha=a)),X) for a in (.01,.1,1.,10.,100.)])
    fit('polynomial',[(f'{d}:{a}',make_pipeline(StandardScaler(),PolynomialFeatures(d,include_bias=False),StandardScaler(),Ridge(alpha=a)),X) for d in (2,3) for a in (.1,10.,100.)])
    fit('spline',[(f'{n}:{a}',make_pipeline(StandardScaler(),SplineTransformer(n_knots=n,extrapolation='linear'),Ridge(alpha=a)),X) for n in (3,5) for a in (.1,10.)])
    sy=max(float(np.std(visible[tr])),1e-8)
    fit('svr',[(str(c),make_pipeline(StandardScaler(),SVR(C=c*sy,epsilon=.1*sy)),X) for c in (.1,1.,10.)])
    fit('trees',[(str(l),ExtraTreesRegressor(n_estimators=64,min_samples_leaf=l,random_state=42,n_jobs=1),X) for l in (2,5)])
    fit('boost',[(str(l),HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=l,min_samples_leaf=5,random_state=42),X) for l in (7,15)])
    key=min((k for k in rows if k not in ('scale','parent')),key=lambda k:rows[k]['validation']);rows['reference']={**rows[key],'method':key+':'+rows[key]['method']}
    return rows
