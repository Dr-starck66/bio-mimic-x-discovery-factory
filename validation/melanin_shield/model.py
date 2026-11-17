#!/usr/bin/env python3
"""ASTRA MELANIN SHIELD Ω v0.1: photon narrow-beam primary attenuation.
No laboratory validation; NOT a galactic cosmic ray dose model.
All underlying NIST coefficients are published at the URLs listed in README.md.
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path

# NIST X-ray mass attenuation coefficients (cm^2/g) - 0.1 and 1 MeV.
# https://physics.nist.gov/PhysRefData/XrayMassCoef/ElemTab/zXX.html
NIST = {
  0.1: {'H': 0.2944, 'C': 0.1514, 'N': 0.1529, 'O': 0.1551, 'Si': 0.1835},
  1.0: {'H': 0.1263, 'C': 0.06361, 'N': 0.06364, 'O': 0.06372, 'Si': 0.06361},
}
ATOMIC_WEIGHTS = {'H': 1.008, 'C': 12.011, 'N': 14.007, 'O': 15.999, 'Si': 28.085}
# Data values / assumptions explicit: real product recipes, measured densities not given.
FORMULAE = {
 'PE': {'C':1, 'H':2},
 'Water': {'H':2, 'O':1},
 'PLA': {'C':3, 'H':4, 'O':2},
 'Melanin_proxy': {'C':18, 'H':10, 'N':2, 'O':4},
 'Silica_proxy': {'Si':1, 'O':2},
}
MATERIALS = {
 'PE': {'rho':0.94, 'composition':{'PE':1}, 'comment':'PE homopolymer; assumed density'},
 'Water': {'rho':1.00, 'composition':{'Water':1}, 'comment':'water at approx room temperature'},
 'PLA': {'rho':1.24, 'composition':{'PLA':1}, 'comment':'PLA density assumed'},
 'PLA_10pct_melanin': {'rho':1.26, 'composition':{'PLA':0.90,'Melanin_proxy':0.10}, 'comment':'HYPOTHETICAL formulation, mass fractions; not an experimental recipe or proven shield'},
 'Silica_packed_proxy': {'rho':1.60,'composition':{'Silica_proxy':1}, 'comment':'packed SiO2 proxy NOT actual Mars regolith; bulk density assumed'},
}

def elemental_mass_fractions(formula):
    total = sum(ATOMIC_WEIGHTS[e]*n for e,n in formula.items())
    return {e: ATOMIC_WEIGHTS[e]*n/total for e,n in formula.items()}

def mu_over_rho(material, energy_mev):
    weights = MATERIALS[material]['composition']
    return sum(frac*sum(w*NIST[energy_mev][e] for e,w in elemental_mass_fractions(FORMULAE[f]).items()) for f,frac in weights.items())

def atten(material, energy_mev, thickness_cm=None, area_mass_kg_m2=None):
    assert (thickness_cm is None) != (area_mass_kg_m2 is None), 'specify one sizing constraint'
    rho = MATERIALS[material]['rho']
    if thickness_cm is None:
        thickness_cm = area_mass_kg_m2 / (10.0*rho)
    assert thickness_cm >= 0
    mass_kg_m2 = 10 * rho * thickness_cm
    # 1 g/cm² = 10 kg/m²
    trans = math.exp(-mu_over_rho(material,energy_mev) * (mass_kg_m2/10))
    return {'material':material,'energy_MeV':energy_mev,'thickness_cm':thickness_cm,
      'mass_kg_m2':mass_kg_m2,'transmission_primary_frac':trans,
      'attenuation_primary_pct':100*(1-trans),'mu_over_rho_cm2_g':mu_over_rho(material, energy_mev)}

def emit(folder:Path):
    folder.mkdir(parents=True, exist_ok=True)
    scenarios=[]
    for energy in NIST:
      for t in (1,5,10):
        for m in MATERIALS:
          scenarios.append({'constraint':f'thickness_{t}cm',**atten(m,energy,thickness_cm=t)})
      for mass in (10,100):
        for m in MATERIALS:
          scenarios.append({'constraint':f'mass_{mass}kg_m2',**atten(m,energy,area_mass_kg_m2=mass)})
    with open(folder/'results.csv','w',newline='',encoding='utf-8') as f:
      w=csv.DictWriter(f, fieldnames=list(scenarios[0])); w.writeheader(); w.writerows(scenarios)
    with open(folder/'materials.json','w',encoding='utf-8') as f:
      json.dump({'NIST':NIST,'formulas':FORMULAE,'materials':MATERIALS,'assumptions':'Photon primary uncollided attenuation, not absorbed dose, not GCR/SEP/neutrons'},f,indent=2)
    return scenarios

if __name__=='__main__':
    p=Path(__file__).resolve().parent
    rows=emit(p)
    for r in rows:
      if r['energy_MeV']==1.0 and r['constraint']=='thickness_5cm':
        print(f"{r['material']:<20} {r['mass_kg_m2']:6.1f} kg/m², primary γ attenuation: {r['attenuation_primary_pct']:5.1f}%")
    print('Created',p/'results.csv',p/'materials.json')
