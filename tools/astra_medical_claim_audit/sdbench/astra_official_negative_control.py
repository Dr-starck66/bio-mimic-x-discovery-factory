import json,hashlib
from pathlib import Path
from types import SimpleNamespace
from sdbench.harness.harness import run_case
from sdbench.config import get_sdbench_config
from sdbench.case_data import get_case_set
def wrap(s):
 return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(role='assistant',content=s))])
def gatekeeper(*,messages,**kwargs):
 return wrap('<test_result id="1"><result>Control response: no diagnostic evidence.</result><is_synthetic>true</is_synthetic></test_result>')
def judge(*,messages,**kwargs):
 return wrap('**REASONING**: Negative control must not receive a correct diagnosis. **SCORE**: 1')
def experiment(case):
 counter=[0]
 def intentionally_wrong(*,messages,**kwargs):
  counter[0]+=1
  return wrap('<test>Completely fictional assay control</test>' if counter[0]==1 else '<diagnosis>INVALID_CONTROL_LABEL_NOT_A_DISEASE</diagnosis>')
 cfg=get_sdbench_config('synthetic')
 cfg.max_turns=2;cfg.compute_costs=False;cfg.compute_actual_workup_costs=False
 out=run_case(cfg,case,'baseline',model=intentionally_wrong,gatekeeper_llm=gatekeeper,judge_llm=judge)
 return {'case_id':case['case_id'],'correct':out.get('correct'),'score':out.get('diagnosis_score'),'model_diagnosis':out.get('model_diagnosis'),'test_rounds':out.get('num_test_rounds'),'requested':out.get('requested_tests_only'),'test_logs':out.get('test_logs')}
cases=get_case_set('synthetic','train')
rows=[experiment(c) for c in cases]
assert len(rows)==5 and all(x['correct'] is False for x in rows)
assert all(x['score']==1 and x['test_rounds']==1 for x in rows)
report={'protocol':'OFFICIAL_MICROSOFT_SDBENCH_RUN_CASE','dataset':'official_synthetic_train_five_cases','experiment':'INTENTIONALLY_INVALID_NEGATIVE_CONTROL','num_cases':len(rows),'false_as_expected':sum(not x['correct'] for x in rows),'cost_calls':0,'individual':rows}
p=Path('/vercel/sdbench/astra_official_negative_control.json');p.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'negative_control':'PASS','cases':len(rows),'all_incorrect_as_expected':True,'test_rounds_each':[x['test_rounds'] for x in rows]}))

