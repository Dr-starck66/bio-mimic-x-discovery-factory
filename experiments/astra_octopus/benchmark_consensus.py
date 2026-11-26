"""New public scientific tasks; local keys and processes, no external trust anchor."""
import os,sys,subprocess,secrets,pathlib
from dataclasses import asdict
import numpy as np
import statsmodels.api as sm
from scientific_evolution import Policy,PARENT,predict_policy,gate,lower_gain,rmse,split
from scientific_consensus import *
ROOT=pathlib.Path(__file__).parent
RULE={'tolerance':0.,'min_gain':.01,'alpha':.05/4,'seed':610,'tasks':['education','inflation'],'bootstrap':2000}
POLICY={'candidate':asdict(Policy(False,False,False,True)),'parent':asdict(PARENT),'reference':asdict(Policy(True,False,True,True))}
def code():return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('*.py')) if not p.name.startswith('test_')}
def datasets():
    e=sm.datasets.star98.load_pandas().data
    y=(e.NABOVE/(e.NABOVE+e.NBELOW)).to_numpy();X=e[['LOWINC','AVYRSEXP','AVSALK','PERSPENK','PTRATIO']].to_numpy()
    d=sm.datasets.interest_inflation.load_pandas().data;v=d.Dp.to_numpy();r=d.R.to_numpy()
    return {'education':{'X':X.tolist(),'y':y.tolist(),'temporal':False,'period':0},'inflation':{'X':np.column_stack([v[1:-1],v[:-2],r[1:-1]]).tolist(),'y':v[2:].tolist(),'temporal':True,'period':4}}
def masked(data):
    out={}
    for k,d in data.items():
        y=np.array(d['y']);_,_,te=split(len(y),d['temporal'],RULE['seed']);y[te]=0.
        out[k]={**d,'y':y.tolist(),'test_idx':te.tolist()}
    return out

def predictions(inputs,policy):
    require(set(inputs)==set(RULE['tasks']) and policy==POLICY,'unknown task or policy')
    out={}
    for k,d in inputs.items():
        X=np.array(d['X']);y=np.array(d['y']);idx=d['test_idx'];require(np.all(y[idx]==0),'unmasked target');out[k]={}
        for role in policy:
            r=predict_policy(X,y,d['temporal'],d['period'],Policy(**policy[role]),reference=role=='reference',seed=RULE['seed'])
            require(r['test_idx'].tolist()==idx,'wrong test indices');out[k][role]={'method':r['method'],'prediction':r['prediction'].tolist()}
    return out

def score(data,inputs,p):
    require(masked(data)==inputs and set(p)==set(RULE['tasks']),'dataset or tasks mismatch');rows=[]
    for i,k in enumerate(RULE['tasks']):
        idx=inputs[k]['test_idx'];y=np.array(data[k]['y'])[idx];require(set(p[k])==set(POLICY),'missing comparator')
        a,b,c=[np.array(p[k][role]['prediction']) for role in ('candidate','parent','reference')]
        block=data[k]['period'] if data[k]['temporal'] else 1
        row={'task':k,'candidate':rmse(y,a),'parent':rmse(y,b),'reference':rmse(y,c),'lower_parent':lower_gain(y,b,a,block,100+i,RULE['alpha']),'lower_reference':lower_gain(y,c,a,block,200+i,RULE['alpha'])}
        for role,z in zip(('candidate','parent','reference'),(a,b,c)):
            require(math.isclose(row[role],math.sqrt(math.fsum(float(q)**2 for q in y-z)/len(y)),rel_tol=1e-12,abs_tol=1e-12),'cross-check failed')
        rows.append(row)
    return {'rows':rows,**gate(rows,RULE['tolerance'],RULE['min_gain'])}

def validator_loop(name):
    # Private key and sign-once journal live only in this process.
    s=Signer(name,Ed25519PrivateKey.generate());data=datasets();inputs=masked(data);state={}
    print(json.dumps({'name':name,'public':public(s.key)}),flush=True)
    for line in sys.stdin:
        try:
            j=json.loads(line);stage=j['stage'];run=j['run'];reg=j['registry'];registry_check(reg)
            require(reg[name]==public(s.key),'wrong registry key')
            if stage=='preregister':
                b={'data_commitment':commitment(data,j['salt']),'public_input_sha256':digest(inputs),'policy':POLICY,'rule':RULE,'code':code(),'registry_sha256':digest(reg)}
                require(j['body']==b,'preregistration mismatch')
                require(not state,'run already registered');state.update(run=run,registry=reg,body=b,salt=j['salt'])
                out=s.sign(run,stage,b)
            else:
                require(state.get('run')==run and state.get('registry')==reg,'unregistered run or registry')
                pre=j['pre'];verify(pre,reg,run,'preregister',state['body']);p=j['predictions']
                if stage=='predictions':
                    require('predictions' not in state,'submission already signed')
                    require(predictions(inputs,POLICY)==p,'prediction replay failed')
                    state['predictions']=p
                    b={'preregistration_sha256':digest(pre),'predictions_sha256':digest(p)};out=s.sign(run,stage,b)
                elif stage=='verdict':
                    require(state.get('predictions')==p,'not the validated predictions')
                    sub=j['sub'];verify_evidence(run,pre,sub,data,state['salt'],inputs,p,reg,code(),RULE)
                    result=score(data,inputs,p);b=verdict_body(pre,sub,result)
                    out={'result':result,'attestation':s.sign(run,stage,b)}
                else:raise ValueError('unknown stage')
            print(json.dumps({'ok':True,'response':out},allow_nan=False),flush=True)
        except Exception as e:print(json.dumps({'ok':False,'error':str(e)}),flush=True)

