"""Finite-horizon active diagnosis for a simulated single axis, not safety firmware."""
from dataclasses import dataclass
import math, random
from statistics import median
DT=.01; COUNT=40; AMP=.6; DURATION=COUNT*DT
CHANNELS=('encoder','vision','imu','effort')
@dataclass(frozen=True)
class Permit:
    authorized: bool
    isolated: bool
    age: float
    clearance: float  # independently certified distance to nearest boundary
    speed_bound: float
    accel_bound: float # independent bound including disturbances, not a sensor estimate
    speed_limit: float

def permitted(p, remaining=DURATION):
    vals=(p.age,p.clearance,p.speed_bound,p.accel_bound,p.speed_limit,remaining)
    if not p.authorized or not p.isolated or not all(math.isfinite(x) and x>=0 for x in vals):return False
    if p.age>.05 or p.accel_bound<AMP: return False
    return (p.speed_bound*remaining+.5*p.accel_bound*remaining**2 < p.clearance
            and p.speed_bound+p.accel_bound*remaining < p.speed_limit)

def request(status, scheduled, permit):
    if status not in ('normal','degraded','fallback'):return 'external_observation'
    if status=='normal' and not scheduled:return 'no_probe'
    return 'probe' if permitted(permit) else 'external_observation'

def waveform(seed):
    # Balanced pulse: zero nominal terminal velocity AND displacement in an ideal double integrator.
    s=random.Random(seed).choice((-1,1))
    return [s*AMP*(1 if k<10 or k>=30 else -1) for k in range(COUNT)]

def residualize(y):
    # Remove constant and linear trends: baseline offset/velocity is not evidence of gain.
    n=len(y); t=[i-(n-1)/2 for i in range(n)]; mean=sum(y)/n
    slope=sum(a*b for a,b in zip(t,y))/sum(a*a for a in t)
    return [b-mean-slope*a for a,b in zip(t,y)]

def gain(y, ref):
    if len(y)!=len(ref) or not all(math.isfinite(x) for x in y):return None
    a=residualize(ref);b=residualize(y);den=sum(x*x for x in a)
    if den<1e-10:return None
    return sum(x*z for x,z in zip(a,b))/den

def diagnose(commands, readings):
    x=v=0.; ref=[]
    for u in commands:v+=DT*u;x+=DT*v;ref.append(x)
    gains={k:gain(readings[k],ref if k in ('encoder','vision') else commands) for k in CHANNELS}
    valid={k:v for k,v in gains.items() if v is not None}
    if len(valid)<3:return 'inconclusive',gains
    healthy=[k for k,v in valid.items() if .65<=v<=1.35]
    low=[k for k,v in valid.items() if abs(v)<.45]
    if len(healthy)==4:return 'response_consistent',gains
    if len(healthy)==3 and len(valid)==4:return 'suspect_'+next(k for k in valid if k not in healthy),gains
    # Reduced response across modalities is NOT proof of a jam: correlated sensor attenuation also fits.
    if len(low)>=3:return 'low_response_ambiguous',gains
    return 'inconclusive',gains

class ActiveDoubt:
    """Supervisor. Does not grant tracking permission after a probe; requires external revalidation."""
    def __init__(self, seed, status, scheduled, permit):
        self.state=request(status,scheduled,permit);self.plan=waveform(seed);self.commands=[];self.readings={k:[] for k in CHANNELS};self.pending=False
    def command(self, permit):
        if self.state!='probe':return 0.
        if self.pending or len(self.commands)>=COUNT or not permitted(permit,(COUNT-len(self.commands))*DT):
            self.state='external_observation';return 0.
        u=self.plan[len(self.commands)];self.commands.append(u);self.pending=True;return u
    def observe(self, sample):
        if not self.pending or self.state!='probe':return
        for k in CHANNELS:self.readings[k].append(sample.get(k,float('nan')))
        self.pending=False
        if len(self.commands)==COUNT:self.state='external_revalidation'
    def result(self):
        if self.state!='external_revalidation':return 'inconclusive',{}
        return diagnose(self.commands,self.readings)
