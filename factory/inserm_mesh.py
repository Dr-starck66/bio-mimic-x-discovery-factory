#!/usr/bin/env python3
"""ASTRA BIORESEARCH: auditable occupational mesh, non-clinical, stdlib only.

Agents are executable scientific workflow roles, not people, autonomous labs,
or validation of publications. Reuses BIO-MIMIC X hypothesis/debate/planning engines.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

SCHEMA = 'astra-bioresearch-mesh/1.1.0'
ENGINE_BLOBS = {'hypothesis_engine':'f1c214f92a1fe335d6c1be3548f54136b54ada48',
                'debate_engine':'fce5aaa47f8bfa88e981eafb6b26b656939ac1ea',
                'experiment_planner':'e98452f4470a05af3b12f469e8b9c1654bde8351'}

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

def verified_engine_fingerprints():
    """Integrity gate uses official Git blob SHA-1 for original scientific engine bytes."""
    output={}
    for module,expected in ENGINE_BLOBS.items():
        path=Path(__file__).with_name(module+'.py')
        if not path.is_file():
            output[module]={'status':'MISSING','expected_git_blob_sha1':expected}
            continue
        raw=path.read_bytes()
        actual=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        output[module]={'status':'PASS' if actual==expected else 'MISMATCH',
                        'expected_git_blob_sha1':expected, 'actual_git_blob_sha1':actual,
                        'sha256':hashlib.sha256(raw).hexdigest()}
    return output

def select_existing_program(mission, programs_path):
    """Read authentic BIO-MIMIC X state/factory/programs.json; never infer papers as verified."""
    collection=json.loads(Path(programs_path).read_text(encoding='utf-8'))
    if not isinstance(collection,dict) or not isinstance(collection.get('programs'),list):
        raise ValueError('Invalid BIO-MIMIC X programs.json structure')
    key=mission.get('existing_program_id')
    matched=[x for x in collection['programs'] if x.get('id')==key]
    if len(matched)!=1:raise ValueError('Existing scientific program missing or ambiguous')
    program=matched[0]
    if program.get('title')!='Acomys cahirinus':
        raise ValueError('Misidentified existing scientific program')
    if not program.get('sources') or not isinstance(program.get('mechanisms'),list):
        raise ValueError('Existing scientific program has no source metadata')
    return program

def bibliography_audit(mission, program):
    evidence=mission.get('evidence',{})
    records=evidence.get('source_records',[])
    supporting=[];negative=[];unverified=[];reviews=[];excluded=[]
    for rec in records:
        if not isinstance(rec,dict) or not isinstance(rec.get('ref'),str):
            raise ValueError('Invalid bibliography record')
        key=rec['ref']
        if rec.get('status')=='WEB_VERIFIED' and rec.get('study_role')=='SUPPORTING_PRIMARY' and key.startswith('PMID:'):
            supporting.append(key)
        elif rec.get('study_role')=='NEGATIVE_CONTEXT':negative.append(key)
        elif rec.get('study_role')=='REVIEW':reviews.append(key)
        else:unverified.append(key)
    legacy=set(program.get('sources',[]) if program else [])
    known=set(r['ref'] for r in records)
    excluded=sorted(legacy-known)
    return {'supporting_primary_pmids':sorted(set(supporting)),
            'negative_context_pmids':sorted(set(negative)),
            'review_pmids':sorted(set(reviews)),
            'unverified_pmids':sorted(set(unverified)),
            'unreviewed_legacy_pmids':excluded,
            'existing_program_source_count':len(legacy),
            'independent_replications_of_same_mechanism':'UNVERIFIED',
            'web_checked_metadata_only':True,
            'no_fabricated_biological_data':True}

def local_model_proposal(role, mission, previous_context, model):
    """Optional Ollama-on-localhost reasoning, never an evidence source or validator."""
    if not isinstance(model,str) or not model.strip() or len(model)>120:
        return {'status':'UNVERIFIED','reason':'Modele local absent ou invalide'}
    prompt=(f"Tu joues le role scientifique {role} dans BIO-MIMIC X. "
            "Propose des controles, contre-arguments ou pistes de travail, pas de faits nouveaux ni de donnees inventees. "
            "Aucune recommandation clinique, aucune publication ni verification de sources sans preuve. "
            f"Question: {mission['question']}. Resultats des taches precedentes: {json.dumps(previous_context,ensure_ascii=False)[:3600]}. "
            "Reponds en francais en 100 mots au maximum.")
    body=json.dumps({'model':model,'prompt':prompt,'stream':False,
                     'options':{'num_predict':180}}).encode('utf-8')
    req=urllib.request.Request('http://127.0.0.1:11434/api/generate',
                               data=body,headers={'Content-Type':'application/json'},method='POST')
    try:
        # Direct local socket; no HTTP proxy, paid API or remote endpoint.
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req,timeout=8) as response:
            payload=response.read(16384)
        answer=json.loads(payload).get('response','')
        if not isinstance(answer,str) or not answer.strip():
            raise ValueError('Empty model response')
        return {'status':'PARTIAL','model':model,'suggestions_unverified':answer[:1600]}
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return {'status':'UNVERIFIED','reason':type(exc).__name__}

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
    if role == 'librarian':
        a=shared['bibliography_audit']
        found=len(a['supporting_primary_pmids'])
        concerns=a['negative_context_pmids']+a['unverified_pmids']+a['review_pmids']+a['unreviewed_legacy_pmids']
        return status_record(role,'PARTIAL' if found else 'UNVERIFIED',
            [f'{found} publications primaires verifiees sur PubMed pour des axes distincts',
             f'Sources adverses/revues/non verifiees: {concerns}',
             'Aucune replication biologique independante du meme mecanisme certifiee'],
            ['source_records','existing_program_id'],warnings,
            [{'type':'bibliography_audit','sha256':digest(a)}])
    if role == 'cohorts':
        ids=evidence.get('independent_cohort_ids',[])
        if not ids or len(ids)!=len(set(ids)):
            return status_record(role,'UNVERIFIED',
                ['Cohortes independantes absentes ou dupliquees: aucune replication confirmee'],
                ['independent_cohort_ids'],warnings)
        return status_record(role,'PARTIAL', ['Identifiants declares; independance non auditee'],
                             ['independent_cohort_ids'],warnings)
    if role == 'hypotheses':
        fn = engine_or_none('hypothesis_engine', 'generate_hypotheses')
        if fn is None:
            return status_record(role,'UNVERIFIED',['Moteur BIO-MIMIC X hypothesis_engine introuvable'],[],warnings)
        claim = {'subject': mission.get('question',''),
                 'sources':shared['bibliography_audit']['supporting_primary_pmids'],
                 'mechanisms':list(dict.fromkeys(mission.get('candidate_mechanisms',[])+(shared.get('existing_program',{}).get('mechanisms',[])))),
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
        a=shared['bibliography_audit']
        flags=['independent biological validation missing','association not causation','correlation not causation']
        if a['negative_context_pmids']:flags.append('negative context evidence must be kept')
        if a['review_pmids']:flags.append('review articles are not independent replication')
        if a['unverified_pmids'] or a['unreviewed_legacy_pmids']:flags.append('unverified legacy citations excluded')
        audit={'flags':flags}
        debate=fn(hs,{},audit,{'counterfactual_tests':mission.get('counterfactual_tests',[])})
        # The upstream scoring engine counts distinct PMID IDs, NOT independent
        # biological replications. Never let its old display string overclaim.
        for item in debate.get('ranked',[]):
            item['evidence_support']=[t.replace('independent PMID-linked sources',
                'distinct PMID IDs; independent biological replication UNVERIFIED')
                for t in item.get('evidence_support',[])]
            item['reviewed_source_scope']='Macrophage and ECM studies have different endpoints; not a replicated mechanism'
            item['evidence_score_is_not_truth']=True
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

def run(mission, local_model=None, existing_program=None):
    if not isinstance(mission,dict) or not isinstance(mission.get('evidence',{}),dict):
        raise ValueError('Mission et evidence doivent etre des objets JSON')
    for name in ('id','question','contact'):
        if not isinstance(mission.get(name),str) or not mission[name].strip():
            raise ValueError(f'Champ requis manquant: {name}')
    if existing_program is not None and (existing_program.get('id')!=mission.get('existing_program_id')
                                         or existing_program.get('title')!='Acomys cahirinus'):
        raise ValueError('Wrong scientific-program mapping')
    biblio=bibliography_audit(mission,existing_program)
    shared={'records':{},'bibliography_audit':biblio,'existing_program':existing_program or {}}
    log=[];model_observations={}
    engines=verified_engine_fingerprints()
    for role, name, deps in ROLES:
        warnings=[d for d in deps if shared['records'][d]['status'] not in ('PASS',)]
        result=evaluate_role(role, mission, shared, warnings)
        result['name']=name
        shared['records'][role]=result
        if local_model:
            if mission.get('contains_personal_health_data') is False and mission.get('authorized_additional_cost_eur') == 0:
                model_observations[role]=local_model_proposal(role,mission,[{'role':d,'status':shared['records'][d]['status'],'findings':shared['records'][d]['findings'],'sha256':shared['records'][d]['sha256']} for d in deps],local_model)
            else:
                model_observations[role]={'status':'UNVERIFIED','reason':'Privacy or zero cost gate denied model execution'}
        log.append({'index':len(log)+1,'role':role,'depends_on':list(deps),
                    'input_hashes':[shared['records'][d]['sha256'] for d in deps],
                    'output_hash':result['sha256']})
    out={'schema':SCHEMA,'mission_id':mission['id'], 'mission_sha256':digest(mission),
         'contact':mission['contact'],'external_communication':'DISABLED',
         'clinical_claim':'UNVERIFIED','real_wetlab_experiments':0,
         'new_cost_eur':0,'new_scheduled_jobs':0,
         'agents':shared['records'],'handoffs':log,
         'engine_fingerprints':engines,
         'bibliography_audit':biblio,
         'existing_program':{'id':existing_program.get('id'),
                             'title':existing_program.get('title'),
                             'original_source_pmids':existing_program.get('sources',[]),
                             'original_source_count_claimed':existing_program.get('independent_source_count'),
                             'source_count_revalidated':'UNVERIFIED',
                             'mechanisms':existing_program.get('mechanisms',[])} if existing_program else None,
         'local_model':{'requested':bool(local_model),'observations':model_observations,
                        'notes_are_evidence':False},
         'scientific_artifacts':{'hypotheses':shared.get('hypotheses',[]),
                                 'debate':shared.get('debate',{}),'plans':shared.get('plans',[])},
         'summary':{'roles_executed':len(log),
                    'technical_pipeline':'PASS' if (all(x['status']=='PASS' for x in engines.values())
                        and len(shared.get('hypotheses',[]))>0 and len(shared.get('debate',{}).get('ranked',[]))>0
                        and len(shared.get('plans',[]))>0) else 'PARTIAL',
                    'biological_validation':'UNVERIFIED',
                    'institutional_partnership':'UNVERIFIED'}}
    out['sha256']=digest(out)
    return out

def main():
    ap=argparse.ArgumentParser(description='ASTRA BIORESEARCH offline research role mesh')
    ap.add_argument('--mission',required=True)
    ap.add_argument('--programs',default=None,help='Real BIO-MIMIC X state/factory/programs.json')
    ap.add_argument('--out',required=True)
    ap.add_argument('--local-model',default=None,help='Optional preinstalled local Ollama model; no remote inference')
    args=ap.parse_args()
    mission=json.loads(Path(args.mission).read_text(encoding='utf-8'))
    p=select_existing_program(mission,args.programs) if args.programs else None
    result=run(mission,local_model=args.local_model,existing_program=p)
    dest=Path(args.out); dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=dest.with_suffix(dest.suffix+'.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(dest)
    print(json.dumps(result['summary'],ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
