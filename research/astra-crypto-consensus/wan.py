"""Cross-VM ASTRA research test. Private keys never leave their generating VM."""
import os,sys,json,time,subprocess,pathlib,re,hashlib,base64,socket,signal,urllib.request,platform,threading
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from lab import A,B,C,D,ALL,Policy,choose,canon,p95
from state import CHAIN,digest,b64,payment,attest
root=pathlib.Path('/tmp/astra-wan');src=pathlib.Path(__file__).resolve().parent
role=os.environ['ROLE']; local=list(range(4)) if role=='A' else list(range(4,7)); other=[i for i in range(7) if i not in local]
pub=root/'public';evidence=pathlib.Path(os.environ['GITHUB_WORKSPACE'])/'evidence';bin='/tmp/cometbft'
def dump(p,x):p.write_text(json.dumps(x,indent=2))
def load(p):return json.loads(p.read_bytes())
def home(i):return root/f'node{i}'
def port(i):return 28000+10*i
def cli(*args,data=None):
    return subprocess.check_output(['openssl',*args],input=data)
def key(name,alg):
    path=root/'keys'/name
    subprocess.run(['openssl','genpkey','-algorithm',alg,'-out',str(path)],check=True)
    path.chmod(0o600)
    return b64(cli('pkey','-in',str(path),'-pubout','-outform','DER'))
def sign(name,m):
    # pkeyutl one-shot PQ signing requires a regular input file.
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(dir=root) as f:
        f.write(m);f.flush()
        return cli('pkeyutl','-sign','-rawin','-inkey',str(root/'keys'/name),'-in',f.name)
def prepare():
    root.mkdir(exist_ok=True);pub.mkdir();evidence.mkdir(exist_ok=True);(root/'keys').mkdir(mode=0o700)
    members=[]
    for i in local:
        subprocess.run([bin,'init','--home',str(home(i))],check=True)
        k=load(home(i)/'config/priv_validator_key.json')
        nid=subprocess.check_output([bin,'show-node-id','--home',str(home(i))],text=True).strip()
        members.append({'index':i,'node_id':nid,'validator':{'address':k['address'],'pub_key':k['pub_key'],'power':'1','name':f'node{i}'}})
    meta={'role':role,'members':members,'host':platform.uname()._asdict()}
    if role=='A':
        g=load(home(0)/'config/genesis.json')
        (pub/'template.json').write_bytes(canon(g))
        gen={'chain':CHAIN,'roster':{str(i):key(f'attest{i}','SLH-DSA-SHA2-256f') for i in range(7)},'banks':{a:key(a,a) for a in sorted(ALL)}}
        (pub/'roster.json').write_bytes(canon(gen))
        # URL allocated by a separate workflow step; only public metadata is uploaded.
        meta['tunnel']=(root/'tunnel.url').read_text().strip()
        assert re.fullmatch(r'https://[a-z0-9-]+\.trycloudflare\.com',meta['tunnel'])
    else:
        k=Ed25519PrivateKey.generate()
        priv=root/'bridge.key';priv.write_bytes(k.private_bytes_raw());priv.chmod(0o600)
        meta['bridge_pub']=k.public_key().public_bytes_raw().hex()
    dump(pub/'members.json',meta)
