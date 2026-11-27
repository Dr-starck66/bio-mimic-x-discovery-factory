"""External regression challenge. Separate custody, not a sandbox or proof of truth."""
import argparse, hashlib, json, os, secrets
from pathlib import Path
import numpy as np
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
from scientific_evolution import candidates, forecast, rmse
from scientific_consensus import canonical, digest
ROOT=Path(__file__).resolve().parent
CODE=('external_challenge.py','scientific_evolution.py','metascience.py','genesis.py','invisible.py','paradigm.py','axiom.py','causal.py','epistemic.py','active_doubt.py','discovery.py','scientific_consensus.py','requirements.txt')
RULE={'type':'grouped_regression','min_gain':.01,'promotion':'never_from_single_task','candidate':'refit_selected','parent':'train_only','reference':'ridge_or_hist_train_only'}
def need(ok,msg):
    if not ok: raise ValueError(msg)
def read(p): return json.loads(Path(p).read_text())
def write(p,obj): Path(p).write_bytes(canonical(obj)+b'\n')
def code(): return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in CODE}
def sign(key,body): return {'body':body,'signature':key.sign(canonical(body)).hex()}
def verify(doc,pin):
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(pin)).verify(bytes.fromhex(doc['signature']),canonical(doc['body']));return doc['body']
def commit(y,salt): return digest({'domain':'external-holdout-v1','salt':salt,'labels':y})
def arrays(task):
    need(set(task)=={'train','validation','test'},'invalid splits');seen=set();parts=[]
    for k in ('train','validation','test'):
        d=task[k];need(set(d)==({'X','groups'} if k=='test' else {'X','groups','y'}),'invalid columns')
        x=np.array(d['X'],float);groups=d['groups'];need(x.ndim==2 and len(x)>=5 and np.isfinite(x).all() and len(groups)==len(x) and all(isinstance(g,str) and g for g in groups),'invalid rows')
        need(not (seen & set(groups)),'group leakage');seen.update(groups)
        y=np.array(d.get('y',[float('nan')]*len(x)),float);need(y.shape==(len(x),) and (k=='test' or np.isfinite(y).all()),'invalid y');parts.append((x,y))
    X=np.concatenate([x for x,y in parts]);y=np.concatenate([y for x,y in parts]);a,b,c=[len(x) for x,y in parts]
    return X,y,np.arange(a),np.arange(a,a+b),np.arange(a+b,a+b+c)
def prepare(task,labels,private,public):
    X,y,tr,va,te=arrays(task);need(np.asarray(labels,float).shape==(len(te),) and np.isfinite(labels).all(),'invalid labels')
    private=Path(private);public=Path(public);need(private.resolve()!=public.resolve() and private.resolve() not in public.resolve().parents and public.resolve() not in private.resolve().parents,'separate directories required')
    private.mkdir(mode=0o700,parents=True,exist_ok=False);public.mkdir(parents=True,exist_ok=False)
    key=Ed25519PrivateKey.generate();pin=key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex();salt=secrets.token_hex(32)
    fd=os.open(private/'key.bin',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:f.write(key.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption()))
    body={'domain':'ASTRA-EXTERNAL-v0.18','run':secrets.token_hex(16),'task_sha256':digest(task),'label_commitment':commit(labels,salt),'rule':RULE,'code':code(),'custodian_public_key':pin}
    prereg=sign(key,body);write(public/'task.json',task);write(public/'prereg.json',prereg);write(private/'opening.json',{'labels':labels,'salt':salt,'prereg_sha256':digest(prereg)})
    return {'pin':pin,'prereg_sha256':digest(prereg)}
def check(task,pre,pin,expected):
    p=verify(pre,pin);need(digest(pre)==expected and p['custodian_public_key']==pin and p['domain']=='ASTRA-EXTERNAL-v0.18','untrusted preregistration');need(p['rule']==RULE and p['code']==code() and p['task_sha256']==digest(task),'protocol/code/input changed');return p
def submit(task,pre,pin,expected):
    check(task,pre,pin,expected);X,y,tr,va,te=arrays(task);out={}
    for role in ('parent','candidate','reference'):
        models=candidates(X,y,tr,va,False,0,reference=role=='reference');best=min(models,key=lambda k:rmse(y[va],forecast(models[k],va)))
        if role=='candidate':models=candidates(X,y,np.r_[tr,va],va,False,0)
        out[role]={'method':best,'prediction':forecast(models[best],te).tolist()}
    return {'prereg_sha256':expected,'predictions':out}
def judge(task,pre,submission,pin,expected,private):
    p=check(task,pre,pin,expected);private=Path(private);opening=read(private/'opening.json');key=Ed25519PrivateKey.from_private_bytes((private/'key.bin').read_bytes())
    need(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()==pin,'wrong key');need(opening['prereg_sha256']==expected and commit(opening['labels'],opening['salt'])==p['label_commitment'],'private labels changed');need(submission==submit(task,pre,pin,expected),'prediction replay mismatch')
    y=np.asarray(opening['labels']);scores={k:rmse(y,v['prediction']) for k,v in submission['predictions'].items()};best=min(scores['parent'],scores['reference']);decision='REJECT' if scores['candidate']>best else 'ELIGIBLE_FOR_FURTHER_TESTING' if best>0 and scores['candidate']<=.99*best else 'NO_GAIN'
    receipt={'domain':'ASTRA-EXTERNAL-RECEIPT-v0.18','prereg_sha256':expected,'submission_sha256':digest(submission),'run':p['run'],'scores':scores,'decision':decision,'promotion':False,'test_n':len(y),'label_commitment':p['label_commitment']}
    return sign(key,receipt)
def verify_receipt(receipt,pre,submission,pin,expected):
    p=verify(pre,pin);r=verify(receipt,pin);need(digest(pre)==expected and p['rule']==RULE and r['domain']=='ASTRA-EXTERNAL-RECEIPT-v0.18' and r['run']==p['run'] and r['prereg_sha256']==expected and r['submission_sha256']==digest(submission) and r['label_commitment']==p['label_commitment'] and r['promotion'] is False,'receipt mismatch')
    s=r['scores'];need(set(s)=={'parent','candidate','reference'} and np.isfinite(list(s.values())).all() and min(s.values())>=0,'invalid scores');b=min(s['parent'],s['reference']);need(r['decision']==('REJECT' if s['candidate']>b else 'ELIGIBLE_FOR_FURTHER_TESTING' if b>0 and s['candidate']<=.99*b else 'NO_GAIN'),'decision mismatch');return r
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','submit','judge','verify']);p.add_argument('--public',required=True);p.add_argument('--private');p.add_argument('--task');p.add_argument('--labels');p.add_argument('--pin');p.add_argument('--expected');a=p.parse_args();d=Path(a.public)
    if a.stage=='prepare':print(json.dumps(prepare(read(a.task),read(a.labels),a.private,d)))
    else:
        task,pre=read(d/'task.json'),read(d/'prereg.json')
        if a.stage=='submit':write(d/'submission.json',submit(task,pre,a.pin,a.expected))
        elif a.stage=='judge':write(d/'receipt.json',judge(task,pre,read(d/'submission.json'),a.pin,a.expected,a.private))
        else:print(json.dumps(verify_receipt(read(d/'receipt.json'),pre,read(d/'submission.json'),a.pin,a.expected),indent=2))
