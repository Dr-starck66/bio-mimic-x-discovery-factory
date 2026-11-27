import json, hashlib, importlib.metadata as md
import numpy as np
import statsmodels.api as sm
from sklearn.datasets import load_diabetes
import metascience as m
from benchmark_paradigm import context,simulate

def run():
    d=load_diabetes(scaled=False); sun=sm.datasets.sunspots.load_pandas().data; eng=sm.datasets.engel.load_pandas().data
    s=sun.SUNACTIVITY.to_numpy(); # one-step forecasting, known past, not multi-step forecasting
    # Common evaluation starts after 13 observations to allow all history features.
    # Drop 13 extra rows only from scoring? warm-up zeros confined to early training.
    Xs=np.column_stack([s[1:-1],s[:-2]]);ys=s[2:]
    tasks={'diabetes':(d.data,d.target,False),'sunspots':(Xs,ys,True),'engel':(eng[['income']].to_numpy(),eng.foodexp.to_numpy(),False)}
    results={}
    for name,(X,y,t) in tasks.items():
        a=m.route('prediction',X=X,y=y,temporal=t);a['data_sha256']=hashlib.sha256(np.ascontiguousarray(np.column_stack([X,y]),dtype='<f8').tobytes()).hexdigest();a['n']=len(y);results[name]=a
    # End-to-end compatibility checks with native synthetic measurement semantics.
    p={k:np.full(m.causal.N,np.dot(a.row,[.24,.0,.0])) for k,a in m.causal.ACTIONS.items()}
    q={k:(float(np.dot(a.row,[0.,0.,0.,.24,.24,0.])),.01) for k,a in m.axiom.CATALOG.items()}
    train=[simulate('interaction',74000,context(i,3),i+900) for i in range(3)]
    hold=[simulate('interaction',74000,context(i+40,4),i+2000) for i in range(2)]
    ca=m.route('physical_audit',observations=p,protocol='causal_calibrated')
    ax=m.route('physical_audit',observations=q,protocol='axiom_bounded')
    pa=m.route('model_revision',train=train,holdout=hold,protocol='axiom_multichannel')
    return {'datasets':results,'synthetic_integration':{'causal':ca['verdict'],'axiom':ax['targets']['force']['label'],'paradigm':pa['label']},'versions':{k:md.version(k) for k in ('numpy','scipy','scikit-learn','statsmodels')}}
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
