"""Eight-actuator ring from v0.2; only actuator 0 uses experimental controller.
Force channel is a simulated net-force sensor (unit mass), not motor current alone.
All architectures receive paired exogenous disturbances; trajectories differ.
"""
import math,random,statistics,json,argparse
from benchmark import N,DT,K,target
from sensor_guard import AnchoredGuard,clamp
from cross_sense import CrossSense
SCENARIOS=('nominal','encoder_bias','vision_bias','imu_bias','force_bias','encoder_vision_coherent','encoder_imu_coherent','all_coherent','vision_missing','vision_replay','imu_force_missing','model_force_bias','noise_high')
STEPS=1200

def run(seed,scenario,mode):
    rng=random.Random(seed);x=[0.]*N;v=[0.]*N;prev_a=0.;g=CrossSense();old=AnchoredGuard(0.);last_frame=None
    err=peak=alarm=blocked=nominal_alarm=unsafe=0;bad_accept=0;first=None
    for k in range(STEPS):
        t=k*DT;active=400<=k<700;d=(k-400)*DT if active else 0.
        noise=[rng.gauss(0,1) for _ in range(7)];dist=[rng.gauss(0,.3) for _ in x]
        scale=5 if scenario=='noise_high' else 1
        p=x[0]+noise[0]*.003*scale;speed=v[0]+noise[1]*.005*scale
        ia=prev_a+noise[2]*.025*scale;force=prev_a+noise[3]*.04*scale
        vision=x[0]+noise[4]*.003*scale; frame=(k,vision) if k%10==0 else None
        if active:
            if scenario=='encoder_bias':p+=1.;speed+=.7
            if scenario=='vision_bias' and frame:frame=(k,vision+1.)
            if scenario=='imu_bias':ia+=.6
            if scenario=='force_bias':force+=.6
            if scenario=='model_force_bias':force+=.1
            if scenario in ('encoder_vision_coherent','encoder_imu_coherent','all_coherent'):
                # Coherent fictitious displacement: constant acceleration .6, integrated discretely.
                n=k-399; shift=.6*DT*DT*n*(n+1)/2; dv=.6*DT*n
                p+=shift;speed+=dv
                if scenario in ('encoder_vision_coherent','all_coherent') and frame:frame=(k,vision+shift)
                if scenario in ('encoder_imu_coherent','all_coherent'):ia+=.6
                if scenario=='all_coherent':force+=.6
            if scenario=='vision_missing':frame=None
            if scenario=='vision_replay':frame=last_frame if frame else None
            if scenario=='imu_force_missing':ia=force=float('nan')
        elif frame:last_frame=frame
        goal=target(t,0)
        if mode=='cross':u,status,_=g.step((p,speed),ia,force,frame,goal)
        elif mode=='v02':
            # Three correlated copies (same modality), with the same vision faults.
            u,status=old.step([p]*3,[speed]*3,goal,frame[1] if frame else None)
        else:u,status=clamp(10*(goal-p)-4*speed),'normal'
        controls=[u]+[clamp(10*(target(t,i)-x[i])-4*v[i]) for i in range(1,N)]
        unsafe+=not math.isfinite(u) or abs(u)>12
        if active:
            alarm+=status!='normal';blocked+=status=='fallback'
            if status!='normal' and first is None:first=k-400
            # Diagnostic using truth ONLY in scoring, not controller: command differs by >2 from clean PD.
            bad_accept+=status!='fallback' and abs(u-clamp(10*(goal-x[0])-4*v[0]))>2
        if scenario=='nominal' and k>=20:nominal_alarm+=status!='normal'
        a=[controls[i]-.7*v[i]+K*(x[(i-1)%N]+x[(i+1)%N]-2*x[i])+dist[i] for i in range(N)]
        prev_a=a[0]
        for i in range(N):v[i]+=DT*a[i];x[i]+=DT*v[i]
        if active:
            e=x[0]-target(t+DT,0);err+=e*e;peak=max(peak,abs(e))
    return dict(rmse=math.sqrt(err/300),peak=peak,alarm=alarm/300,blocked=blocked/300,nominal_alarm=nominal_alarm,unsafe=unsafe,bad_accept=bad_accept/300,first_alarm_ms=first*10 if first is not None else 3000)

def benchmark(seeds):
    out={}
    for s in SCENARIOS:
        out[s]={}
        for m in ('raw','v02','cross'):
            runs=[run(i,s,m) for i in range(seeds)]
            out[s][m]={k:statistics.mean(r[k] for r in runs) for k in runs[0]}
    tests={'bounded':all(m['unsafe']==0 for row in out.values() for m in row.values()),'nominal_tracking':out['nominal']['cross']['rmse']<1.1*out['nominal']['raw']['rmse'],'single_encoder_fault':out['encoder_bias']['cross']['bad_accept']<.01,'two_modal_fault':out['encoder_vision_coherent']['cross']['bad_accept']<out['encoder_vision_coherent']['v02']['bad_accept'],'missing_two_blocks':out['imu_force_missing']['cross']['blocked']>.99,'common_mode_negative':out['all_coherent']['cross']['bad_accept']>.1}
    return dict(seeds=seeds,scenarios=out,tests=tests)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=10);a=p.parse_args();print(json.dumps(benchmark(a.seeds),indent=2))
