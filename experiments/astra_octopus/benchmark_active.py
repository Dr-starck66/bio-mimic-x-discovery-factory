"""Holdout paired active/passive gain diagnosis, independent permission assumed in simulation."""
import argparse,json,math,random,statistics
from active_doubt import *
from cross_sense import CrossSense
SCENARIOS=('nominal','encoder_gain','vision_gain','imu_gain','effort_gain','actuator_low','all_gain','common_offset','double_gain','high_noise','no_permission','near_boundary','permit_revoked','missing_imu')
def run(seed,scenario,active):
    rng=random.Random(seed);mass=rng.uniform(.9,1.1);damping=rng.uniform(.05,.25);spring=rng.uniform(.05,.3)
    p=Permit(scenario!='no_permission',True,0.,.04 if scenario=='near_boundary' else .18,.015,1.2,.55)
    # Existing gate is exercised at rest; even nominal consensus cannot establish response to motion.
    gate=CrossSense()
    for k in range(25):_,status,_=gate.step((0.,0.),0.,0.,(k,0.) if k%10==0 else None,0.)
    supervisor=ActiveDoubt(seed,status,True,p);x=v=0.;max_x=max_v=0.; commands=[]; readings={k:[] for k in CHANNELS};after_revoke=0
    for k in range(COUNT):
        if scenario=='permit_revoked' and k>=15:p=Permit(False,True,0.,.18,.015,1.2,.55)
        u=supervisor.command(p) if active else 0.
        commands.append(u);after_revoke+=int(k>=15 and scenario=='permit_revoked' and u!=0)
        a=(u*(.2 if scenario=='actuator_low' else 1.)-damping*v-spring*x)/mass+rng.gauss(0,.015)
        v+=DT*a;x+=DT*v;max_x=max(max_x,abs(x));max_v=max(max_v,abs(v))
        scale=8 if scenario=='high_noise' else 1
        samples={'encoder':x+rng.gauss(0,.00015*scale),'vision':x+rng.gauss(0,.00025*scale),'imu':a+rng.gauss(0,.025*scale),'effort':mass*a+rng.gauss(0,.035*scale)}
        for ch in CHANNELS:
            if scenario==ch+'_gain' or scenario=='all_gain' or (scenario=='double_gain' and ch in ('encoder','vision')):samples[ch]*=.2
            if scenario=='common_offset':samples[ch]+=.3
        if scenario=='missing_imu':samples['imu']=float('nan')
        for ch in CHANNELS:readings[ch].append(samples[ch])
        if active:supervisor.observe(samples)
    result=supervisor.result()[0] if active else diagnose(commands,readings)[0]
    expected={'nominal':'response_consistent','common_offset':'response_consistent','high_noise':'response_consistent','actuator_low':'low_response_ambiguous','all_gain':'low_response_ambiguous','double_gain':'inconclusive','missing_imu':'inconclusive'}.get(scenario,'suspect_'+scenario.removesuffix('_gain') if scenario.endswith('_gain') else 'inconclusive')
    return dict(result=result,expected=expected,correct=result==expected,nonzero=sum(u!=0 for u in commands),max_x=max_x,max_v=max_v,after_revoke=after_revoke,external=supervisor.state if active else 'passive')
def benchmark(seeds,start):
    out={}
    for scenario in SCENARIOS:
        out[scenario]={}
        for mode in ('passive','active'):
            runs=[run(i,scenario,mode=='active') for i in range(start,start+seeds)]
            out[scenario][mode]=dict(counts={r:sum(x['result']==r for x in runs) for r in sorted(set(x['result'] for x in runs))},correct=sum(x['correct'] for x in runs),nonzero=sum(x['nonzero'] for x in runs),max_x=max(x['max_x'] for x in runs),max_v=max(x['max_v'] for x in runs),after_revoke=sum(x['after_revoke'] for x in runs))
    tests={'nominal':out['nominal']['active']['correct']>=.95*seeds,'single_faults':all(out[s]['active']['correct']>=.9*seeds for s in ('encoder_gain','vision_gain','imu_gain','effort_gain')),'ambiguous_not_jam_claim':out['all_gain']['active']['correct']>=.9*seeds and out['actuator_low']['active']['correct']>=.9*seeds,'denied_zero':all(out[s]['active']['nonzero']==0 for s in ('no_permission','near_boundary')),'revoked_zero':out['permit_revoked']['active']['after_revoke']==0,'bounded_simulated_motion':all(r['active']['max_x']<.18 and r['active']['max_v']<.55 for r in out.values()),'offset_negative_control':out['common_offset']['active']['counts'].get('response_consistent',0)>=.95*seeds}
    return dict(seeds=seeds,start=start,scenarios=out,tests=tests)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=100);p.add_argument('--start',type=int,default=1000);a=p.parse_args();print(json.dumps(benchmark(a.seeds,a.start),indent=2))