def run():
    mine=load(pub/'members.json');remote=load(root/'other/members.json')
    assert mine['role']==role and remote['role']!=role and mine['host']['machine']!=remote['host']['machine']
    a=pub if role=='A' else root/'other'
    g=load(a/'template.json');gen=load(a/'roster.json');gd=digest(gen)
    members=sorted(mine['members']+remote['members'],key=lambda x:x['index'])
    assert [m['index'] for m in members]==list(range(7))
    assert len({m['validator']['address'] for m in members})==7
    g['validators']=[m['validator'] for m in members];g['chain_id']=CHAIN;g['app_state']={'astra_roster_sha256':gd}
    gp=evidence/'genesis.json';gp.write_bytes(canon(g));rp=evidence/'roster.json';rp.write_bytes(canon(gen))
    dump(evidence/'members.json',{'local':mine,'remote':remote})
    for i in local:
        h=home(i);(h/'config/genesis.json').write_bytes(canon(g));cfg=h/'config/config.toml';s=cfg.read_text()
        peers=[f"{members[j]['node_id']}@127.0.0.1:{port(j)}" for j in local if j!=i]
        if role=='B':peers += [f"{members[j]['node_id']}@127.0.0.1:{29000+j}" for j in other]
        for name,val in [('persistent_peers',json.dumps(','.join(peers))),('pprof_laddr','""'),('timeout_commit','"1s"'),('addr_book_strict','false'),('allow_duplicate_ip','true'),('pex','false')]:
            s=re.sub(r'(?m)^'+name+r'\s*=.*$',name+' = '+val,s)
        s=s.replace('tcp://0.0.0.0:26656',f'tcp://127.0.0.1:{port(i)}').replace('tcp://127.0.0.1:26657',f'tcp://127.0.0.1:{port(i)+1}')
        cfg.write_text(s)
    cleanenv={k:v for k,v in os.environ.items() if k not in ('GH_TOKEN','GITHUB_TOKEN')}
    def spawn(args,name,session=False):
        f=open(evidence/name,'a')
        return subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT,start_new_session=session,env=cleanenv)
    bridge=spawn([sys.executable,'-u',str(src/'wan_bridge.py'),role],'bridge.log')
    apps={};nodes={};checks={};metrics={};trace=[];done=threading.Event()
    def check(n,v):checks[n]=bool(v);print('CHECK',role,n,v,flush=True);assert v,n
    def wait(fn,seconds=120):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            try:
                v=fn()
                if v:return v
            except (OSError,ValueError,RuntimeError,KeyError):pass
            time.sleep(.25)
        raise RuntimeError('timeout '+str(fn))
    def rpc(i,method,params=None):
        req=urllib.request.Request(f'http://127.0.0.1:{port(i)+1}/',data=canon({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}}),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=10) as r:d=json.load(r)
        if 'error' in d:raise RuntimeError(d['error'])
        return d['result']
    def height(i):return int(rpc(i,'status')['sync_info']['latest_block_height'])
    def state(i):return load(root/f'state{i}.json')
    def start(i):
        apps[i]=spawn(['/tmp/astra-abci','--listen',f'tcp://127.0.0.1:{port(i)+2}','--genesis',str(rp),'--state',str(root/f'state{i}.json'),'--script',str(src/'state.py')],f'app{i}.log',True)
        def ready():
            if apps[i].poll() is not None:raise AssertionError('ABCI exited')
            with socket.create_connection(('127.0.0.1',port(i)+2),timeout=.3):return True
        wait(ready,20)
        nodes[i]=spawn([bin,'node','--home',str(home(i)),f'--proxy_app=tcp://127.0.0.1:{port(i)+2}'],f'node{i}.log')
    def cert(i,h,name):
        d=wait(lambda:rpc(i,'commit',{'height':str(h)}));f=evidence/(name+'.json');dump(f,d)
        subprocess.run(['/tmp/astra-verify',str(gp),str(f)],check=True)
        sh=d['signed_header'];sigs={s['validator_address'] for s in sh['commit']['signatures'] if s['block_id_flag']==2}
        a_ids={m['validator']['address'] for m in members[:4]};b_ids={m['validator']['address'] for m in members[4:]}
        assert len(sigs)>=5 and sigs&a_ids and sigs&b_ids
        return sh
    def pay(e,a,i):
        m={'chain':CHAIN,'genesis':gd,'epoch':e,'id':i,'alg':a,'cents':100}
        return canon({'kind':'payment','message':m,'signature':b64(sign(a,payment(m)))})
    def inc(e,n):
        m={'chain':CHAIN,'genesis':gd,'epoch':e,'incident':n}
        return canon({'kind':'incident','message':m,'votes':[{'member':str(i),'signature':b64(sign(f'attest{i}',attest(m,str(i))))} for i in (0,1,2)]})
    def tx(x,name):
        i=local[0];r=rpc(i,'broadcast_tx_sync',{'tx':b64(x)});assert int(r.get('code',0))==0,r
        d=wait(lambda:rpc(i,'tx',{'hash':b64(hashlib.sha256(x).digest()),'prove':True}));assert int(d['tx_result'].get('code',0))==0
        dump(evidence/(name+'-tx.json'),d);(evidence/(name+'-raw.json')).write_bytes(x);cert(i,int(d['height']),name+'-commit')
    def trace_loop():
        while not done.is_set():
            try:trace.append({'utc':time.time(),'heights':[height(i) for i in local]})
            except Exception:pass
            done.wait(.5)
    def anchor():
        wait(lambda:all(len(state(i)['ledger'])==12 and state(i)['epoch']==2 for i in local),180)
        snaps=[state(i) for i in local]
        projection=[{k:v for k,v in s.items() if k!='height'} for s in snaps]
        check('local_convergence',len({digest(s) for s in projection})==1)
        metrics['ledger_projection_sha256']=digest(projection[0])
        for i,s in zip(local,snaps):
            (evidence/f'public-state-{i}.json').write_bytes(canon(s));h=s['height']+1
            wait(lambda:height(i)>h)
            sh=cert(i,h,f'anchor-{i}');check(f'anchor_{i}',sh['header']['app_hash'].lower()==digest(s))
    try:
        for i in local:start(i)
        wait(lambda:min(height(i) for i in local)>=2,180)
        check('cross_host_first_commit',bool(cert(local[0],1,'first')))
        thread=threading.Thread(target=trace_loop,daemon=True);thread.start()
        if role=='A':
            m={}
            for alg in sorted(ALL):
                times=[]
                for j in range(4):
                    t=time.perf_counter();sign(alg,b'calibration');times.append(time.perf_counter()-t)
                m[alg]={'p95_ms':p95(times)*1000,'pairs_s':len(times)/sum(times)}
            metrics['calibration']=m;metrics['selections']=[]
            for e in range(3):
                if e:
                    n='targeted' if e==1 else 'family'
                    tx(inc(e-1,n),n)
                    wait(lambda:all(state(i)['epoch']==e for i in local))
                revoked=frozenset() if e==0 else frozenset({A}) if e==1 else frozenset({A,B})
                alg=choose(Policy(e,ALL,revoked),'adaptive',m)[0];metrics['selections'].append(alg)
                for j in range(4):tx(pay(e,alg,f'{e}-{j}'),f'payment-{e}-{j}')
                if e==1:
                    (root/'partition.flag').touch();time.sleep(3)
                    before=[height(i) for i in local];t0=time.time();time.sleep(8);after=[height(i) for i in local];t1=time.time()
                    metrics['partition']={'before':before,'after':after,'utc_start':t0,'utc_end':t1}
                    check('four_cannot_finalize_partitioned',before==after)
                    (root/'partition.flag').unlink()
                    wait(lambda:min(height(i) for i in local)>max(after),120)
                    check('resume_after_reconnect',True)
        anchor()
        if role=='A':
            # Wait for the peer's public evidence upload, keeping the quorum alive.
            token=os.environ.get('GH_TOKEN','')
            def peer_evidence():
                r=subprocess.run(['gh','api',f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}/artifacts",'--jq','.artifacts[].name'],capture_output=True,text=True,timeout=15)
                return r.returncode==0 and 'wan-evidence-B' in r.stdout.splitlines()
            wait(peer_evidence,120)
        print('WAN PASS',role,metrics.get('ledger_projection_sha256'),flush=True)
    finally:
        done.set();dump(evidence/'summary.json',{'role':role,'checks':checks,'metrics':metrics,'height_trace':trace})
        for proc in nodes.values():
            if proc.poll() is None:proc.terminate()
        for proc in apps.values():
            if proc.poll() is None:os.killpg(proc.pid,signal.SIGTERM)
        if bridge.poll() is None:bridge.terminate()
        for proc in [*nodes.values(),*apps.values(),bridge]:
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
if __name__=='__main__':
    prepare() if sys.argv[1]=='prepare' else run()
