"""Paired held-out random seeds; synthetic single-axis dynamics and independent external reference."""
import argparse,json,random,statistics,math
from active_doubt import ActiveDoubt,Permit,CHANNELS,COUNT,DT, gain
from hypothesis_engine import Engine,H
SCENARIOS=H[:-1]+('out_of_model_high_gain','out_of_model_mild_gain','denied','revoked','no_external')

def observe(e,h,seed,permit):
    rng=random.Random(seed+{'static':0,'pulse':100000,'external_pulse':200000}[e]); mass=rng.uniform(.85,1.15); damping=rng.uniform(.04,.3); spring=rng.uniform(.02,.35)
    if e=='static':
        # External absolute position reference: independent measurement, no excitation.
        diff=(.3 if h=='common_offset' else 0.)+rng.gauss(0,.018)
        return (0 if diff<-.12 else 2 if diff>.12 else 1,),0
    sup=ActiveDoubt(seed,'fallback',False,permit);x=v=0.;ref=[];commands=[];external=[];rx=rv=0.;p=permit
    for k in range(COUNT):
        if h=='revoked' and k>=15:p=Permit(False,True,0.,.18,.015,1.2,.55)
        u=sup.command(p);commands.append(u);rv+=DT*u;rx+=DT*rv;ref.append(rx)
        a=(u*(.2 if h=='actuator_low' else 1.)-damping*v-spring*x)/mass+rng.gauss(0,.025)
        v+=DT*a;x+=DT*v
        samples=dict(encoder=x+rng.gauss(0,.00025),vision=x+rng.gauss(0,.0004),imu=a+rng.gauss(0,.04),effort=mass*a+rng.gauss(0,.05))
        for ch in CHANNELS:
            if h==ch+'_gain' or h=='all_gain' or (h=='double_gain' and ch in ('encoder','vision')):samples[ch]*=rng.uniform(.15,.25)
            if h=='common_offset':samples[ch]+=.3
            if h=='out_of_model_high_gain' and ch=='encoder':samples[ch]*=1.9
            if h=='out_of_model_mild_gain' and ch=='encoder':samples[ch]*=.8
        external.append(x+rng.gauss(0,.0002));sup.observe(samples)
    n=sum(u!=0 for u in commands)
    if sup.state!='external_revalidation':return None,n
    _,g=sup.result(); vals=[g[k] for k in CHANNELS]
    if e=='external_pulse':vals.append(gain(external,ref))
    if any(v is None or not math.isfinite(v) for v in vals):return None,n
    return tuple(0 if v<.5 else 2 if v>1.5 else 1 for v in vals),n

def run(h,seed,policy):
    eng=Engine();p=Permit(h!='denied',True,0.,.18,.015,1.2,.55);ext=h!='no_external'; pulses=0; trace=[]
    while (e:=eng.choose(p,ext,policy)) is not None:
        assert eng.begin(e,p,ext);o,n=observe(e,h,seed,p);pulses+=n;trace.append(e)
        if not eng.observe(e,o):break
    truth=h if h in H[:-1] else None
    return dict(verdict=eng.verdict(),correct=eng.verdict()==truth,cost=eng.spent,steps=len(trace),pulses=pulses,trace=trace)

def benchmark(seeds,start):
    out={}; policies=('adaptive','fixed_pulse','fixed_static')
    for h in SCENARIOS:
        out[h]={}
        for policy in policies:
            runs=[run(h,i,policy) for i in range(start,start+seeds)]
            out[h][policy]=dict(correct=sum(r['correct'] for r in runs),abstained=sum(r['verdict']=='inconclusive' for r in runs),cost=statistics.mean(r['cost'] for r in runs),steps=statistics.mean(r['steps'] for r in runs),pulses=statistics.mean(r['pulses'] for r in runs),verdicts={v:sum(r['verdict']==v for r in runs) for v in sorted(set(r['verdict'] for r in runs))},first={v:sum(bool(r['trace']) and r['trace'][0]==v for r in runs) for v in ('static','pulse','external_pulse')})
    summary={p:{'correct':sum(out[h][p]['correct'] for h in H[:-1]),'total':seeds*len(H[:-1]),'mean_cost':statistics.mean(out[h][p]['cost'] for h in H[:-1]),'mean_pulses_ticks':statistics.mean(out[h][p]['pulses'] for h in H[:-1])} for p in policies}
    checks={'budget':all(v['cost']<=7 for row in out.values() for v in row.values()),'denied_zero':all(v['pulses']==0 for v in out['denied'].values()),'revocation':all(v['pulses']<=15 and v['abstained']==seeds for v in out['revoked'].values()),'offset_detected':out['common_offset']['adaptive']['correct']>=.95*seeds,'distinguish_low':all(out[h]['adaptive']['correct']>=.95*seeds for h in ('actuator_low','all_gain')),'high_gain_abstention':out['out_of_model_high_gain']['adaptive']['abstained']>=.95*seeds}
    return dict(seeds=seeds,start=start,summary=summary,checks=checks,scenarios=out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=100);p.add_argument('--start',type=int,default=5000);a=p.parse_args();print(json.dumps(benchmark(a.seeds,a.start),indent=2))
