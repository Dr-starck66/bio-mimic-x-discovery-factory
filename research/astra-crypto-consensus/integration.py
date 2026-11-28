"""Real CometBFT integration test. Fictional data only; no direct App.dispatch calls."""
import base64, concurrent.futures, hashlib, json, os, pathlib, re, socket, subprocess, sys, time, urllib.request, urllib.error
from native import Key,export_public,L
from lab import A,B,C,D,ALL,choose,Policy,canon,p95
from state import CHAIN,digest,b64,attest,payment
root=pathlib.Path("/tmp/astra-integration")
p=pathlib.Path(sys.argv[1]).resolve();p.mkdir(parents=True,exist_ok=True)
root.mkdir();src=pathlib.Path(__file__).resolve().parent
bin="/tmp/cometbft"; adapter="/tmp/astra-abci"
keys={str(i):Key('SLH-DSA-SHA2-256f') for i in range(7)}
banks={a:Key(a) for a in sorted(ALL)}
gen={'chain':CHAIN,'roster':{i:b64(export_public(k)) for i,k in keys.items()},'banks':{a:b64(export_public(k)) for a,k in banks.items()}}
g=digest(gen);rp=p/'roster.json';rp.write_bytes(canon(gen))
print("OPENSSL",L.version().decode(),"ROSTER",g,flush=True)
subprocess.run([bin,'testnet','--v','7','--o',str(root/'net'),'--populate-persistent-peers=false'],check=True)
homes=[root/'net'/f'node{i}' for i in range(7)]
ports=[28000+10*i for i in range(7)]
ids=[subprocess.check_output([bin,'show-node-id','--home',str(h)],text=True).strip() for h in homes]
for i,h in enumerate(homes):
    gj=h/'config/genesis.json';d=json.loads(gj.read_text());d['chain_id']=CHAIN;gj.write_text(json.dumps(d,indent=2))
    cfg=h/'config/config.toml';s=cfg.read_text()
    peers=','.join(f'{ids[j]}@127.0.0.1:{ports[j]}' for j in range(7) if j!=i)
    s=re.sub(r'(?m)^persistent_peers\s*=.*$',f'persistent_peers = "{peers}"',s)
    s=s.replace('tcp://0.0.0.0:26656',f'tcp://127.0.0.1:{ports[i]}').replace('tcp://127.0.0.1:26657',f'tcp://127.0.0.1:{ports[i]+1}')
    s=re.sub(r'(?m)^pprof_laddr\s*=.*$','pprof_laddr = ""',s)
    s=re.sub(r'(?m)^timeout_commit\s*=.*$','timeout_commit = "1s"',s)
    cfg.write_text(s)
(p/'genesis.json').write_bytes((homes[0]/'config/genesis.json').read_bytes())
apps={};nodes={};checks={};receipts=[];metrics={}
def check(label,condition):
    checks[label]=bool(condition);print("CHECK",label,condition,flush=True);assert condition,label
def state(i):return json.loads((root/f'state{i}.json').read_bytes())
def wait(fn,seconds=75):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        try:
            v=fn()
            if v:return v
        except (OSError,ValueError,RuntimeError,KeyError):pass
        time.sleep(.25)
    raise RuntimeError("wait timed out")
def rpc(i,method,params=None):
    url=f'http://127.0.0.1:{ports[i]+1}/'
    req=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=20) as r:d=json.load(r)
    if 'error' in d:raise RuntimeError(d['error'])
    return d['result']
