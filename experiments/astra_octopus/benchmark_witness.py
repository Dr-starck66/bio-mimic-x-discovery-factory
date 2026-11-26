"""Paired synthetic tests; independent witness may itself fail. No motion executed."""
import json
from collections import Counter
import numpy as np
from benchmark_causal import run
from independent_check import witness,verify,N

CASES={'force':'force','bias':'bias','both':'both','neither':'neither','reference_biased':'reference_biased','no_external':'no_external','coherent_deception':'coherent_deception','all_channels_coherent':'coherent_deception','witness_unavailable':'force','witness_zero_drift':'force','witness_gain_outside_bound':'force','witness_transient_bias':'force','weak_force':'weak_force'}

def trial(s,seed):
    initial=run(CASES[s],seed,'adaptive');rng=np.random.default_rng(seed+800000);F=initial['force'];g=rng.uniform(.9,1.1);z=rng.uniform(-.3,.3);drift=rng.uniform(-.015,.015)
    if s=='all_channels_coherent':F=.24
    if s=='witness_zero_drift':drift=.12
    if s=='witness_gain_outside_bound':g=.45
    transient=.3 if s=='witness_transient_bias' else 0.
    blocks=[z+rng.normal(0,.02,N),z+drift/2+g*F+transient+rng.normal(0,.02,N),z+drift+rng.normal(0,.02,N)]
    w=witness(*blocks,available=s!='witness_unavailable');final=verify(initial,w)
    return dict(seed=seed,truth=initial['truth'],before=initial['verdict'],after=final,witness=w)

def benchmark(seeds=100,start=31000):
    out={}
    for s in CASES:
        rows=[trial(s,i) for i in range(start,start+seeds)]
        out[s]={'before':dict(Counter(r['before'] for r in rows)),'after':dict(Counter(r['after'] for r in rows)),'correct_after':sum(r['truth']==r['after'] for r in rows),'rows':rows}
    return out
if __name__=='__main__':print(json.dumps(benchmark(),indent=2))
