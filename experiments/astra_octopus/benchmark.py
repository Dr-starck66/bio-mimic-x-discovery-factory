"""ASTRA OCTOPUS: paired benchmark of local vs networked PD control.
Python standard library only. Dimensionless coupled actuator model, not hardware.
"""
import math, random, statistics, json, argparse
N=8; DT=.01; STEPS=1500; KP=10.; KD=4.; K=.8; UMAX=12.
SCENARIOS={'ideal':(0,0.,False,0.),'delay_100ms':(10,0.,False,0.),'loss_30pct':(0,.3,False,0.),'outage_2s':(0,0.,True,0.),'local_sensor_fault':(0,0.,False,1.5)}
def target(t,i): return math.sin(0.9*t+i*math.pi/4)
def run(seed, mode, scenario):
    delay,loss,outage,bias=SCENARIOS[scenario]; rng=random.Random(seed)
    x=[0.]*N; v=[0.]*N; u=[0.]*N; queue={}; estimate=[0.]*N; alarms=0; err=effort=0.; packets=0; peak=0.; saturated=0
    phases=[rng.uniform(-.1,.1) for _ in range(N)]
    for k in range(STEPS):
        t=k*DT; goal=[target(t,i) for i in range(N)]
        # Shared preplanned reference and paired disturbances; both controllers use identical PD law.
        disturb=[rng.gauss(0,.3)+(3. if 5<=t<5.4 and i==2 else 0.) for i in range(N)]
        drops=[rng.random()<loss for _ in range(N)]
        measured=[x[i]+(bias if mode in ('local','guarded') and i==0 and 5<=t<7 else 0.) for i in range(N)]
        def clip(z):return max(-UMAX,min(UMAX,z))
        if mode in ('local','guarded'):
            if mode=='guarded':
                for i in range(N):
                    # Independent velocity-based predictor, with deterministic sensor error.
                    if k: estimate[i]+=DT*(v[i]+.02*math.sin(1.7*t+i))
                    if abs(measured[i]-estimate[i])>.15:
                        measured[i]=estimate[i]; alarms+=1
                    else: estimate[i]=measured[i]
            u=[clip(KP*(goal[i]-measured[i])-KD*v[i]) for i in range(N)]
        else:
            # Effective feedback round-trip delay. Per-actuator state/command transaction.
            if not (outage and 5<=t<7):
                for i in range(N):
                    packets+=2 # attempted state and command messages, not bytes
                    if not drops[i]:
                        queue.setdefault(k+delay,[]).append((i,clip(KP*(goal[i]-x[i])-KD*v[i])))
            for i,val in queue.pop(k,[]):u[i]=val
        # Ring coupling; same physical plant for both modes.
        a=[u[i]-.7*v[i]+K*(x[(i-1)%N]+x[(i+1)%N]-2*x[i])+disturb[i]+phases[i] for i in range(N)]
        for i in range(N):
            v[i]+=DT*a[i]; x[i]+=DT*v[i]
        if k>=100:
            for i in range(N):
                e=x[i]-goal[i]; err+=e*e; effort+=u[i]**2*DT; peak=max(peak,abs(e)); saturated+=int(abs(u[i])>=UMAX)
    return {'rmse':math.sqrt(err/((STEPS-100)*N)), 'effort_proxy':effort,'peak_error':peak,'feedback_messages':packets,'saturation_fraction':saturated/((STEPS-100)*N),'guard_alarms':alarms}
def benchmark(seeds):
    results={}
    for s in SCENARIOS:
        pairs=[(run(seed,'central',s),run(seed,'local',s),run(seed,'guarded',s)) for seed in range(seeds)]
        means={m:{k:statistics.mean(p[j][k] for p in pairs) for k in pairs[0][j]} for j,m in enumerate(['central','local','guarded'])}
        diffs=[a['rmse']-b['rmse'] for a,b,_ in pairs]
        means['paired_rmse_delta']=statistics.mean(diffs)
        means['local_wins']=sum(d>1e-12 for d in diffs)
        results[s]=means
    assert abs(results['ideal']['paired_rmse_delta'])<1e-12, 'ideal parity failed'
    assert results['outage_2s']['paired_rmse_delta']>0, 'outage hypothesis failed'
    assert results['local_sensor_fault']['paired_rmse_delta']<0, 'negative control failed'
    assert results['local_sensor_fault']['guarded']['rmse'] < results['local_sensor_fault']['local']['rmse'], 'guard failed'
    assert results['ideal']['guarded']['guard_alarms']==0, 'false alarm'
    assert abs(results['ideal']['guarded']['rmse']-results['ideal']['local']['rmse'])<1e-12, 'guard ideal parity failed'
    return {'seeds':seeds,'dt':DT,'steps':STEPS,'actuators':N,'scenarios':results,'assertions':'PASS: ideal parity, outage advantage, asymmetric local sensor fault disadvantage, guard recovery, no ideal false alarm, guard ideal parity'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=30);a=p.parse_args();print(json.dumps(benchmark(a.seeds),indent=2))
