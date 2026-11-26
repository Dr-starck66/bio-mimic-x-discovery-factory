"""Independent force witness; advisory validation, no hardware interface."""
import numpy as np
from causal import classify, N

SIGMA=.025
GAIN=(.9,1.1)
DRIFT_LIMIT=.04

def witness(before, loaded, after, *, available=True):
    if not available:return {'status':'unavailable'}
    blocks=[np.asarray(b,dtype=float) for b in (before,loaded,after)]
    if any(b.shape!=(N,) or not np.isfinite(b).all() for b in blocks):return {'status':'invalid'}
    z0,y,z1=map(np.mean,blocks)
    if abs(z1-z0)>DRIFT_LIMIT:return {'status':'unstable_zero'}
    # Linear zero drift is assumed; independently bounded positive gain.
    d=y-(z0+z1)/2
    r=4*SIGMA*np.sqrt(1.5/N)
    endpoints=[v/g for v in (d-r,d+r) for g in GAIN]
    return {'status':'valid','interval':[float(min(endpoints)),float(max(endpoints))]}

def verify(initial, result):
    verdict=initial.get('verdict','invalid')
    if verdict not in ('force','bias','both','neither'):return verdict
    if result.get('status')!='valid':return 'unverified'
    old=initial['intervals']['force'];new=result['interval']
    if max(old[0],new[0])>min(old[1],new[1]):return 'witness_conflict'
    if classify(new)!=classify(old) or classify(new)=='uncertain':return 'unverified'
    return verdict
