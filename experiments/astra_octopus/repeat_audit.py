"""Independent repeat of the selected design; doubles sampling, not an actuator interface."""
import json
from collections import Counter
import numpy as np
from causal import N,SIGMA,infer
from benchmark_causal import case,run,SCENARIOS

def repeat_check(first,second):
    if set(first)!=set(second) or not first:return False
    if any(np.asarray(v).shape!=(N,) or not np.isfinite(v).all() for d in (first,second) for v in d.values()):return False
    threshold=4*SIGMA*np.sqrt(2/N)
    return bool(all(abs(np.mean(first[k])-np.mean(second[k]))<=threshold for k in first))

def stress(seeds=100,start=23000):
    results={}
    for s in SCENARIOS:
        rows=[]
        for seed in range(start,start+seeds):
            original=run(s,seed,'adaptive');names=original['experiments'];_,a,*_=case(s,seed);_,b,*_=case(s,seed,repeat=1)
            # Repeat only when initial verdict would otherwise assert a cause.
            repeat=original['verdict'] in ('force','bias','both','neither')
            stable=repeat_check({n:a[n] for n in names},{n:b[n] for n in names}) if repeat else None
            verdict='unstable_rejected' if stable is False else original['verdict']
            rows.append({'seed':seed,'before':original['verdict'],'after':verdict,'truth':original['truth'],'repeat':repeat,'cost':original['cost']*(2 if repeat else 1),'motion':original['motion']*(2 if repeat else 1)})
        results[s]={'before':dict(Counter(r['before'] for r in rows)),'after':dict(Counter(r['after'] for r in rows)),'mean_cost':float(np.mean([r['cost'] for r in rows])),'rows':rows}
    return results
if __name__=='__main__':print(json.dumps(stress(),indent=2))
