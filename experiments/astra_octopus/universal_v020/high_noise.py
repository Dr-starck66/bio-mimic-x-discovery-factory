import json,numpy as np
from industrial import *
from monitor_benchmark import ensemble

def first(t,s,th,w):
    for i in range(1,len(t)):
        if t[i]-t[i-1]<=w+1e-9 and s[i]>th and s[i-1]>th:return float(t[i])
    return None

def score(L,c,tr):
    out=[]
    for t,z in tr:
        u,s=monitor(L,c,t,z,3.15);m=u<=12;out.append((u[m],s[m]))
    return out

def evaluate(L,c,cal,healthy,fault):
    w=L.width
    peaks=[max([min(s[i],s[i-1]) for i in range(1,len(t)) if t[i]-t[i-1]<=w+1e-9],default=0.) for t,s in score(L,c,cal)]
    th=float(np.quantile(peaks,.95,method='higher'));h=[first(t,s,th,w) for t,s in score(L,c,healthy)];f=[first(t,s,th,w) for t,s in score(L,c,fault)];det=[x-5 for x in f if x is not None and x>=5]
    return {'threshold':th,'healthy_false':sum(x is not None for x in h),'early_false':sum(x is not None and x<5 for x in f),'detected':len(det),'median_delay':float(np.median(det)) if det else None,'restricted_delay':float(np.mean([x-5 if x is not None and x>=5 else 7 for x in f])),'healthy_times':h,'fault_times':f}

def run():
    noise=.06;a,b,c=[ensemble(46000+j,16,noise) for j in (1,2,3)];L=None;m=None
    for w in (.35,.7,1.05):
        L=IntegralLibrary(w);m=discover_integral(L,a,b)
        if m is not None:break
    out={'width':L.width,'expression':m['expression'] if m else None,'test':audit_integral(L,m,c),'negative':[],'methods':{}}
    for seed in range(5):
        a,b,c=[ensemble(47000+10*seed+j,12,noise,'constant') for j in (1,2,3)];row=None
        for w in (.35,.7,1.05):
            lib=IntegralLibrary(w);v=discover_integral(lib,a,b)
            if v is not None:row={'width':w,'expression':v['expression'],**audit_integral(lib,v,c)};break
        out['negative'].append(row)
    if m is not None:
        cal,healthy,fault=ensemble(46004,80,noise),ensemble(46005,80,noise),ensemble(46006,80,noise,True);names=list(map(str,L.expr));a=np.zeros(len(names));a[names.index('x**2')]=1;a[names.index('y**2')]=1;e=np.zeros(len(names));e[names.index('cos(x)')]=-1;e[names.index('y**2')]=.5
        for name,lib,co in [('ASTRA',L,m['coef']),('amplitude',L,a),('known_energy_matched',L,e),('known_energy_short',IntegralLibrary(.35),e)]:out['methods'][name]=evaluate(lib,co,cal,healthy,fault)
    return out
if __name__=='__main__':
    out=run();open('high_results.json','w').write(json.dumps(out,indent=2,sort_keys=True)+'\n');print({k:v for k,v in out.items() if k!='methods'});print({k:{a:b for a,b in v.items() if not a.endswith('times')} for k,v in out['methods'].items()})
