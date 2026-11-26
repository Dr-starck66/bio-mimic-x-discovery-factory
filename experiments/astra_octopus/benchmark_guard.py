"""Paired simulation, identical sensor faults in both modes."""
import argparse,json,math,random,statistics
from benchmark import N, DT, KP, KD, K, UMAX, target
from sensor_guard import Guard,AnchoredGuard,clamp
SCENARIOS=('nominal','spike','drift','freeze','nan','velocity_bias','dual_position','mixed','all_position_drift','all_velocity_missing','coherent_fault','anchor_fault','anchor_missing','all_coherent')
STEPS=1200

def run(seed,scenario,protected):
    rng=random.Random(seed); x=[0.]*N; v=[0.]*N; guards=[(AnchoredGuard if protected==2 else Guard)(0.,DT) for _ in x]
    fallback=detected=false_alerts=unsafe=0; squared=0.; fault_squared=0.; frozen=0.
    for k in range(STEPS):
        t=k*DT; active=400<=k<700; controls=[]
        for i in range(N):
            ps=[x[i]+rng.gauss(0,.003) for _ in range(3)]; vs=[v[i]+rng.gauss(0,.005) for _ in range(3)]
            fault=active and i==0 and scenario!='nominal'
            if i==0 and k==400: frozen=ps[0]
            if fault:
                if scenario=='spike':ps[0]+=2 if k%2 else -2
                elif scenario=='drift':ps[0]+=(k-400)*.003
                elif scenario=='freeze':ps[0]=frozen
                elif scenario=='nan':ps[0]=float('nan')
                elif scenario=='velocity_bias':vs[0]+=2
                elif scenario=='dual_position':ps[0]+=1.;ps[1]+=1.
                elif scenario=='mixed':ps[0]+=1.;vs[0]-=2.
                elif scenario=='all_position_drift':ps=[p+(k-400)*.003 for p in ps]
                elif scenario=='all_velocity_missing':vs=[float('nan')]*3
                elif scenario in ('coherent_fault','all_coherent'):
                    d=(k-400)*DT*.4;ps=[p+d for p in ps];vs=[w+.4 for w in vs]
            goal=target(t,i)
            # Separate random stream unnecessary: deterministic independent anchor noise.
            anchor=x[i]+.002*math.sin(1.37*t+i) if k%10==0 else None
            if fault and anchor is not None:
                if scenario=='anchor_fault':anchor+=1.
                elif scenario=='anchor_missing':anchor=None
                elif scenario=='all_coherent':anchor+=(k-400)*DT*.4
            if protected==2: u,status=guards[i].step(ps,vs,goal,anchor)
            elif protected: u,status=guards[i].step(ps,vs,goal)
            else: u,status=clamp(KP*(goal-ps[0])-KD*vs[0],UMAX),'normal'
            controls.append(u); fallback+=status=='fallback'
            if fault: detected+=status!='normal'
            if scenario=='nominal' and k>=5:false_alerts+=status!='normal'
            unsafe+=not math.isfinite(u) or abs(u)>UMAX
        a=[controls[i]-.7*v[i]+K*(x[(i-1)%N]+x[(i+1)%N]-2*x[i])+rng.gauss(0,.3) for i in range(N)]
        for i in range(N):
            v[i]+=DT*a[i];x[i]+=DT*v[i];e=x[i]-target(t+DT,i);squared+=e*e
            if active and i==0:fault_squared+=e*e
    return dict(rmse=math.sqrt(squared/(N*STEPS)),fault_rmse=math.sqrt(fault_squared/300),detected=detected/300,false_alerts=false_alerts,fallback=fallback,unsafe=unsafe)

def benchmark(seeds):
    out={}
    for s in SCENARIOS:
        modes={}
        for protected in (0,1,2):
            runs=[run(i,s,protected) for i in range(seeds)]
            modes[('raw','guarded','anchored')[protected]]={key:statistics.mean(r[key] for r in runs) for key in runs[0]}
        out[s]=modes
    tests={
        'finite_bounded':all(m['unsafe']==0 for row in out.values() for m in row.values()),
        'nominal_no_false_alarm':out['nominal']['guarded']['false_alerts']==0,
        'single_fault_rmse':all(out[s]['guarded']['fault_rmse']<out[s]['raw']['fault_rmse'] for s in ('spike','drift','freeze','nan','velocity_bias','mixed')),
        'dual_position_fallback':out['dual_position']['guarded']['fallback']>=300,
        'velocity_loss_fallback':out['all_velocity_missing']['guarded']['fallback']>=300,
        'coherent_fault_negative_control':out['coherent_fault']['guarded']['detected']<.1,
        'anchor_detects_coherent_fault':out['coherent_fault']['anchored']['detected']>.8,
        'anchor_nominal_no_false_alarm':out['nominal']['anchored']['false_alerts']==0,
        'anchor_missing_fallback':out['anchor_missing']['anchored']['detected']>.9,
        'anchor_common_mode_negative_control':out['all_coherent']['anchored']['detected']<.1,
    }
    return dict(seeds=seeds,scenarios=out,tests=tests)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=10);args=p.parse_args();print(json.dumps(benchmark(args.seeds),indent=2))
