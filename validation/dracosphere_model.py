#!/usr/bin/env python3
"""ASTRA BIO-MIMIC X: minimal, falsifiable dracosphere O2 transport model.

Models radial steady-state diffusion resistance through a spherical water shell,
plus N concentric membrane interface resistances. This is NOT a fitted biological
model: there are no in-vivo transport or respiration measurements for this organelle.

Sources of numerical inspiration:
- Li et al. Nat Commun 2026, doi:10.1038/s41467-026-78965-0 (12 um spheres,
  >20 lamellae, lamellar shell 77-1060 nm, mean 506 nm).
- oxygen permeability: doi:10.1007/978-3-030-48238-1_4 (simulations ~12-15 cm/s)
  and PMID 34694438 (experimental value near 0.2 cm/s at 45 mol% cholesterol).

Formulas:
  R_water = (1/r_inner - 1/r_outer)/(4*pi*D_water) [s/m^3]
  R_mem_i = 1/(4*pi*P_mem*r_i**2)               [s/m^3]
  J = (C_ext - C_int)/(R_water + sum(R_mem_i))   [mol/s]
  J(N)/J(0) = R_water/(R_water + sum(R_mem_i)).
  Under a separate illustrative first-order bacterial sink, Da is the ratio
  of first-order reaction to *bare* shell conductance and
  C_int/C_ext = 1/(1+Da*(R_total/R_water)).

NOTE: membrane resistance is added to the full-water-layer resistance rather
than subtracting membrane thickness from water path (conservative approximation).
"""
from __future__ import annotations
import argparse
import json
from math import pi, isfinite
from pathlib import Path

R_IN_M=5.5e-6
R_OUT_M=6.0e-6
D_WATER_M2_S=2.0e-9
BILAYER_M=4e-9  # geometry assumption, NOT measured for dracosphere
PERMEABILITIES_CM_S=(0.2, 12.0, 15.0, 100.0)
COUNTS=(0, 1, 5, 20, 30)

def calc(n:int, p_cm_s:float, r_inner:float=R_IN_M, r_outer:float=R_OUT_M,
         d:float=D_WATER_M2_S, da:float=1.0)->dict:
    if isinstance(n,bool) or not isinstance(n,int) or n<0:
        raise ValueError('n must be a nonnegative integer')
    if not all(isfinite(z) and z>0 for z in (p_cm_s,r_inner,r_outer,d)) or r_inner>=r_outer:
        raise ValueError('positive transport parameters and r_outer > r_inner required')
    if not isfinite(da) or da<0:
        raise ValueError('Da must be finite and nonnegative')
    rw=(1/r_inner-1/r_outer)/(4*pi*d)
    p_m_s=p_cm_s/100.0
    rm=sum(1.0/(4*pi*p_m_s*(r_inner+(i+0.5)*(r_outer-r_inner)/n)**2)
           for i in range(n))
    r=rw+rm
    return {'n':n,'p_cm_s':p_cm_s,'Da':da,
            'water_resistance_s_m-3':rw,'membrane_resistance_s_m-3':rm,
            'transport_relative_to_no_membranes':rw/r,
            'inside_O2_fraction_of_outside':1/(1+da*r/rw),
            'lamellae_fit_in_506nm_shell':n*BILAYER_M<=506e-9,
            'lamellae_thickness_fraction_of_mean_shell':n*BILAYER_M/506e-9}

def report()->dict:
    rows=[calc(n,p) for p in PERMEABILITIES_CM_S for n in COUNTS]
    sensitive=[]
    for h in (77e-9,506e-9,1060e-9):
        for p in (0.2,12.0,100.0):
            if 20*BILAYER_M>h:
                sensitive.append({'n':20,'shell_width_nm':round(h*1e9),
                                  'p_cm_s':p,'status':'GEOMETRY_INVALID',
                                  'reason':'20 assumed 4 nm lamellae cannot fit within this local thickness'})
            else:
                sensitive.append({'shell_width_nm':round(h*1e9),'status':'MODELLED',
                                  **calc(20,p,r_outer=R_IN_M+h)})
    return {'status':'PASS local physics calculation; biological mechanism UNVERIFIED',
            'not_a_biological_validation':True,
            'purpose':'test whether 20 membranes can attenuate radial O2 delivery under published membrane-permeability ranges',
            'calibration':'NOT CALIBRATED to C. shenloong. No fitted parameters.',
            'geometry':{'outer_diameter_um':12,'mean_shell_width_nm':500,
                        'published_shell_width_range_nm':[77,1060],
                        'published_mean_shell_width_nm':506,
                        'bilayer_assumed_width_nm':4,
                        'water_D_m2_s':D_WATER_M2_S},
            'scenario_notes':{'P_0.2':'Experimental erythrocyte-like lipid at 45 mol% cholesterol; composition NOT known in dracosphere',
                              'P_12_to_15':'POPC / POPC:cholesterol molecular dynamics estimates; extrapolation only',
                              'P_100':'high permeability negative-control scenario, not directly measured for dracosphere',
                              'Da_1':'arbitrary illustrative first-order sink, not a biological rate'},
            'models':rows,'shell_width_sensitivity':sensitive,
            'sources':[
              {'doi':'10.1038/s41467-026-78965-0','role':'observed geometry, hypothesized oxygen barrier'},
              {'doi':'10.1007/978-3-030-48238-1_4','role':'simulated POPC O2 permeability'},
              {'pmid':'34694438','role':'alternative experimentally measured membrane O2 permeability'},
              {'doi':'10.1038/s41467-024-48719-x','role':'oxygen requirements of regenerative tissues'}],
            'unmeasured':'native lamella chemistry/permeability, oxygen gradients, uptake, nutrient release, viability, regenerative effects'}

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',default='report.json')
    ns=ap.parse_args()
    result=report()
    Path(ns.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    for row in result['models']:
        if row['n'] in (0,20):
            print(f"N={row['n']:2d} P={row['p_cm_s']:5g} cm/s J/J0={row['transport_relative_to_no_membranes']:.6f}, Cinside/Cext(Da=1)={row['inside_O2_fraction_of_outside']:.6f}")
    print('Written:',ns.output)
