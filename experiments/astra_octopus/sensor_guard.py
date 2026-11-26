"""Local sensor quorum and independent velocity consistency check."""
import math
from statistics import median
from itertools import combinations

def quorum(values, tolerance):
    good = [v for v in values if math.isfinite(v)]
    if len(good)<2: return None
    if max(good)-min(good)<=tolerance: return median(good)
    pairs=[(a+b)/2 for a,b in combinations(good,2) if abs(a-b)<=tolerance]
    return pairs[0] if len(pairs)==1 else None

def clamp(x, limit=12.):
    return max(-limit,min(limit,x)) if math.isfinite(x) else 0.

class Guard:
    def __init__(self, initial_position, dt=.01):
        self.prediction=initial_position
        self.dt=dt
        self.age=0.
        self.streak=5
        self.initial=True
        self.history_valid=True
    def step(self, positions, velocities, goal):
        p=quorum(positions,.055)
        v=quorum(velocities,.08)
        if v is None: self.history_valid=False
        elif not self.initial and self.history_valid: self.prediction+=self.dt*v
        self.initial=False
        self.age+=self.dt
        trusted=(self.history_valid and p is not None and v is not None and math.isfinite(goal) and abs(p-self.prediction)<=.045+.018*self.age)
        self.streak=min(5,self.streak+1) if trusted else 0
        if self.streak<5:
            return (clamp(-4*v) if v is not None else 0.), 'fallback'
        degraded=any(not math.isfinite(z) or abs(z-p)>.055 for z in positions) or any(not math.isfinite(z) or abs(z-v)>.08 for z in velocities)
        return clamp(10*(goal-p)-4*v), 'degraded' if degraded else 'normal'

class AnchoredGuard(Guard):
    """Independent absolute position sample every 10 ticks; fail closed if stale."""
    def __init__(self, initial_position, dt=.01):
        super().__init__(initial_position,dt)
        self.anchor_age=0.
        self.anchor_ok=False
        self.anchor_streak=0
    def step(self, positions, velocities, goal, anchor=None):
        u,status=super().step(positions,velocities,goal)
        p=quorum(positions,.055)
        self.anchor_age+=self.dt
        if anchor is not None:
            self.anchor_age=0.
            self.anchor_ok=(math.isfinite(anchor) and p is not None and abs(p-anchor)<=.08)
        valid=self.anchor_ok and self.anchor_age<=.15 and status!='fallback'
        self.anchor_streak=min(5,self.anchor_streak+1) if valid else 0
        return (u,status) if self.anchor_streak>=5 else (0.,'fallback')
