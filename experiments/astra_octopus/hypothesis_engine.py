"""Finite hypothesis library, exact categorical information gain, advisory only."""
from itertools import product
from math import log2, erf, sqrt, isfinite
from functools import lru_cache
from active_doubt import CHANNELS, permitted
H=('nominal',)+tuple(k+'_gain' for k in CHANNELS)+('actuator_low','all_gain','common_offset','double_gain','unknown')
COST={'static':1,'pulse':2,'external_pulse':4}
PRIOR=dict.fromkeys(H, .09); PRIOR['nominal']=.19  # sums to 1

def entropy(p):return -sum(x*log2(x) for x in p if x>0)
def probs(mu,sd,edges):
    c=[0.]+[.5*(1+erf((e-mu)/(sd*sqrt(2)))) for e in edges]+[1.]
    q=[max(1e-5,b-a) for a,b in zip(c,c[1:])];return tuple(x/sum(q) for x in q)
@lru_cache(None)
def likelihood(exp,h):
    if exp=='static':
        return {(i,):p for i,p in enumerate((1/3,)*3 if h=='unknown' else probs(.3 if h=='common_offset' else 0.,.025,(-.12,.12)))}
    names=CHANNELS+(('external',) if exp=='external_pulse' else ())
    distributions=[]
    for k in names:
        mu=.2 if h=='actuator_low' or (k!='external' and (h=='all_gain' or h==k+'_gain' or (h=='double_gain' and k in ('encoder','vision')))) else 1.
        distributions.append((1/3,)*3 if h=='unknown' else probs(mu,.12,(.5,1.5)))
    return {o:__import__('math').prod(d[j] for d,j in zip(distributions,o)) for o in product(range(3),repeat=len(names))}

def update(p,exp,outcome):
    if outcome is None or outcome not in likelihood(exp,H[0]):return None
    weights={h:p[h]*likelihood(exp,h)[outcome] for h in H};z=sum(weights.values())
    return {h:w/z for h,w in weights.items()} if z>0 else None

def information(p,exp):
    # I(H;O) = H(O) - sum_h p(h) H(O|h)
    models=[likelihood(exp,h) for h in H];mix=[sum(p[h]*m[o] for h,m in zip(H,models)) for o in models[0]]
    return max(0.,entropy(mix)-sum(p[h]*entropy(m.values()) for h,m in zip(H,models)))

class Engine:
    def __init__(self):self.p=PRIOR.copy();self.used=set();self.spent=0;self.trace=[];self.pending=None;self.invalid=False
    def verdict(self):
        h=max(self.p,key=self.p.get)
        return h if not self.invalid and self.pending is None and h!='unknown' and self.p[h]>=.95 else 'inconclusive'
    def choose(self,permit,external_available=True,policy='adaptive',budget=7):
        if self.pending is not None or self.invalid or self.verdict()!='inconclusive':return None
        allowed=[e for e,c in COST.items() if e not in self.used and self.spent+c<=budget and (e=='static' or permitted(permit)) and (e=='pulse' or external_available)]
        if not allowed:return None
        scores={e:information(self.p,e)/COST[e] for e in allowed}
        if policy=='adaptive':
            e=max(allowed,key=lambda e:scores[e]);return e if scores[e]>1e-4 else None
        order=('pulse','static','external_pulse') if policy=='fixed_pulse' else ('static','pulse','external_pulse')
        return next(e for e in order if e in allowed)
    def begin(self,e,permit,external_available=True,budget=7):
        if self.invalid or self.pending is not None or self.verdict()!='inconclusive' or e not in COST or e in self.used or self.spent+COST[e]>budget or (e!='static' and not permitted(permit)) or (e!='pulse' and not external_available):return False
        self.pending=e;self.used.add(e);self.spent+=COST[e];return True
    def observe(self,e,outcome):
        if self.pending!=e or self.pending is None:self.invalid=True;return False
        self.pending=None;new=update(self.p,e,outcome)
        if new is None:self.invalid=True;return False
        self.p=new;self.trace.append((e,outcome,self.p.copy()));return True
