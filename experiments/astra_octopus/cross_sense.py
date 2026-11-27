"""Four-modal consistency gate. Simulation research, not a safety-certified controller."""
import math
from itertools import combinations
from statistics import median
from sensor_guard import clamp


def consensus(values, minimum):
    """Unique maximal interval clique; refuse competing hypotheses of equal size."""
    vals={k:(x,r) for k,(x,r) in values.items() if math.isfinite(x) and math.isfinite(r) and r>=0}
    for n in range(len(vals),minimum-1,-1):
        matches=[]
        for keys in combinations(vals,n):
            lo=max(vals[k][0]-vals[k][1] for k in keys)
            hi=min(vals[k][0]+vals[k][1] for k in keys)
            if lo<=hi: matches.append((keys,lo,hi))
        if matches:
            if len(matches)!=1:return None,()
            keys,lo,hi=matches[0]
            return min(hi,max(lo,median(vals[k][0] for k in keys))),keys
    return None,()

class CrossSense:
    def __init__(self, x0=0.,v0=0.,dt=.01):
        self.dt=dt;self.tick=-1;self.paths={k:[x0,v0,True] for k in ('imu','force')}
        self.frame=None;self.prev_frame=None;self.streak=0
    def step(self, encoder, imu_accel, net_force, frame, goal):
        self.tick+=1; t=self.tick*self.dt
        # Acceleration samples represent the previous integration interval.
        for key,a in [('imu',imu_accel),('force',net_force)]:
            state=self.paths[key]
            if not math.isfinite(a):state[2]=False
            if self.tick and state[2]:
                state[1]+=self.dt*a;state[0]+=self.dt*state[1]
        if frame is not None:
            stamp,p=frame
            if isinstance(stamp,int) and stamp==self.tick and math.isfinite(p) and (self.frame is None or stamp>self.frame[0]):
                self.prev_frame,self.frame=self.frame,(stamp,p)
        pos={};vel={}
        if math.isfinite(encoder[0]):pos['encoder']=(encoder[0],.035)
        if math.isfinite(encoder[1]):vel['encoder']=(encoder[1],.06)
        for key,(p,v,ok) in self.paths.items():
            if ok:
                # Conservative finite-horizon uncertainty; no automatic reset from encoder.
                pos[key]=(p,.035+.003*t+.0005*t*t)
                vel[key]=(v,.045+.004*t)
        if self.frame and self.prev_frame:
            stamp,p=self.frame; old_stamp,old_p=self.prev_frame
            age=(self.tick-stamp)*self.dt; interval=(stamp-old_stamp)*self.dt
            if age<=.15 and 0<interval<=.2:
                speed=(p-old_p)/interval
                pos['vision']=(p+speed*age,.045+.9*age)
                vel['vision']=(speed,.15+5*(age+interval/2))
        p,pk=consensus(pos,3);v,vk=consensus(vel,3)
        # Require the same three modalities to support both position and velocity.
        common=set(pk)&set(vk)
        good=p is not None and v is not None and len(common)>=3 and math.isfinite(goal)
        self.streak=min(5,self.streak+1) if good else 0
        if self.streak<5:return 0.,'fallback',tuple(sorted(common))
        return clamp(10*(goal-p)-4*v),'normal' if len(common)==4 else 'degraded',tuple(sorted(common))
