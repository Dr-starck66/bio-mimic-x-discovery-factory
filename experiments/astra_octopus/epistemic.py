"""Exact structural identifiability and bounded-error planning; advisory only."""
from fractions import Fraction as Q
from itertools import combinations
from dataclasses import dataclass
import numpy as np
from scipy.optimize import linprog
from causal import ACTIONS

@dataclass(frozen=True)
class Measurement:
    row: tuple
    cost: int
    requires: tuple = ()

def catalog(common=False):
    # C is a hypothetical shared artifact with the same response as F.
    out={n:Measurement(a.row+((a.row[0],) if common else ()),a.cost,
         tuple(k for k,b in [('external',a.external),('motion',a.motion)] if b)) for n,a in ACTIONS.items()}
    out['witness']=Measurement((1,0,0,1) if common else (1,0,0),2,('witness',))
    out['isolated_force']=Measurement((1,0,0,0) if common else (1,0,0),4,('isolated',))
    return out

def nullspace(rows,n):
    a=[[Q(x) for x in row] for row in rows]; piv=[]; i=0
    for j in range(n):
        k=next((k for k in range(i,len(a)) if a[k][j]),None)
        if k is None:continue
        a[i],a[k]=a[k],a[i];d=a[i][j];a[i]=[x/d for x in a[i]]
        for k in range(len(a)):
            if k!=i:
                d=a[k][j];a[k]=[x-d*y for x,y in zip(a[k],a[i])]
        piv.append(j);i+=1
    basis=[]
    for j in range(n):
        if j in piv:continue
        z=[Q(0)]*n;z[j]=Q(1)
        for k,p in enumerate(piv):z[p]=-a[k][j]
        basis.append(tuple(z))
    return basis

def dot(a,b):return sum(x*y for x,y in zip(a,b))

def knowledge(rows,targets):
    n=len(next(iter(targets.values())))
    if n==0 or any(len(r)!=n for r in rows) or any(len(r)!=n for r in targets.values()):raise ValueError('dimension mismatch')
    basis=nullspace(rows,n);out={}
    for name,t in targets.items():
        z=next((z for z in basis if dot(t,z)),None)
        out[name]={'identifiable':z is None,'counterexample':None if z is None else [str(x) for x in z]}
    return {'rank':n-len(basis),'nullity':len(basis),'targets':out,'nullspace':[[str(x) for x in z] for z in basis]}

def plan(existing,measurements,targets,available,budget):
    """Exhaustive least-cost full design; otherwise report best attainable coverage."""
    if budget<0:raise ValueError('negative budget')
    rows=[measurements[k].row for k in existing]
    options=[k for k,m in measurements.items() if k not in existing and set(m.requires)<=set(available)]
    choices=[]
    for i in range(len(options)+1):
        for s in combinations(options,i):
            c=sum(measurements[k].cost for k in s)
            if c>budget:continue
            info=knowledge(rows+[measurements[k].row for k in s],targets)
            coverage=sum(v['identifiable'] for v in info['targets'].values())
            choices.append(((-coverage,c,len(s),s),info))
    score,info=min(choices,key=lambda z:z[0]);n=-score[0]
    return {'status':'complete' if n==len(targets) else 'partial' if n else 'impossible','actions':list(score[3]),'cost':score[1],'knowledge':info}

def bounds(rows,y,radius,targets):
    """Feasible target interval under declared deterministic error boxes, not a confidence level."""
    n=len(next(iter(targets.values())));a=np.asarray(rows,float).reshape(-1,n);y=np.asarray(y,float);r=np.asarray(radius,float)
    if y.shape!=(len(a),) or r.shape!=y.shape or not np.isfinite(a).all() or not np.isfinite(y).all() or not np.isfinite(r).all() or np.any(r<0):raise ValueError('invalid data')
    A=np.vstack([a,-a]);b=np.r_[y+r,-y+r];kw=dict(A_ub=A,b_ub=b,bounds=[(None,None)]*n,method='highs')
    feasible=linprog(np.zeros(n),**kw)
    if feasible.status==2:return {'status':'inconsistent','intervals':{}}
    if not feasible.success:return {'status':'solver_failure','intervals':{}}
    out={}
    exact=knowledge(rows,targets)
    for k,t in targets.items():
        if not exact['targets'][k]['identifiable']:
            out[k]=[None,None];continue
        t=np.asarray(t,float);lo=linprog(t,**kw);hi=linprog(-t,**kw)
        if lo.status not in (0,3) or hi.status not in (0,3):return {'status':'solver_failure','intervals':{}}
        out[k]=[float(lo.fun) if lo.success else None,float(-hi.fun) if hi.success else None]
    return {'status':'feasible','intervals':out}

def assess(interval,delta=.06):
    lo,hi=interval
    if lo is None or hi is None:return 'unbounded'
    if lo>delta or hi<-delta:return 'present'
    if lo>=-delta and hi<=delta:return 'absent'
    return 'uncertain'
