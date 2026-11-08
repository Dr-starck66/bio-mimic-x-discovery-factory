#!/usr/bin/env python3
"""ASTRA BIORESEARCH: auditable occupational mesh, non-clinical, stdlib only.

Agents are executable scientific workflow roles, not people, autonomous labs,
or validation of publications. Reuses BIO-MIMIC X hypothesis/debate/planning engines.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = 'astra-bioresearch-mesh/1.0.0'
ROLES = (
    ('director', 'Direction scientifique', ()),
    ('librarian', 'Documentation et bibliographie', ('director',)),
    ('cohorts', 'Integrite des cohortes', ('librarian',)),
    ('genomics', 'Genomique', ('director',)),
    ('transcriptomics', 'Transcriptomique', ('genomics',)),
    ('proteomics', 'Proteomique', ('genomics',)),
    ('immunology', 'Immunologie des macrophages', ('librarian',)),
    ('extracellular_matrix', 'Matrice extracellulaire', ('librarian',)),
    ('comparative_biology', 'Biologie comparee Acomys/Mus', ('immunology','extracellular_matrix')),
    ('bioinformatics', 'Bioinformatique et pipeline', ('genomics','transcriptomics')),
    ('biostatistics', 'Biostatistique et reproductibilite', ('cohorts','bioinformatics')),
    ('epidemiology', 'Epidemiologie et biais', ('biostatistics',)),
    ('hypotheses', 'Generation d hypotheses falsifiables', ('librarian','comparative_biology')),
    ('red_team', 'Revue adversariale Morpheus', ('hypotheses','biostatistics')),
    ('experiments', 'Plans experimentaux conceptuels', ('red_team',)),
    ('animal_welfare', 'Bien etre animal et comite ethique', ('experiments',)),
    ('clinical_safety', 'Securite et recherche clinique', ('experiments',)),
    ('privacy', 'Protection des donnees', ('director',)),
    ('legal_ip', 'Reglementation et propriete intellectuelle', ('privacy',)),
    ('quality', 'Assurance qualite scientifique', ('red_team','privacy')),
    ('finance', 'Gestion budgetaire', ('legal_ip',)),
    ('partnership', 'Relations scientifiques Inserm', ('quality','finance','animal_welfare','clinical_safety')),
    ('final_review', 'Comite de decision', ('partnership',)),
)
REQUIREMENTS = {
    'librarian': ('source_records', 'Fournir des sources primaires verifiables'),
    'cohorts': ('independent_cohort_ids', 'Identifier les cohortes independantes'),
    'genomics': ('genome_assembly_accessions', 'Specifier les assemblages et acces GenBank'),
    'transcriptomics': ('rna_dataset_accessions', 'Fournir jeux ARN autorises et appariees'),
    'proteomics': ('proteomics_dataset_accessions', 'Verifier des proteomes independants'),
    'immunology': ('macrophage_evidence', 'Associer macrophages a des observations sourcees'),
    'extracellular_matrix': ('ecm_evidence', 'Associer matrice a des observations sourcees'),
    'comparative_biology': ('negative_control_species', 'Inclure un controle Mus et critere de comparaison'),
    'bioinformatics': ('analysis_artifacts', 'Tracer fichiers, scripts et empreintes SHA256'),
    'biostatistics': ('biological_replicates', 'Ajouter replicats et plan statistique'),
    'epidemiology': ('confounders', 'Identifier facteurs de confusion'),
    'animal_welfare': ('ethical_approval_ref', 'Aucune experimentation animale sans autorisation'),
    'clinical_safety': ('human_study_approval_ref', 'Aucune intervention humaine autorisee'),
    'legal_ip': ('prior_art_review', 'Verifier antecedents et droits'),
}

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',',':')).encode()).hexdigest()

def status_record(role, status, findings, inputs=None, dependency_warnings=None, artifacts=None):
    out = {'role':role,'status':status,'findings':findings,
           'inputs':inputs or [],'dependency_warnings':dependency_warnings or [],
           'artifacts':artifacts or []}
    out['sha256'] = digest(out)
    return out

def engine_or_none(module, function):
    try:
        import importlib
        return getattr(importlib.import_module(module), function)
    except (ImportError, AttributeError):
        return None

def evaluate_role(role, mission, shared, warnings):
    evidence = mission.get('evidence',{})
    if role == 'director':
        ok=bool(mission.get('id') and mission.get('question') and mission.get('contact'))
        return status_record(role,'PASS' if ok else 'FAIL',
            ['Cadrage lu; aucun accord institutionnel presume' if ok else 'Mission sans identifiant, question ou interlocuteur'],
            ['id','question','contact'],warnings)
    if role == 'privacy':
        includes=mission.get('contains_personal_health_data', None)
        if includes is True:
            return status_record(role,'FAIL',['Donnees de sante personnelles: traitement bloque'],['contains_personal_health_data'],warnings)
        if includes is None:
            return status_record(role,'UNVERIFIED',['Classification des donnees absente'],[],warnings)
        return status_record(role,'PASS',['Mission declaree sans donnees patient; declaration non auditee'],['contains_personal_health_data'],warnings)
    if role == 'finance':
        expense=mission.get('authorized_additional_cost_eur',None)
        if expense is None or not isinstance(expense,(int,float)) or expense != 0:
            return status_record(role,'FAIL',['Budget non conforme: depense nouvelle interdite'],['authorized_additional_cost_eur'],warnings)
        return status_record(role,'PASS',['Budget additionnel 0 EUR applique dans ce cycle'],['authorized_additional_cost_eur'],warnings)
    if role == 'hypotheses':
        fn = engine_or_none('hypothesis_engine', 'generate_hypotheses')
        if fn is None:
            return status_record(role,'UNVERIFIED',['Moteur BIO-MIMIC X hypothesis_engine introuvable'],[],warnings)
        claim = {'subject': mission.get('question',''),
                 'sources':[s.get('ref') for s in evidence.get('source_records',[]) if isinstance(s,dict) and isinstance(s.get('ref'),str)],
                 'mechanisms':mission.get('candidate_mechanisms',[]),
                 'genes':mission.get('candidate_genes',[])}
        hypotheses=fn({'id':mission['id']},claim,{'counterfactual_tests':mission.get('counterfactual_tests',[])},[],3)
        shared['hypotheses']=hypotheses
        return status_record(role,'PARTIAL' if hypotheses else 'UNVERIFIED',
            [f'{len(hypotheses)} hypotheses proposees; non verifiees scientifiquement'],
            ['candidate_mechanisms','candidate_genes'],warnings,[{'type':'hypotheses','count':len(hypotheses),'sha256':digest(hypotheses)}])
    if role == 'red_team':
        fn=engine_or_none('debate_engine','debate_hypotheses')
        hs=shared.get('hypotheses',[])
        if fn is None or not hs:
            return status_record(role,'UNVERIFIED',['Critique non executable: moteur ou hypotheses absents'],[],warnings)
        audit={'flags':['independent biological validation missing','association not causation']}
        debate=fn(hs,{},audit,{'counterfactual_tests':mission.get('counterfactual_tests',[])})
        shared['debate']=debate
        return status_record(role,'PARTIAL',['Contradictions et objections generees; pas de validation biologique'],
            ['hypotheses'],warnings,[{'type':'adversarial_review','sha256':digest(debate)}])
    if role == 'experiments':
        fn=engine_or_none('experiment_planner','plan_experiments')
        hs=shared.get('hypotheses',[]); db=shared.get('debate',{})
        if fn is None or not hs or not db:
            return status_record(role,'UNVERIFIED',['Planification impossible: moteurs scientifiques requis absents'],[],warnings)
        plans=fn({'id':mission['id']},{'subject':mission.get('question','')},hs,db,
                 {'counterfactual_tests':mission.get('counterfactual_tests',[])},2)
        shared['plans']=plans
        return status_record(role,'PARTIAL',[f'{len(plans)} plans proposes, aucun essai physique execute'],
            ['debate'],warnings,[{'type':'conceptual_plans','count':len(plans),'sha256':digest(plans)}])
    if role == 'partnership':
        blocked=[r for r in ('clinical_safety','animal_welfare','privacy','quality')
                 if shared['records'][r]['status'] in ('FAIL','UNVERIFIED')]
        if blocked:
            return status_record(role,'UNVERIFIED',[f'Dossier collaboration en attente des controles: {", ".join(blocked)}',
                'Aucun email envoye; aucun accord institutionnel presume'],[],warnings)
        return status_record(role,'PARTIAL',['Note interne preparable pour Florence Apparailly; pas d envoi ni accord'],[],warnings)
    if role == 'quality':
        blocked=[r for r in ('librarian','cohorts','biostatistics','red_team')
                 if shared['records'][r]['status']!='PASS']
        return status_record(role,'UNVERIFIED' if blocked else 'PARTIAL',
            [f'Validite biologique non etablie. Controles a completer: {blocked}'],[],warnings)
    if role == 'final_review':
        counts={s:sum(r['status']==s for r in shared['records'].values()) for s in ('PASS','PARTIAL','FAIL','UNVERIFIED')}
        return status_record(role,'PARTIAL',['Cycle de revue multiagents termine; aucune validation biologique ou clinique',
            f'Synthese des agents precedents: {counts}'],[],warnings)
    field, action=REQUIREMENTS[role]
    value=evidence.get(field)
    if value in (None,[],{},''):
        return status_record(role,'UNVERIFIED',[action], [field],warnings)
    # Presence is not independent scientific proof. Keep scientific status unverified.
    return status_record(role,'PARTIAL',[f'Donnees fournies pour {field}; authenticite et resultats non verifies'],[field],warnings)

def run(mission):
    if not isinstance(mission,dict) or not isinstance(mission.get('evidence',{}),dict):
        raise ValueError('Mission et evidence doivent etre des objets JSON')
    for name in ('id','question','contact'):
        if not isinstance(mission.get(name),str) or not mission[name].strip():
            raise ValueError(f'Champ requis manquant: {name}')
    shared={'records':{}}; log=[]
    for role, name, deps in ROLES:
        warnings=[d for d in deps if shared['records'][d]['status'] not in ('PASS',)]
        result=evaluate_role(role, mission, shared, warnings)
        result['name']=name
        shared['records'][role]=result
        log.append({'index':len(log)+1,'role':role,'depends_on':list(deps),
                    'input_hashes':[shared['records'][d]['sha256'] for d in deps],
                    'output_hash':result['sha256']})
    out={'schema':SCHEMA,'mission_id':mission['id'], 'mission_sha256':digest(mission),
         'contact':mission['contact'],'external_communication':'DISABLED',
         'clinical_claim':'UNVERIFIED','real_wetlab_experiments':0,
         'new_cost_eur':0,'new_scheduled_jobs':0,
         'agents':shared['records'],'handoffs':log,
         'scientific_artifacts':{'hypotheses':shared.get('hypotheses',[]),
                                 'debate':shared.get('debate',{}),'plans':shared.get('plans',[])},
         'summary':{'roles_executed':len(log),
                    'technical_pipeline':'PASS',
                    'biological_validation':'UNVERIFIED',
                    'institutional_partnership':'UNVERIFIED'}}
    out['sha256']=digest(out)
    return out

def main():
    ap=argparse.ArgumentParser(description='ASTRA BIORESEARCH offline research role mesh')
    ap.add_argument('--mission',required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    mission=json.loads(Path(args.mission).read_text(encoding='utf-8'))
    result=run(mission)
    dest=Path(args.out); dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=dest.with_suffix(dest.suffix+'.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(dest)
    print(json.dumps(result['summary'],ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
