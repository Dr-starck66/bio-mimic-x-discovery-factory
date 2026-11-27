"""Post-hoc temporal policy revision; evaluate on a separate public CO2 series.
Sunspot re-evaluation is exploratory because its original holdout was already observed.
"""
import json
import numpy as np
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from metascience import features,rmse,predict


def robust(X,y):
    n=len(y); end=int(.8*n); folds=[(int(n*a),int(n*b)) for a,b in ((.35,.45),(.45,.55),(.6,.8))]
    scores={};last={}
    for lo,hi in folds:
        f=features(X,np.arange(lo),True);val={}
        for name,F in f.items():
            for alpha in (.1,1.,10.,100.):
                k=f'{name}:{alpha:g}';mod=make_pipeline(StandardScaler(),Ridge(alpha=alpha)).fit(F[:lo],y[:lo]);val[k]=rmse(y[lo:hi],mod.predict(F[lo:hi]));last[k]=(mod,F)
        lin=min(v for k,v in val.items() if k.startswith('linear:'))
        for k,v in val.items():scores.setdefault(k,[]).append(v/max(lin,1e-12))
    linear=min((k for k in scores if k.startswith('linear:')),key=lambda k:np.mean(scores[k]))
    # Challenge complexity: accept it only if it improves on the best linear model
    # in every rolling validation fold by at least 1%.
    approved=[k for k,s in scores.items() if not k.startswith('linear:') and max(s)<.99]
    best=min(approved,key=lambda k:np.mean(scores[k])) if approved else linear
    def err(k):
        mod,F=last[k];return rmse(y[end:],mod.predict(F[end:]))
    return {'selected':best,'baseline':linear,'test_rmse':err(best),'linear_rmse':err(linear),'fold_ratios':scores,'complex_models_approved':approved,'test_n':n-end,'persistence_rmse':rmse(y[end:],X[end:,0])}


def run():
    s=sm.datasets.sunspots.load_pandas().data.SUNACTIVITY.to_numpy()
    c=sm.datasets.co2.load_pandas().data.co2.resample('MS').mean().loc['1964-05-01':].to_numpy()
    assert np.isfinite(c).all()
    out={}
    for k,v in [('sunspots_exploratory',s),('co2_new_dataset',c)]:
        X=np.column_stack([v[1:-1],v[:-2]]);y=v[2:];r=robust(X,y);old=predict(X,y,temporal=True);r['original_method']=old['selected'];r['original_rmse']=old['test_rmse'][old['selected']];r['n']=len(y);r['seasonal_naive_rmse']=rmse(y[-r['test_n']:],v[len(v)-r['test_n']-12:len(v)-12]);out[k]=r
    return out
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
