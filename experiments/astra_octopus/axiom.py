"""AXIOM: conditional model criticism, bounded-error feasibility and experiment planning.
Advisory only. No actuator interface; all measurement semantics are assumptions.
"""
from dataclasses import dataclass
from itertools import product, combinations
import numpy as np
from scipy.optimize import linprog
from epistemic import knowledge, Measurement, plan

PARAMS=('F','B','R','C','D','T')
TARGETS={'force':(1,0,0,0,0,0),'bias':(0,1,0,0,0,0)}
# C: ordinary shared artifact; D: isolated channel artifact; T: late change.
ASSUMPTIONS={'C':'ordinary_reference_independent','D':'isolated_reference_independent','T':'stationary_force'}
# Each check is an idealized distinct observation; no claim it exists on real hardware.
CATALOG={
 'passive':Measurement((1,1,0,1,0,0),0),
 'reference':Measurement((1,0,1,1,0,0),1,('reference',)),
 'reference_zero':Measurement((0,0,1,0,0,0),1,('reference',)),
 'primary_zero':Measurement((0,1,0,0,0,0),2,('calibration',)),
 'reverse':Measurement((-1,1,0,-1,0,0),3,('intervention',)),
 'isolated':Measurement((1,0,0,0,1,0),2,('isolated',)),
 'late':Measurement((1,1,0,1,0,1),1,('repeat',)),
 'artifact_check':Measurement((0,0,0,1,0,0),3,('artifact_check',)),
 'isolation_check':Measurement((0,0,0,0,1,0),2,('isolation_check',)),
 'late_isolated':Measurement((1,0,0,0,1,1),2,('isolated','repeat')),
}
@dataclass(frozen=True)
class World:
    free: tuple
    @property
    def name(self):return '+'.join(self.free) or 'strict'
    @property
    def assumptions(self):return tuple(ASSUMPTIONS[k] for k in ASSUMPTIONS if k not in self.free)
    @property
    def bounds(self):return [(None,None)]*3+[(None,None) if k in self.free else (0,0) for k in ASSUMPTIONS]
    def exact_rows(self):return [tuple(int(i==PARAMS.index(k)) for i in range(6)) for k in ASSUMPTIONS if k not in self.free]
WORLDS=tuple(World(tuple(k for k,b in zip(ASSUMPTIONS,bits) if b)) for bits in product((False,True),repeat=3))
FULL=WORLDS[-1]

def constraints(obs):
    if any(k not in CATALOG for k in obs):raise ValueError('unknown measurement')
    a=np.asarray([CATALOG[k].row for k in obs],float).reshape(-1,6)
    y=np.asarray([v[0] for v in obs.values()],float);r=np.asarray([v[1] for v in obs.values()],float)
    if y.shape!=(len(a),) or r.shape!=y.shape or not np.isfinite(y).all() or not np.isfinite(r).all() or np.any(r<0):raise ValueError('invalid observation')
    return a,np.vstack((a,-a)),np.r_[y+r,-y+r]

def solve(world,obs,target=None):
    a,A,b=constraints(obs)
    kw=dict(A_ub=A if len(A) else None,b_ub=b if len(b) else None,bounds=world.bounds,method='highs')
    r=linprog(np.zeros(6),**kw)
    if r.status==2:return {'status':'refuted'}
    if not r.success:return {'status':'solver_failure'}
    if target is None:return {'status':'compatible','witness':r.x.tolist()}
    # Exact structural check before LP endpoints, using EPISTEMIC's rational kernel.
    info=knowledge([tuple(map(int,row)) for row in a]+world.exact_rows(),{'target':target})['targets']['target']
    if not info['identifiable']:return {'status':'compatible','interval':[None,None],'counterexample':info['counterexample']}
    t=np.asarray(target,float);lo=linprog(t,**kw);hi=linprog(-t,**kw)
    if not lo.success or not hi.success:return {'status':'solver_failure'}
    return {'status':'compatible','interval':[float(lo.fun),float(-hi.fun)]}

def audit(obs,targets=TARGETS,worlds=WORLDS,delta=.06):
    if not worlds or not targets:raise ValueError('empty model/target collection')
    statuses={w.name:solve(w,obs) for w in worlds}
    live=[w for w in worlds if statuses[w.name]['status']=='compatible']
    if any(v['status']=='solver_failure' for v in statuses.values()):return {'status':'solver_failure','models':statuses,'targets':{},'assumptions':{}}
    if not live:return {'status':'all_refuted','models':statuses,'targets':{},'assumptions':{}}
    results={}
    for key,t in targets.items():
        sub={w.name:solve(w,obs,t) for w in live}
        if any(v['status']!='compatible' for v in sub.values()):return {'status':'solver_failure','models':statuses,'targets':{},'assumptions':{}}
        intervals=[v['interval'] for v in sub.values()];unbounded=any(None in x for x in intervals)
        hull=[None,None] if unbounded else [min(x[0] for x in intervals),max(x[1] for x in intervals)]
        lo,hi=hull;label='non_identifiable' if unbounded else 'present' if lo>delta or hi<-delta else 'absent' if lo>=-delta and hi<=delta else 'uncertain'
        results[key]={'interval':hull,'label':label,'by_model':sub}
    assumptions={k:('refuted' if not any(k not in w.free for w in live) else 'not_established') for k in ASSUMPTIONS}
    return {'status':'compatible','models':statuses,'targets':results,'assumptions':assumptions}

def recommend(obs,available,budget,targets=TARGETS):
    """Minimum-cost structural identification across the largest (nested) world.
    Does not assume future outcomes; additional checks to challenge presumptions listed separately.
    """
    if budget<0:raise ValueError('negative budget')
    result=plan(list(obs),CATALOG,targets,available,budget)
    # Diagnostic checks are not automatically authorized or executed.
    result['assumption_checks']={a: [k for k in keys if k not in obs and set(CATALOG[k].requires)<=set(available) and CATALOG[k].cost<=budget] for a,keys in {'C':('artifact_check',),'D':('isolation_check',),'T':('late','late_isolated')}.items()}
    return result

def prediction_overlap(obs,action,radius=.01,worlds=WORLDS):
    """Pairwise predicted interval disjointness: sufficient, not necessary, for separation.
    Model nesting makes universal separation impossible; report overlap honestly.
    """
    if action not in CATALOG or not np.isfinite(radius) or radius<0:raise ValueError('invalid experiment')
    vals={w.name:solve(w,obs,CATALOG[action].row) for w in worlds};pairs={}
    for (a,x),(b,y) in combinations(vals.items(),2):
        if x['status']!='compatible' or y['status']!='compatible':continue
        i,j=x['interval'],y['interval']
        pairs[a+' / '+b]=bool(None not in i+j and (i[1]+2*radius<j[0] or j[1]+2*radius<i[0]))
    return {'predictions':vals,'guaranteed_separation':pairs}

def challenge(obs,available,budget):
    """For each zero-effect assumption, find the cheapest design that makes its
    violation estimable, plus the conditional prediction for direct checks.
    No guarantee that the effect is nonzero or measurable at finite precision.
    """
    report=audit(obs)
    if report['status']!='compatible':return {'status':report['status'],'checks':{}}
    out={}
    for key in ASSUMPTIONS:
        t={key:tuple(int(p==key) for p in PARAMS)}
        p=plan(list(obs),CATALOG,t,available,budget)
        estimates=solve(FULL,obs,t[key]);out[key]={'assumption':ASSUMPTIONS[key], 'state':report['assumptions'][key], 'current_effect':estimates,'plan':p}
    return {'status':'compatible','checks':out}
