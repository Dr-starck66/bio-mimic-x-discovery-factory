import json, hashlib, pathlib
import numpy as np
import statsmodels.api as sm
import plotly.express as px
from breakthrough import compare,rmse
ROOT=pathlib.Path(__file__).parent

def blocked(key):
    i=np.argsort(key,kind='stable');n=len(i);return i[:int(.6*n)],i[int(.6*n):int(.8*n)],i[int(.8*n):]

def tasks():
    d=px.data.gapminder();countries=d.groupby('country').gdpPercap.median().sort_values().index.to_numpy();a,b,c=blocked(np.arange(len(countries)));idx=tuple(np.flatnonzero(d.country.isin(countries[i])) for i in (a,b,c));yield 'gapminder',d[['gdpPercap','pop']].to_numpy(),d.lifeExp.to_numpy(),idx
    d=sm.datasets.copper.load_pandas().data;yield 'copper',d[['COPPERPRICE','INCOMEINDEX','ALUMPRICE','INVENTORYINDEX']].to_numpy(),d.WORLDCONSUMPTION.to_numpy(),blocked(d.TIME.to_numpy())
    d=sm.datasets.stackloss.load_pandas().data;yield 'stackloss',d[['AIRFLOW','WATERTEMP','ACIDCONC']].to_numpy(),d.STACKLOSS.to_numpy(),blocked(d.AIRFLOW.to_numpy())
    from sklearn.datasets import load_linnerud
    d=load_linnerud();yield 'linnerud',d.data+1,d.target[:,0],blocked(d.data[:,2])

def simulation(family,seed):
    r=np.random.default_rng(seed);X=np.exp(r.uniform(-1.5,1.5,(180,3)));z=X[:,0];eps=r.normal(0,.1,180)
    if family=='power': y=4*X[:,0]**.7*X[:,1]**-.4*X[:,2]**.3*np.exp(eps)
    elif family=='linear':y=10+2*z+X[:,1]+eps
    elif family=='switch':y=10+2*z+X[:,1]+eps+np.where(z>3.,-4*(z-3),0)
    elif family=='oscillatory':y=10+2*np.sin(4*z)+X[:,1]+eps
    return X,y,blocked(z)

def run(X,y,idx):
    tr,va,te=idx;rows=compare(X,y,tr,va,te);return {'n':len(y),'split':[len(i) for i in idx],'data_sha256':hashlib.sha256(np.column_stack([X,y]).astype('<f8').tobytes()).hexdigest(),'models':{k:{**{a:b for a,b in v.items() if a!='prediction'},'rmse':rmse(y[te],v['prediction'])} for k,v in rows.items()},'test_idx':te.tolist(),'actual':y[te].tolist(),'predictions':{k:v['prediction'].tolist() for k,v in rows.items()}}
if __name__=='__main__':
    out={'real':{},'simulation':{}}
    for k,X,y,idx in tasks():
        print(k,flush=True);out['real'][k]=run(X,y,idx)
    for fam in ('power','linear','switch','oscillatory'):
        print(fam,flush=True);out['simulation'][fam]=[run(*simulation(fam,s)) for s in range(83000,83012)]
    (ROOT/'results.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
