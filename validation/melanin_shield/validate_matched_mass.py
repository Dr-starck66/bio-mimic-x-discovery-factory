#!/usr/bin/env python3
"""ASTRA MELANIN SHIELD Ω: independently check model.py at fixed areal mass.

Only NIST photon narrow-beam attenuation is calculated. Measured beta and gamma
studies are separate evidence streams; no GCR/SEP dose or material validation.
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import model

DOIS = {
  'beta_experimental':'10.1371/journal.pone.0229921',
  'beta_data':'10.5281/zenodo.3667494',
  'gamma_experimental':'10.3390/polym17050609',
  'iss_exposure':'10.1073/pnas.2427118122'
}

def compare():
    rows=[]
    for energy in sorted(model.NIST):
        for mass in (10.0,100.0):
            base=model.atten('PE',energy,area_mass_kg_m2=mass)
            pure=model.atten('PLA',energy,area_mass_kg_m2=mass)
            candidate=model.atten('PLA_10pct_melanin',energy,area_mass_kg_m2=mass)
            assert math.isclose(base['mass_kg_m2'],candidate['mass_kg_m2'],abs_tol=1e-10)
            assert math.isclose(pure['mass_kg_m2'],candidate['mass_kg_m2'],abs_tol=1e-10)
            for other_name,other in [('PLA',pure),('PLA_10pct_melanin',candidate)]:
                rows.append({
                    'energy_mev':energy,'areal_mass_kg_m2':mass,'candidate':other_name,
                    'candidate_mu_over_rho_cm2_g':other['mu_over_rho_cm2_g'],
                    'pe_mu_over_rho_cm2_g':base['mu_over_rho_cm2_g'],
                    'candidate_primary_transmission':other['transmission_primary_frac'],
                    'pe_primary_transmission':base['transmission_primary_frac'],
                    'candidate_minus_pe_attenuation_pct_points':other['attenuation_primary_pct']-base['attenuation_primary_pct'],
                    'candidate_beats_pe_at_matched_mass':other['transmission_primary_frac'] < base['transmission_primary_frac'],
                    'evidence':'MODEL_ONLY_NOT_EXPERIMENTAL'
                })
    return rows

def record():
    rows=compare()
    return {
        'status':'NUMERICAL_MODEL_CHECK_ONLY',
        'scope':'unscattered monoenergetic photons (narrow beam), 0.1 and 1 MeV, equal g/cm²',
        'measurements_used':False,
        'dosimetry_or_space_shield_proven':False,
        'input':'existing ASTRA MELANIN SHIELD Ω v0.1 model.py with published NIST elemental coefficients; hypothetical proxy chemistry',
        'comparisons':rows,
        'independent_negative_controls':{
            'beta':'Vasileiou & Summerer (2020): experiments did not find improved beta shielding of melanin versus cellulose; qualitative external evidence, NOT fitted to this photon model',
            'density':'At fixed areal mass, density changes thickness but cannot change gamma-primary attenuation for a fixed material composition',
            'gamma':'Marashdeh & Madkhali (2025): measured plant eumelanin gamma energies and metal dopants; NOT directly transferable to fungal-melanin/PLA formulation',
        },
        'future_discrimination':'Only independent measured transmission with stated energy, sample composition, areal mass, uncertainty and consistent controls can assess actual improvement',
        'primary_sources':DOIS,
        'limitations':['No beta electron transport','No neutron, proton or heavy-ion transport','No GCR/SEP dose equivalent','No measured composite densities/composition','No secondary radiation or buildup']
    }

if __name__=='__main__':
    path=Path(__file__).with_name('matched_mass_validation.json')
    path.write_text(json.dumps(record(),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    for row in compare():
        print(f"{row['energy_mev']:.1f} MeV; {row['areal_mass_kg_m2']:g} kg/m²; {row['candidate']}: Δ attenuation vs PE {row['candidate_minus_pe_attenuation_pct_points']:+.4f} pp; beats PE={row['candidate_beats_pe_at_matched_mass']}")
    print('Receipt:',path)
