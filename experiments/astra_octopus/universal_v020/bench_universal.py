import json,sys
import numpy as np
import sympy as sp
from universal import Library,discover,audit,symbolic_certificate,x,y
from scipy.integrate import solve_ivp
# Independent analytic vector fields; not constructed via learner derivatives.
FAMILIES=('oscillator','quartic','pendulum','rational','coupled','damped','switch','random')

def field(name,X):
    a,b=X.T
    if name=='oscillator':return np.c_[b,-2*a]
    if name=='quartic':return np.c_[b,-a**3]
    if name=='pendulum':return np.c_[b,-np.sin(a)]
    if name=='rational':return np.c_[b, -2*a/(1+a*a)**2]
    if name=='coupled':return np.c_[b*(2+np.cos(a)),.5*b*b*np.sin(a)-a]
    if name=='damped':return np.c_[b,-a-.6*b]
    if name=='switch':return np.c_[b,-np.sin(a)-np.where(abs(a)>1.5,.9*b,0)]
    return np.c_[np.sin(2*a)+b,a-np.cos(3*b)]

def symfield(name):
    return {'oscillator':(y,-2*x),'quartic':(y,-x**3),'pendulum':(y,-sp.sin(x)),'rational':(y,-2*x/(1+x*x)**2),'coupled':(y*(2+sp.cos(x)),y*y*sp.sin(x)/2-x),'damped':(y,-x-sp.Rational(3,5)*y),'random':(sp.sin(2*x)+y,x-sp.cos(3*y))}.get(name)

def sample(name,seed):
    r=np.random.default_rng(seed);a=r.uniform(-1.3,1.3,(240,2));b=r.uniform(-1.5,1.5,(160,2));c=r.uniform(-2.5,2.5,(300,2));c=c[np.max(abs(c),axis=1)>1.5]
    v=field(name,a);w=field(name,b);z=field(name,c)
    return a,v+r.normal(0,.002,v.shape),b,w+r.normal(0,.002,w.shape),c,z+r.normal(0,.002,z.shape)

def run(seed0=81000,n=8):
    libs={k:Library(v) for k,v in [('polynomial',False),('composite',True)]};out={}
    for name in FAMILIES:
        out[name]=[]
        for seed in range(seed0,seed0+n):
            a,v,b,w,c,z=sample(name,seed);row={'seed':seed}
            for k,L in libs.items():
                m=discover(L,a,v,b,w);test=audit(L,m,c,z);sf=symfield(name)
                row[k]={**test,'expression':m['expression'] if m else None,'symbolic':symbolic_certificate(m,sf) if sf else None,'validation':m['validation'] if m else None}
                if m:
                    e=sp.lambdify((x,y),sp.sympify(m['expression'],locals={'x':x,'y':y}),'numpy');sol=solve_ivp(lambda t,q:field(name,q[None,:])[0],(0,4),[1.8,.5],rtol=1e-9,atol=1e-11,t_eval=np.linspace(0,4,201));vals=e(*sol.y);row[k]['trajectory_span']=float(np.ptp(vals))
            out[name].append(row)
        print(name,[(k,sum(r[k]['accepted'] for r in out[name]),sum(r[k]['symbolic'] is True for r in out[name])) for k in libs],flush=True)
    return out
if __name__=='__main__':
    out=run();open(sys.argv[1] if len(sys.argv)>1 else 'results.json','w').write(json.dumps(out,indent=2,sort_keys=True)+'\n')
