"""Synthetic bounded error experiments; no physical interventions."""
import json
from itertools import combinations
import numpy as np
from epistemic import *

def bench(seeds=100,start=42000):
    out={};T={'F':(1,0,0,0),'B':(0,1,0,0)};M=catalog(True)
    designs={'passive':['passive'],'repeat':['passive']*10,'all_ordinary':[k for k in M if k!='isolated_force'],'isolated':['passive','isolated_force'],'complete':['passive','primary_zero','isolated_force']}
    for name,keys in designs.items():
        rows=[M[k].row for k in keys];info=knowledge(rows,T);counts={};cover=0
        for i in range(seeds):
            rng=np.random.default_rng(start+i)
            truth=np.array([rng.choice([0.,.24,-.24]),rng.choice([0.,.24,-.24]),rng.uniform(-.3,.3),rng.uniform(-.3,.3)])
            err=rng.uniform(-.01,.01,len(rows));y=np.array(rows)@truth+err
            result=bounds(rows,y,[.01]*len(rows),T);assert result['status']=='feasible'
            for k,idx in [('F',0),('B',1)]:
                ci=result['intervals'][k];cover+=int((ci[0] is None or ci[0]-1e-8<=truth[idx]) and (ci[1] is None or truth[idx]<=ci[1]+1e-8))
                label=assess(ci);counts[k+':'+label]=counts.get(k+':'+label,0)+1
                if label in ('present','absent'):assert label==('absent' if truth[idx]==0 else 'present')
        out[name]={'rank':info['rank'],'targets':info['targets'],'classifications':counts,'covered':cover,'total_intervals':2*seeds}
    plans={}
    for common in (False,True):
        m=catalog(common);t={'F':(1,0,0)+( (0,) if common else ()),'B':(0,1,0)+( (0,) if common else ())}
        for name,avail in [('none',()),('external',('external',)),('ordinary',('external','motion','witness')),('isolated',('external','motion','witness','isolated'))]:
            plans[f'{common}:{name}']=plan(['passive'],m,t,avail,5)
        plans[f'{common}:isolated_budget6']=plan(['passive'],m,t,('external','motion','witness','isolated'),6)
    # Exact certificate checks across every subset, including all common-mode designs.
    checks=0
    for n in range(len(M)+1):
        for subset in combinations(M,n):
            rows=[M[k].row for k in subset];info=knowledge(rows,T)
            for k,v in info['targets'].items():
                if v['counterexample'] is not None:
                    z=list(map(Q,v['counterexample']));assert all(dot(r,z)==0 for r in rows) and dot(T[k],z)!=0
                    checks+=1
    return {'seeds':seeds,'start':start,'designs':out,'plans':plans,'exact_counterexamples_checked':checks}
if __name__=='__main__':print(json.dumps(bench(),indent=2))
