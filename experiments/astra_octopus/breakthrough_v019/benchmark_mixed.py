import json,numpy as np,statsmodels.api as sm
from breakthrough import power,compare,rmse
from mixed_power import fit_mixed
from benchmark import blocked

def simulation(family,seed):
    r=np.random.default_rng(seed);X=np.exp(r.uniform(-1.5,1.5,(240,3)));eps=r.normal(0,.15,len(X));x=X[:,0];f=3*power(x,-.8)+2.5*power(X[:,1],.6)+1.2*power(X[:,2],1.4)
    if family=='mixed':y=40+f+eps
    elif family=='linear':y=10+2*x+X[:,1]+eps
    elif family=='switch':y=40+f+np.where(x>3.,-4*(x-3),0)+eps
    return X,y,blocked(x)

def real():
    d=sm.datasets.scotland.load_pandas().data;yield 'scotland',d[['COUTAX','GDP','AGE']].to_numpy(),d.YES.to_numpy(),blocked(d.GDP.to_numpy())
    d=sm.datasets.statecrime.load_pandas().data;yield 'statecrime',d[['poverty','hs_grad','single']].to_numpy(),d.murder.to_numpy()+1,blocked(d.poverty.to_numpy())

def run(X,y,idx):
    tr,va,te=idx;v=y.copy();v[te]=np.nan;m=compare(X,y,tr,va,te);m['mixed']=fit_mixed(X,v,tr,va,te);return {'n':len(y),'split':[len(i) for i in idx],'models':{k:{**{a:b for a,b in v.items() if a!='prediction'},'rmse':rmse(y[te],v['prediction'])} for k,v in m.items()}}
if __name__=='__main__':
    out={'simulation':{},'real':{}}
    for f in ('mixed','linear','switch'):out['simulation'][f]=[run(*simulation(f,s)) for s in range(94000,94012)]
    for k,X,y,idx in real():out['real'][k]=run(X,y,idx)
    with open('mixed_results.json','w') as f:json.dump(out,f,indent=2,sort_keys=True)
