"""Symbolic residual search in normalized coordinates. Simulation only."""
from dataclasses import dataclass
from itertools import product
import numpy as np
from scipy.optimize import minimize_scalar
from discovery import Experiment, rollout
OPS=('sin','cos','tanh','gaussian','rational','log1p')
ARGS=('x','v','u','x+v','x-v')
ENVS=('1','x','v','u')
FREQ=np.arange(.5,40.01,.5)
DIM={'x':(1,0),'v':(1,-1),'u':(1,-2),'1':(0,0)}
@dataclass(frozen=True,order=True)
class Atom:
    op:str
    arg:str
    env:str='1'
    def dimensions(self,normalized=True):
        d={k:(0,0) if normalized else v for k,v in DIM.items()}
        names=self.arg.replace('-','+').split('+');out=d[names[0]]
        if any(d[n]!=out for n in names) or out!=(0,0):raise ValueError('incompatible or dimensional function argument')
        return d[self.env]
    def evaluate(self,x,v,u,k):
        a={'x':x,'v':v,'u':u,'x+v':x+v,'x-v':x-v}[self.arg]*k
        f={'sin':np.sin,'cos':np.cos,'tanh':np.tanh,'gaussian':lambda z:np.exp(-z*z),'rational':lambda z:1/(1+z*z),'log1p':lambda z:np.log1p(z*z)}[self.op](a)
        return f*{'1':1.,'x':x,'v':v,'u':u}[self.env]
@dataclass
class Symbolic:
    c:np.ndarray
    atom:Atom|None
    k:float
    bic:float
    rmse:float
    def predict(self,x,v,u):return self.c[0]*u+self.c[1]*x+self.c[2]*v+(self.c[3]*self.atom.evaluate(x,v,u,self.k) if self.atom else 0.)
    def equation(self):return f'{self.c[0]:+.5f} u {self.c[1]:+.5f} x {self.c[2]:+.5f} v'+(f' {self.c[3]:+.5f} {self.atom.env}*{self.atom.op}({self.k:.5g}*({self.atom.arg}))' if self.atom else '')
def neighbors(elite):
    out=set()
    for a in elite:
        out.update(Atom(o,a.arg,a.env) for o in OPS)
        out.update(Atom(a.op,s,a.env) for s in ARGS)
        out.update(Atom(a.op,a.arg,e) for e in ENVS)
    out.update(Atom(a.op,b.arg,b.env) for a,b in product(elite,repeat=2))
    return out

def search(data):
    data=np.asarray(data,float)
    if data.ndim!=2 or data.shape[1]!=4 or len(data)<30 or not np.isfinite(data).all():raise ValueError('invalid observations')
    x,v,u,y=data.T;base=np.column_stack((u,x,v));n=len(y)
    if np.linalg.matrix_rank(base)<3:raise ValueError('unidentifiable base')
    Q,_=np.linalg.qr(base,mode='reduced');r=y-Q@(Q.T@y);rss0=float(r@r)
    baseline=Symbolic(np.linalg.lstsq(base,y,rcond=None)[0],None,0.,n*np.log(max(rss0,1e-12)/n)+3*np.log(n),np.sqrt(rss0/n))
    seen={};attempted=set()
    def score(a):
        if a in attempted:return
        attempted.add(a)
        if a.dimensions()!=(0,0):return
        z=a.evaluate(x[:,None],v[:,None],u[:,None],FREQ[None,:]);z=z-Q@(Q.T@z)
        den=np.sum(z*z,axis=0);num=r@z
        improvement=np.divide(num*num,den,out=np.zeros_like(den),where=den>1e-10);j=int(np.argmax(improvement))
        def loss(k):
            z=a.evaluate(x,v,u,k);z=z-Q@(Q.T@z);d=z@z
            return rss0-(r@z)**2/d if d>1e-10 else rss0
        opt=minimize_scalar(loss,bounds=(max(.25,FREQ[j]-.5),min(40.5,FREQ[j]+.5)),method='bounded')
        k=float(opt.x);X=np.column_stack((base,a.evaluate(x,v,u,k)))
        if np.linalg.cond(X)>1e5:return
        c=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@c;rss=max(float(res@res),1e-12)
        complexity=5+int(a.env!='1')+int(a.arg in ('x+v','x-v'))
        seen[a]=Symbolic(c,a,k,n*np.log(rss/n)+complexity*np.log(n),np.sqrt(rss/n))
    # Explore every simple input/envelope combination before pruning.
    for op,arg,env in product(OPS,('x','v','u'),ENVS):score(Atom(op,arg,env))
    for _ in range(2):
        elite=[m.atom for m in sorted(seen.values(),key=lambda m:m.bic)[:4]]
        for a in sorted(neighbors(elite)):score(a)
    return sorted([baseline,*seen.values()],key=lambda m:m.bic),len(attempted)

def select_probe(models,experiments,permit):
    scores={}
    for e in experiments:
        if not e.authorized(permit):continue
        pred=[rollout(m,e) for m in models[:5]]
        if len(pred)>=2 and all(p is not None for p in pred):scores[e]=float(np.mean(np.var(pred,axis=0)))
    return max(scores,key=scores.get) if scores else None

def audit(model,data,threshold=.035):
    data=np.asarray(data,float)
    if data.ndim!=2 or data.shape[1]!=4 or not len(data) or not np.isfinite(data).all():return {'accepted':False,'rmse':None}
    err=data[:,3]-model.predict(*data[:,:3].T);rmse=float(np.sqrt(np.mean(err**2)))
    return {'accepted':bool(np.isfinite(rmse) and rmse<=threshold),'rmse':rmse}
