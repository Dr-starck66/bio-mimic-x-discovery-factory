"""Bounded scientific policy evaluation. Logical roles, not a security sandbox."""
import hashlib,json,pathlib,subprocess,sys
from dataclasses import asdict
import numpy as np
from scientific_evolution import Policy,PARENT,mutations,predict_policy,gate,lower_gain,rmse,split
ROOT=pathlib.Path(__file__).resolve().parent
TASKS=('cancer_counts','fertility','medical_visits','strike_duration')
RULE={'tolerance':0.,'min_gain':.01,'alpha':.05/8,'seed':610}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def code_lock():return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('*.py')) if not p.name.startswith('test_')}
def require(ok,message):
    if not ok:raise ValueError(message)
def discover():
    from benchmark_evolution import development,heldout,score
    tasks={**development(),**heldout()};base={k:score(v,PARENT) for k,v in tasks.items()};rows=[]
    for p in mutations():
        ratios={k:score(v,p)/base[k] for k,v in tasks.items()}
        rows.append({'policy':asdict(p),'ratios':ratios,'objective':float(np.mean(list(ratios.values()))+max(ratios.values())-1)})
    best=min((r for r in rows if r['policy']!=asdict(PARENT)),key=lambda r:r['objective'])
    l={'policy':best['policy'],'parent':asdict(PARENT),'reference':asdict(Policy(True,False,True,True)),'tasks':list(TASKS),'rule':RULE,'code':code_lock(),'development':rows}
    return {'lock':l,'sha256':digest(l)}
def validate_lock(f):
    l=f['lock'];require(digest(l)==f['sha256'],'lock digest');require(l['code']==code_lock(),'code changed');require(l['tasks']==list(TASKS) and l['rule']==RULE,'protocol changed');require(l['parent']==asdict(PARENT) and l['reference']==asdict(Policy(True,False,True,True)),'comparator changed');return l
def new_tasks():
    import statsmodels.api as sm
    c=sm.datasets.cancer.load_pandas().data
    f=sm.datasets.fertility.load_pandas().data[['1980','1990','2000','2010']].dropna()
    r=sm.datasets.randhie.load_pandas().data;r=r.iloc[np.random.default_rng(20261126).choice(len(r),1200,replace=False)]
    s=sm.datasets.strikes.load_pandas().data
    return {'cancer_counts':(c[['population']].to_numpy(),c.cancer.to_numpy()),'fertility':(f[['1980','1990','2000']].to_numpy(),f['2010'].to_numpy()),'medical_visits':(r.drop(columns='mdvis').to_numpy(),r.mdvis.to_numpy()),'strike_duration':(s[['iprod']].to_numpy(),s.duration.to_numpy())}
def public_input(task,X,y):
    X=np.asarray(X,float);y=np.asarray(y,float);_,_,te=split(len(y),False,RULE['seed']);v=y.copy();v[te]=0.
    return {'task':task,'X':X.tolist(),'visible_y':v.tolist(),'test_idx':te.tolist()}
def worker(p):
    a=p['input'];X=np.array(a['X']);y=np.array(a['visible_y']);require(np.all(y[a['test_idx']]==0),'test labels not masked')
    r=predict_policy(X,y,False,0,Policy(**p['policy']),reference=p['role']=='reference',seed=RULE['seed'])
    require(r['test_idx'].tolist()==a['test_idx'],'index mismatch')
    return {'input_sha256':digest(a),'role':p['role'],'policy':p['policy'],'method':r['method'],'prediction':r['prediction'].tolist(),'test_idx':r['test_idx'].tolist()}
def call_worker(p):
    r=subprocess.run([sys.executable,str(ROOT/'scientific_arbiter.py'),'worker'],input=json.dumps(p),text=True,capture_output=True,check=True,timeout=60)
    return json.loads(r.stdout)
def build_submission(f):
    l=validate_lock(f);out={};truth={}
    for k,(X,y) in new_tasks().items():
        a=public_input(k,X,y);truth[k]={'input':a,'y':np.asarray(y)[a['test_idx']].tolist()};out[k]={}
        for role in ('candidate','parent','reference'):
            out[k][role]=call_worker({'input':a,'policy':l['policy' if role=='candidate' else role],'role':role})
    b={'lock_sha256':f['sha256'],'predictions':out};return {'body':b,'sha256':digest(b)},truth
def verify_submission(f,s,t):
    l=validate_lock(f);b=s['body'];require(digest(b)==s['sha256'],'submission digest');require(b['lock_sha256']==f['sha256'],'wrong lock');require(set(b['predictions'])==set(TASKS)==set(t),'missing/extra task')
    for k in TASKS:
        a=t[k]['input'];rr=b['predictions'][k];require(set(rr)=={'candidate','parent','reference'},'roles')
        for role,r in rr.items():
            require(r['role']==role and r['policy']==l['policy' if role=='candidate' else role],'wrong role/policy');require(r['input_sha256']==digest(a) and r['test_idx']==a['test_idx'],'wrong data/indices');z=np.asarray(r['prediction'],float);require(z.shape==(len(a['test_idx']),) and np.isfinite(z).all(),'invalid predictions')
    return True
def falsify(f,s,t):
    verify_submission(f,s,t);l=f['lock'];checks={}
    for k in TASKS:
        a=t[k]['input']
        for role in ('candidate','parent','reference'):
            p={'input':a,'policy':l['policy' if role=='candidate' else role],'role':role};checks[k+':'+role+':replay']=call_worker(p)==s['body']['predictions'][k][role]
        bad=json.loads(json.dumps(p));bad['input']['visible_y'][a['test_idx'][0]]=123456.
        try:worker(bad);checks[k+':mask_reject']=False
        except ValueError:checks[k+':mask_reject']=True
    return {'submission_sha256':s['sha256'],'checks':checks,'passed':all(checks.values())}
def arbitrate(f,s,t,report):
    verify_submission(f,s,t);require(report==falsify(f,s,t) and report['passed'],'falsifier mismatch/fail');rows=[]
    for i,k in enumerate(TASKS):
        y=np.array(t[k]['y']);r=s['body']['predictions'][k];c,p,b=[np.array(r[a]['prediction']) for a in ('candidate','parent','reference')]
        rows.append({'task':k,'n':len(t[k]['input']['X']),'test_n':len(y),'candidate':rmse(y,c),'parent':rmse(y,p),'reference':rmse(y,b),'lower_parent':lower_gain(y,p,c,1,100+i,RULE['alpha']),'lower_reference':lower_gain(y,b,c,1,200+i,RULE['alpha']),'methods':{a:z['method'] for a,z in r.items()}})
    return {'lock_sha256':f['sha256'],'submission_sha256':s['sha256'],'rows':rows,'gate':gate(rows,RULE['tolerance'],RULE['min_gain'])}
def write(name,obj):(ROOT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def read(name):return json.loads((ROOT/name).read_text())
if __name__=='__main__':
    if sys.argv[1]=='worker':print(json.dumps(worker(json.load(sys.stdin)),allow_nan=False))
    elif sys.argv[1]=='discover':
        require(not (ROOT/'arbiter_lock.json').exists(),'lock already exists');write('arbiter_lock.json',discover())
    elif sys.argv[1]=='evaluate':
        f=read('arbiter_lock.json');s,t=build_submission(f);write('committed_predictions.json',s);r=falsify(f,s,t);write('falsifier_report.json',r);result=arbitrate(f,s,t,r);write('evaluation_truth.json',t);write('arbiter_results.json',result)