def start(i):
    log=open(p/f'app{i}.log','a')
    apps[i]=subprocess.Popen([adapter,'--listen',f'tcp://127.0.0.1:{ports[i]+2}','--genesis',str(rp),'--state',str(root/f'state{i}.json'),'--script',str(src/'state.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    def listening():
        if apps[i].poll() is not None:raise AssertionError(f'ABCI exited {i}')
        with socket.create_connection(('127.0.0.1',ports[i]+2),timeout=.3):return True
    wait(listening,20)
    log=open(p/f'node{i}.log','a')
    nodes[i]=subprocess.Popen([bin,'node','--home',str(homes[i]),f'--proxy_app=tcp://127.0.0.1:{ports[i]+2}'],stdout=log,stderr=subprocess.STDOUT)
def kill(i):
    import signal
    nodes[i].kill();nodes[i].wait()
    os.killpg(apps[i].pid,signal.SIGKILL);apps[i].wait()
def height(i):return int(rpc(i,'status')['sync_info']['latest_block_height'])
def certificate(i,h,label):
    d=wait(lambda:rpc(i,'commit',{'height':str(h)}))
    f=p/(label+'.json');f.write_text(json.dumps(d,indent=2))
    subprocess.run(['/tmp/astra-verify',str(p/'genesis.json'),str(f)],check=True)
    return d['signed_header']
def inc(e,n,who):
    m={'chain':CHAIN,'genesis':g,'epoch':e,'incident':n}
    return canon({'kind':'incident','message':m,'votes':[{'member':str(i),'signature':b64(keys[str(i)].sign(attest(m,str(i))))} for i in who]})
def pay(e,a,i):
    m={'chain':CHAIN,'genesis':g,'epoch':e,'id':i,'alg':a,'cents':100}
    return canon({'kind':'payment','message':m,'signature':b64(banks[a].sign(payment(m)))})
def send(i,tx):
    return rpc(i,'broadcast_tx_sync',{'tx':b64(tx)})
def refused(i,tx,label):
    res=send(i,tx);check(label,int(res.get('code',0))!=0)
    (p/(label+'.json')).write_text(json.dumps(res,indent=2))
def final(i,tx,label):
    res=send(i,tx);check(label+'_checktx',int(res.get('code',0))==0)
    hsh=hashlib.sha256(tx).digest()
    d=wait(lambda:rpc(i,'tx',{'hash':b64(hsh),'prove':True}))
    check(label+'_final',int(d['tx_result'].get('code',0))==0)
    h=int(d['height']);sh=certificate(i,h,label+'-commit')
    receipts.append({'label':label,'height':h,'tx_hash':hsh.hex(),'round':sh['commit']['round']})
    (p/(label+'-tx.json')).write_text(json.dumps(d,indent=2));(p/(label+'-raw.json')).write_bytes(tx)
    return h
def batch(i,ep,a,count):
    txs=[pay(ep,a,f'{ep}-{j}') for j in range(count)]
    def submit(tx):
        r=send(i,tx);assert int(r.get('code',0))==0,r
    t=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:list(ex.map(submit,txs))
    wait(lambda:all(f'{ep}-{j}' in state(i)['ledger'] for j in range(count)))
    for tx in txs:
        d=wait(lambda:rpc(i,'tx',{'hash':b64(hashlib.sha256(tx).digest()),'prove':False}))
        assert int(d['tx_result'].get('code',0))==0
    check(f'phase_{ep}_all_final',True)
    metrics[f'phase_{ep}']={'count':count,'algorithm':a,'seconds':time.monotonic()-t}
def calibrate():
    result={}
    for a,k in banks.items():
        pub=k.public();times=[]
        for j in range(8):
            msg=f'calibrate-{j}'.encode();t=time.perf_counter();sig=k.sign(msg);assert pub.verify(msg,sig);times.append(time.perf_counter()-t)
        result[a]={'p95_ms':p95(times)*1000,'pairs_s':len(times)/sum(times)}
    return result
try:
    for i in range(7):start(i)
    wait(lambda:min(height(i) for i in range(7))>=2)
    certificate(0,1,'first')
    m=calibrate();metrics['calibration']=m
    a=choose(Policy(0,ALL,frozenset()),'adaptive',m)[0];check('initial_algorithm',a==A)
    batch(0,0,a,40)
    refused(0,inc(0,'targeted',[0,1]),'insufficient_attestations')
    bad=json.loads(inc(0,'targeted',[0,1,2]));bad['message']['incident']='family';refused(0,canon(bad),'tampered_incident')
    final(0,inc(0,'targeted',[0,1,2]),'targeted')
    wait(lambda:all(state(i)['epoch']==1 for i in range(7)))
    refused(0,pay(1,A,'revoked'),'revoked_signature')
    refused(0,pay(0,B,'old'),'old_epoch')
    refused(0,inc(0,'family',[3,4,5]),'contradictory_old_policy')
    a=choose(Policy(1,ALL,frozenset({A})),'adaptive',m)[0];check('targeted_selection',a in ALL-{A})
    kill(5);kill(6);print("KILLED NODES 5,6",flush=True)
    batch(0,1,a,40)
    refused(0,pay(1,a,'1-0'),'duplicate_payment')
    final(0,inc(1,'family',[3,4,5]),'family')
    wait(lambda:all(state(i)['epoch']==2 for i in range(5)))
    refused(0,pay(2,B,'revoked-family'),'revoked_family')
    a=choose(Policy(2,ALL,frozenset({A,B})),'adaptive',m)[0];check('family_selection',a in (C,D))
    batch(0,2,a,40)
    # Loss and restoration of quorum, then catch-up using the persisted app and consensus state.
    kill(4);time.sleep(2);before=[height(i) for i in range(4)];time.sleep(8);after=[height(i) for i in range(4)]
    check('no_finality_without_quorum',before==after);metrics['quorum_loss']={'before':before,'after':after,'seconds':8}
    for i in (4,5,6):start(i)
    wait(lambda:all(len(state(i)['ledger'])==120 and state(i)['epoch']==2 for i in range(7)),120)
    snaps=[state(i) for i in range(7)]
    projections=[{k:v for k,v in s.items() if k!='height'} for s in snaps]
    check('all_seven_ledger_convergence',len({digest(s) for s in projections})==1)
    check('no_revoked_post_migration',all(v['alg'] not in ({A} if v['epoch']==1 else {A,B} if v['epoch']==2 else set()) for v in projections[0]['ledger'].values()))
    # Header at H+1 commits to the application's post-H hash.
    for i,s in enumerate(snaps):
        (p/f'public-state-{i}.json').write_bytes(canon(s))
        h=s['height']+1;wait(lambda:height(i)>h)
        sh=certificate(i,h,f'anchor-{i}')
        check(f'ledger_anchor_{i}',sh['header']['app_hash'].lower()==digest(s))
    print("INTEGRATION PASS: 120 fictional payments, 2 PQ signed incident policies, 7 converged ledgers",flush=True)
finally:
    (p/'summary.json').write_text(json.dumps({'checks':checks,'metrics':metrics,'receipts':receipts},indent=2))
    import signal
    for proc in nodes.values():
        if proc.poll() is None:proc.terminate()
    for proc in apps.values():
        if proc.poll() is None:os.killpg(proc.pid,signal.SIGTERM)
    for proc in list(nodes.values())+list(apps.values()):
        try:proc.wait(timeout=4)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