class Lab:
    def __init__(self,name):
        self.proc=subprocess.Popen([sys.executable,__file__,'lab',name],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
        self.identity=json.loads(self.proc.stdout.readline())
    def ask(self,j):
        self.proc.stdin.write(json.dumps(j)+'\n');self.proc.stdin.flush();r=json.loads(self.proc.stdout.readline());require(r['ok'],r.get('error','validator failure'));return r['response']
    def close(self):
        self.proc.stdin.close();self.proc.wait(timeout=10);self.proc.stdout.close()

def call(mode,p):
    r=subprocess.run([sys.executable,__file__,mode],input=json.dumps(p),text=True,capture_output=True,check=True,timeout=60)
    return json.loads(r.stdout)
def write(name,obj):(ROOT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def run():
    run=secrets.token_hex(16);salt=secrets.token_hex(32);data=datasets();inputs=masked(data)
    labs=[Lab('lab-'+str(i)) for i in range(4)];reg={l.identity['name']:l.identity['public'] for l in labs}
    try:
        base={'run':run,'registry':reg};body={'data_commitment':commitment(data,salt),'public_input_sha256':digest(inputs),'policy':POLICY,'rule':RULE,'code':code(),'registry_sha256':digest(reg)}
        pre=certificate(run,'preregister',body,[l.ask({**base,'stage':'preregister','salt':salt,'body':body}) for l in labs],reg);write('preregistration.json',pre);write('registry.json',reg)
        p=call('predict',{'inputs':inputs,'policy':POLICY});b={'preregistration_sha256':digest(pre),'predictions_sha256':digest(p)}
        sub=certificate(run,'predictions',b,[l.ask({**base,'stage':'predictions','pre':pre,'predictions':p}) for l in labs],reg);write('submission.json',{'certificate':sub,'predictions':p})
        out=[l.ask({**base,'stage':'verdict','pre':pre,'sub':sub,'predictions':p}) for l in labs]
        result=out[0]['result'];require(all(q['result']==result for q in out),'validator disagreement')
        cert=finalize(run,pre,sub,result,[q['attestation'] for q in out],reg)
        bundle={**base,'pre':pre,'sub':sub,'data':data,'salt':salt,'inputs':inputs,'predictions':p,'result':result,'certificate':cert,'validator_results':out};verify_bundle(bundle,reg);write('consensus_evidence.json',bundle)
        return {'run':run,'dataset_sizes':{k:len(v['y']) for k,v in data.items()},'test_sizes':{k:len(v['test_idx']) for k,v in inputs.items()},'result':result,'signatures':len(out),'preregister_sha256':digest(pre),'submission_sha256':digest(sub),'verdict_sha256':digest(cert)}
    finally:
        for l in labs:l.close()

def verify_bundle(b,pinned_registry):
    require(b['registry']==pinned_registry,'registry changed')
    p=verify_evidence(b['run'],b['pre'],b['sub'],b['data'],b['salt'],b['inputs'],b['predictions'],pinned_registry,code(),RULE)
    require(p==POLICY and score(b['data'],b['inputs'],b['predictions'])==b['result'],'result mismatch')
    return verify_final(b['run'],b['pre'],b['sub'],b['result'],b['certificate'],pinned_registry)
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='lab':validator_loop(sys.argv[2])
    elif len(sys.argv)>1 and sys.argv[1]=='predict':
        j=json.load(sys.stdin);print(json.dumps(predictions(j['inputs'],j['policy']),allow_nan=False))
    elif len(sys.argv)>1 and sys.argv[1]=='verify':
        print(verify_bundle(json.loads((ROOT/'consensus_evidence.json').read_text()),json.loads((ROOT/'registry.json').read_text())))
    else:print(json.dumps(run(),indent=2,sort_keys=True))
