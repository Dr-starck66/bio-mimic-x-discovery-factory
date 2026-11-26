"""Independent healthy calibration and test, causal windows, fixed horizon."""
import json,numpy as np
from industrial import IntegralLibrary,discover_integral,monitor

def ensemble(seed,n,noise,fault=False):
    rng=np.random.default_rng(seed);dt=.01;T=np.arange(0,12+dt/2,dt);q=np.zeros((len(T),n,2));q[0,:,0]=rng.choice([-1,1],n)*rng.uniform(.5,2.1,n);q[0,:,1]=rng.uniform(-.8,.8,n)
    def f(t,z):return np.stack([z[:,1],-np.sin(z[:,0])-(.3 if fault=='constant' else min(max(t-5.,0)*.10,.5) if fault else 0)*z[:,1]],axis=1)
    for i,t in enumerate(T[:-1]):
        a=q[i];k=f(t,a);l=f(t+dt/2,a+dt*k/2);m=f(t+dt/2,a+dt*l/2);p=f(t+dt,a+dt*m);q[i+1]=a+dt*(k+2*l+2*m+p)/6
    out=[]
    for j in range(n):
        t=T[::2][:-1].copy();t[1:]+=rng.uniform(-.007,.007,len(t)-1);z=np.column_stack([np.interp(t,T,q[:,j,k]) for k in range(2)])+rng.normal(0,noise,(len(t),2));z[rng.random(z.shape)<.1]=np.nan;keep=rng.random(len(t))>.1;out.append((t[keep],z[keep]))
    return out

def first(t,s,threshold):
    # Two consecutive available windows; a gap resets the counter.
    for i in range(1,len(t)):
        if t[i]-t[i-1]<.36 and s[i]>threshold and s[i-1]>threshold:return float(t[i])
    return None

def score(L,c,tr):return [monitor(L,c,t,z) for t,z in tr]
def cutoff(scores):
    peak=[max([min(s[i],s[i-1]) for i in range(1,len(t)) if t[i]-t[i-1]<.36],default=0.) for t,s in scores]
    return float(np.quantile(peak,.95,method='higher'))
def run():
    L=IntegralLibrary();out={};names=list(map(str,L.expr));a=np.zeros(len(names));a[names.index('x**2')]=1;a[names.index('y**2')]=1;e=np.zeros(len(names));e[names.index('cos(x)')]=-1;e[names.index('y**2')]=.5
    for noise in (.01,.03,.06):
        model=discover_integral(L,ensemble(101,12,noise),ensemble(102,12,noise));r={'model':None if model is None else model['expression'],'methods':{}};out[str(noise)]=r
        cal=ensemble(103,60,noise);healthy=ensemble(104,60,noise);fault=ensemble(105,60,noise,True)
        for name,c in [('ASTRA',model['coef'] if model else None),('quadratic_amplitude',a),('known_pendulum_energy',e)]:
            if c is None:continue
            th=cutoff(score(L,c,cal));h=[first(t,s,th) for t,s in score(L,c,healthy)];f=[first(t,s,th) for t,s in score(L,c,fault)];det=[x-5 for x in f if x is not None and x>=5];r['methods'][name]={'threshold':th,'healthy_false':sum(x is not None for x in h),'fault_early_false':sum(x is not None and x<5 for x in f),'fault_detected':len(det),'median_delay':float(np.median(det)) if det else None,'restricted_delay':float(np.mean([x-5 if x is not None and x>=5 else 7 for x in f])),'healthy_times':h,'fault_times':f}
        print(noise,r['model'],{k:{a:b for a,b in v.items() if not a.endswith('times')} for k,v in r['methods'].items()},flush=True)
    return out
if __name__=='__main__':
    with open('monitor_results.json','w') as f:json.dump(run(),f,indent=2,sort_keys=True)
