"""Unified scientific routing. Offline research; no physical action or clinical advice.
Model selection on validation only, one final held-out evaluation. All adapters explicit.
"""
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.dummy import DummyRegressor
import genesis, invisible, causal, epistemic, axiom, paradigm


def rmse(a,b):
    a,b=np.asarray(a),np.asarray(b)
    if a.shape!=b.shape or not len(a) or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('invalid prediction')
    return float(np.sqrt(np.mean((a-b)**2)))


def split(n,temporal,seed=610):
    if n<60:raise ValueError('not enough observations')
    idx=np.arange(n) if temporal else np.random.default_rng(seed).permutation(n)
    return idx[:int(.6*n)],idx[int(.6*n):int(.8*n)],idx[int(.8*n):]


def features(X,train,temporal):
    """Use GENESIS atoms and PARADIGM grammar as bounded feature constructors.
    INVISIBLE uses lag only on chronological series; no invented history for patients.
    """
    X=np.asarray(X,float);s=StandardScaler().fit(X[train]);Z=s.transform(X);n,d=Z.shape
    base=Z
    symbolic=[]
    for i in range(d):
        x=Z[:,i];zero=np.zeros(n)
        for op in genesis.OPS:
            for k in (.5,1.,2.):symbolic.append(genesis.Atom(op,'x').evaluate(x,zero,zero,k))
    latent=[]
    for i in range(min(d,3)):
        for j in range(i,min(d,3)):
            g=paradigm.grammar(np.column_stack([Z[:,i],Z[:,j]]))
            latent.append(g['x*u'])
    out={'linear':base,'genesis_atoms':np.column_stack([base,*symbolic]),'paradigm_interactions':np.column_stack([base,*latent])}
    if temporal:
        x=Z[:,0];zero=np.zeros(n);h=[]
        # X contains observations through t-1 only. Time scale is discrete samples,
        # not physical seconds: INVISIBLE's lag operator is reusable without rescaling DT.
        for lag in (1,2,3,5,8,10,11,12):h.append(invisible.history(zero,zero,x,'delay',lag))
        out['invisible_lags']=np.column_stack([base,*h])
        out['combined']=np.column_stack([base,*symbolic,*latent,*h])
    return out


def predict(X,y,*,temporal=False,seed=610):
    X,y=np.asarray(X,float),np.asarray(y,float)
    if X.ndim!=2 or len(X)!=len(y) or y.ndim!=1 or not np.isfinite(X).all() or not np.isfinite(y).all():raise ValueError('invalid dataset')
    tr,va,te=split(len(y),temporal,seed);f=features(X,tr,temporal)
    # Models fitted on train only, selection on validation only; holdout scored afterwards.
    models={}; val={}
    for name,F in f.items():
        for alpha in (.1,1.,10.,100.):
            m=make_pipeline(StandardScaler(),Ridge(alpha=alpha)).fit(F[tr],y[tr]);key=f'{name}:{alpha:g}'
            models[key]=(m,F);val[key]=rmse(y[va],m.predict(F[va]))
    dummy=DummyRegressor().fit(X[tr],y[tr]);models['mean']=(dummy,X);val['mean']=rmse(y[va],dummy.predict(X[va]))
    if temporal:
        val['persistence']=rmse(y[va],X[va,0])
    best=min(val,key=val.get);linear=min((k for k in val if k.startswith('linear:')),key=val.get)
    def forecast(k,idx):
        if k=='persistence':return X[idx,0]
        m,F=models[k];return m.predict(F[idx])
    errors={k:rmse(y[te],forecast(k,te)) for k in (best,linear,'mean')}
    if temporal:errors['persistence']=rmse(y[te],forecast('persistence',te))
    # No rescue selection on test. Reject recommendation if no gain vs linear.
    status='predictive_gain' if errors[best]<.99*errors[linear] else 'no_gain_demonstrated'
    # Observational slope decomposed into effect + unmeasured confounding:
    # illustrative exact ambiguity, not a learned causal graph.
    ident=epistemic.knowledge([(1,1)],{'causal_effect':(1,0)})
    return {'selected':best,'baseline':linear,'validation':val,'test_rmse':errors,'status':status,
            'split_sizes':[len(tr),len(va),len(te)],'causal_claim':'abstain_observational','ambiguity':ident,'test_indices':te.tolist()}


def physical_audit(observations,*,protocol):
    """Explicit type dispatch, never reinterpret observational data as interventions."""
    if protocol=='causal_calibrated':return causal.infer(observations)
    if protocol=='axiom_bounded':return axiom.audit(observations)
    raise ValueError('unrecognized physical measurement protocol')


def model_revision(train,holdout,*,protocol):
    if protocol!='axiom_multichannel':raise ValueError('requires ten AXIOM channels and documented mapping')
    return paradigm.diagnose(train,holdout)


def route(task,**kwargs):
    if task=='prediction':return predict(**kwargs)
    if task=='physical_audit':return physical_audit(**kwargs)
    if task=='model_revision':return model_revision(**kwargs)
    if task=='identifiability':return epistemic.knowledge(**kwargs)
    raise ValueError('unknown task; abstain')
