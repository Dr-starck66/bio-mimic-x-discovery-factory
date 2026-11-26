"""Advisory causal identifiability on residual forces. No actuator interface.
Each experiment assumes stable force/bias and known intervention response.
"""
from dataclasses import dataclass
import numpy as np
from active_doubt import permitted, Permit

@dataclass(frozen=True)
class Action:
    row: tuple
    cost: int
    motion: bool=False
    external: bool=False

# Parameters: physical force F, primary bias B, external reference bias R.
ACTIONS = {
    'passive': Action((1,1,0),0),
    'reference': Action((1,0,1),1,external=True),
    'reference_zero': Action((0,0,1),1,external=True),
    'primary_zero': Action((0,1,0),2,motion=True),
    'reverse': Action((-1,1,0),3,motion=True),
}
TARGET=np.eye(3)[:2]
SIGMA=.025 # declared upper bound, not estimated from test outcomes
N=24

def matrix(names):return np.array([ACTIONS[n].row for n in names],float).reshape(-1,3)

def identifiable(names):
    a=matrix(names); rank=np.linalg.matrix_rank(a) if len(a) else 0
    return tuple(bool(np.linalg.matrix_rank(np.vstack([a,t]))==rank) for t in TARGET)

def eligible(name,permit,external):
    a=ACTIONS[name]
    return (not a.external or external) and (not a.motion or permitted(permit))

def redundant(names):
    # Causal labels require a cross-check: two disjoint alternative routes beyond passive.
    return 'passive' in names and (('primary_zero' in names and 'reverse' in names) or (('reference' in names and 'reference_zero' in names) and ('primary_zero' in names or 'reverse' in names)))

def choose(names,permit,external,budget):
    """Plan least-cost reachable redundant design; otherwise collect identifiable evidence.
    No outcomes from future experiments used. Return only first suggested action.
    """
    from itertools import combinations
    available=[n for n in ACTIONS if n not in names and eligible(n,permit,external)]
    options=[]
    for k in range(1,len(available)+1):
        for subset in combinations(available,k):
            c=sum(ACTIONS[n].cost for n in subset)
            if c>budget:continue
            full=names+list(subset)
            score=(int(redundant(full)),sum(identifiable(full)),-c,-len(subset))
            options.append((score,subset))
    if redundant(names) or not options:return None
    score,subset=max(options,key=lambda o:o[0])
    if not score[0] and score[1]<=sum(identifiable(names)):return None
    # Prefer immediate information, then cheap actions.
    return max(subset,key=lambda n:(sum(identifiable(names+[n])),-ACTIONS[n].cost))

def classify(ci,delta=.06):
    lo,hi=ci
    if lo>delta or hi<-delta:return 'present'
    if lo>=-delta and hi<=delta:return 'absent'
    return 'uncertain'

def infer(observations):
    names=list(observations)
    if not names or any(n not in ACTIONS for n in names) or any(np.asarray(v).shape!=(N,) or not np.isfinite(v).all() for v in observations.values()):return {'verdict':'invalid'}
    a=matrix(names)
    y=np.array([np.mean(observations[n]) for n in names]); p=np.linalg.pinv(a); theta=p@y
    pred=a@theta; residual=y-pred
    # Independent Gaussian sample errors with upper bound SIGMA; conservative 4-sigma contrasts.
    cov=(SIGMA**2/N)*p@p.T
    projector=np.eye(len(a))-a@p
    residual_sd=SIGMA/np.sqrt(N)*np.sqrt(np.maximum(np.diag(projector),0))
    reject=bool(np.any(np.abs(residual)>4*residual_sd+1e-10))
    flags=identifiable(names); intervals={}
    for i,k in enumerate(('force','bias')):
        if flags[i]:
            radius=4*np.sqrt(cov[i,i]); intervals[k]=[float(theta[i]-radius),float(theta[i]+radius)]
    verdict='inconclusive'
    if reject:verdict='model_rejected'
    elif all(flags) and redundant(names):
        f,b=(classify(intervals[k]) for k in ('force','bias'))
        verdict={('present','present'):'both',('present','absent'):'force',('absent','present'):'bias',('absent','absent'):'neither'}.get((f,b),'inconclusive')
    return {'verdict':verdict,'identifiable':list(flags),'redundant':redundant(names),'intervals':intervals,'estimate':{k:float(theta[i]) for i,k in enumerate(('force','bias')) if flags[i]},'max_residual':float(max(abs(residual))),'experiments':names}
