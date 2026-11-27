"""Predeclared uniform grid and dense-nullspace baseline on identical inputs."""
import json,numpy as np
from universal import Library,discover,audit
from bench_universal import sample,field,FAMILIES

def dense(lib,X,V):
    G=lib.matrix(X);s=np.sqrt(np.mean(np.sum(G*G,axis=2),axis=0));D=np.einsum('nid,nd->ni',G,V)/s
    _,_,vh=np.linalg.svd(D,full_matrices=False);return {'coef':vh[-1]/s}

def scan(lib,model,name,seed=111100):
    rng=np.random.default_rng(seed);edges=np.linspace(-2.5,2.5,22);rows=[]
    for a,b in zip(edges,edges[1:]):
        X=np.c_[rng.uniform(a,b,500),rng.uniform(-2.5,2.5,500)];V=field(name,X)+rng.normal(0,.002,X.shape)
        rows.append({'range':[float(a),float(b)],**audit(lib,model,X,V)})
    regions=[]
    for r in rows:
        if r['accepted']:
            if regions and regions[-1][1]==r['range'][0]:regions[-1][1]=r['range'][1]
            else:regions.append(r['range'].copy())
    return {'cells':rows,'accepted_regions':regions}

def run():
    lib=Library();out={'scan':{},'dense':{}}
    for name in ('pendulum','switch','coupled'):
        a,v,b,w,*_=sample(name,111001);out['scan'][name]=scan(lib,discover(lib,a,v,b,w),name)
    for name in FAMILIES:
        out['dense'][name]=[]
        for seed in range(81000,81008):
            a,v,b,w,c,z=sample(name,seed);m=dense(lib,a,v);va=audit(lib,m,b,w);te=audit(lib,m,c,z)
            out['dense'][name].append({'seed':seed,'validation':va,'test':te,'accepted':va['accepted'] and te['accepted']})
    return out
if __name__=='__main__':
    out=run();open('scan_results.json','w').write(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print({k:v['accepted_regions'] for k,v in out['scan'].items()});print({k:sum(r['accepted'] for r in v) for k,v in out['dense'].items()})
