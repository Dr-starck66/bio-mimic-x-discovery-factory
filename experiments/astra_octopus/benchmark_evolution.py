"""Development on previously exposed tasks; one locked challenger on four new datasets."""
import argparse,json,hashlib, pathlib
import numpy as np
import statsmodels.api as sm
from sklearn.datasets import load_diabetes
from scientific_evolution import *
ROOT=pathlib.Path(__file__).parent

def series(v,period=0):
    v=np.asarray(v,float);return np.column_stack([v[1:-1],v[:-2]]),v[2:],True,period

def development():
    d=load_diabetes(scaled=False);e=sm.datasets.engel.load_pandas().data
    s=sm.datasets.sunspots.load_pandas().data.SUNACTIVITY.to_numpy()
    c=sm.datasets.co2.load_pandas().data.co2.resample('MS').mean().loc['1964-05-01':].to_numpy()
    return {'diabetes':(d.data,d.target,False,0),'engel':(e[['income']].to_numpy(),e.foodexp.to_numpy(),False,0),'sunspots':series(s,11),'co2':series(c,12)}

def heldout():
    n=sm.datasets.nile.load_pandas().data.volume.to_numpy();en=sm.datasets.elnino.load_pandas().data.iloc[:,1:].to_numpy().ravel();m=sm.datasets.macrodata.load_pandas().data.unemp.to_numpy();c=sm.datasets.ccard.load_pandas().data
    return {'nile':series(n),'elnino':series(en,12),'unemployment':series(m,4),'credit_expenditure':(c[['AGE','INCOME','OWNRENT']].to_numpy(),c.AVGEXP.to_numpy(),False,0)}

def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def data_hash(X,y):return hashlib.sha256(np.ascontiguousarray(np.column_stack([X,y]),dtype='<f8').tobytes()).hexdigest()
def score(data,p):
    X,y,t,s=data;r=predict_policy(X,y,t,s,p);return rmse(y[r['test_idx']],r['prediction'])

def evolve():
    tasks=development();base={k:score(v,PARENT) for k,v in tasks.items()};rows=[]
    for p in mutations():
        scores={k:score(v,p) for k,v in tasks.items()};ratios={k:scores[k]/base[k] for k in scores}
        rows.append({'policy':asdict(p),'scores':scores,'ratios':ratios,'objective':float(np.mean(list(ratios.values())))})
    # Select only one challenger, never inspect reserved datasets for this decision.
    nonparent=[r for r in rows if r['policy']!=asdict(PARENT)];best=min(nonparent,key=lambda r:r['objective'])
    lock={'policy':best['policy'],'parent':asdict(PARENT),'development':rows,'gate':{'tolerance':0.,'min_gain':.01,'alpha':.05/8,'bootstrap':2000},'reserved':['nile','elnino','unemployment','credit_expenditure'],'code_sha256':hashlib.sha256((ROOT/'scientific_evolution.py').read_bytes()).hexdigest(),'benchmark_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
    return {'lock':lock,'sha256':digest(lock)}

def evaluate(frozen):
    lock=frozen['lock'];assert digest(lock)==frozen['sha256'];assert lock['code_sha256']==hashlib.sha256((ROOT/'scientific_evolution.py').read_bytes()).hexdigest();assert lock['benchmark_sha256']==hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    policy=Policy(**lock['policy']);tasks=heldout();assert list(tasks)==lock['reserved'];rows=[]
    for i,(name,(X,y,t,s)) in enumerate(tasks.items()):
        a=predict_policy(X,y,t,s,policy);b=predict_policy(X,y,t,s,PARENT);c=predict_policy(X,y,t,s,Policy(True,False,True,True),reference=True)
        idx=a['test_idx'];assert np.array_equal(idx,b['test_idx']) and np.array_equal(idx,c['test_idx']);z=y[idx];q=a['prediction'];p=b['prediction'];r=c['prediction'];block=(s or 4) if t else 1
        rows.append({'task':name,'n':len(y),'test_n':len(idx),'data_sha256':data_hash(X,y),'candidate':rmse(z,q),'parent':rmse(z,p),'reference':rmse(z,r),'candidate_method':a['method'],'parent_method':b['method'],'reference_method':c['method'],'lower_parent':lower_gain(z,p,q,block,100+i,lock['gate']['alpha']),'lower_reference':lower_gain(z,r,q,block,200+i,lock['gate']['alpha']),'block':block,'indices':idx.tolist(),'actual':z.tolist(),'predictions':{'candidate':q.tolist(),'parent':p.tolist(),'reference':r.tolist()}})
    return {'lock_sha256':frozen['sha256'],'rows':rows,'gate':gate(rows,lock['gate']['tolerance'],lock['gate']['min_gain'])}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['dev','gate']);a=p.parse_args()
    if a.stage=='dev':
        if (ROOT/'frozen.json').exists():raise SystemExit('lock already exists')
        result=evolve();(ROOT/'frozen.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    else:
        result=evaluate(json.loads((ROOT/'frozen.json').read_text()))
    print(json.dumps(result,indent=2,sort_keys=True))
