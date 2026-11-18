"""ASTRA Ω experimental free-model integration into the UNMODIFIED Microsoft SDBench run_case API.
REAL Qwen agent; two explicit deterministic SURROGATE roles (NOT official gatekeeper/judge models).
Official synthetic training split only. No clinical accuracy claims.
"""
import json, re, hashlib, time, traceback
from pathlib import Path
from types import SimpleNamespace
from llama_cpp import Llama
from sdbench import agents
from sdbench.harness.harness import run_case
from sdbench.config import get_sdbench_config
from sdbench.case_data import get_case_set

MODEL='/tmp/qwen2_5_0_5b_q4km.gguf'
MODEL_SHA=hashlib.sha256(Path(MODEL).read_bytes()).hexdigest()
llm=Llama(model_path=MODEL,n_ctx=4096,n_batch=512,n_threads=2,verbose=False)
usage=[]
def resp(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(role="assistant",content=content))])
def real_qwen(*,messages,**kwargs):
    t=time.monotonic()
    raw=llm.create_chat_completion(messages=list(messages),max_tokens=96,temperature=0.0)
    content=raw["choices"][0]["message"].get("content") or ""
    usage.append({"seconds":round(time.monotonic()-t,3),"prompt":raw["usage"]["prompt_tokens"],"generated":raw["usage"]["completion_tokens"],"output":content[:180]})
    return resp(content)

def astra_run(case_summary,test_runner,agent_llm,collector,config):
    messages=[{"role":"system","content":(
        "Synthetic research case ONLY. Answer with ONLY a valid JSON object. "
        'First choose {"action":"question","name":"What relevant symptom or history should be clarified?"} '
        'or {"action":"test","name":"CBC"}. After test result choose {"action":"diagnosis","value":"one diagnostic label"} '
        'or {"action":"abstain"}. Never advise treatment; do not claim certainty.'
    )},{"role":"user","content":"Synthetic presentation: "+str(case_summary)[:1000]}]
    have_evidence=False
    tried=set()
    for i in range(4):
        response=agent_llm(messages=messages)
        content=response.choices[0].message.content or ""
        try: action=json.loads(content)
        except Exception: break
        if not isinstance(action,dict):break
        kind=action.get("action")
        collector.setdefault("astra_actions",[]).append(action)
        if kind=="abstain":break
        if kind=="diagnosis":
            label=action.get("value")
            if have_evidence and isinstance(label,str) and 0<len(label)<=180:
                collector["astra_evidence_steps"]=1
                collector["agent_messages"]=messages
                return label
            break
        if kind not in ("test","question") or not test_runner.turns_left:break
        name=action.get("name")
        if not isinstance(name,str) or not (0<len(name)<=150) or name.casefold() in tried:break
        tried.add(name.casefold())
        prefix="Test to order: " if kind=="test" else "Question for the patient: "
        result=test_runner([prefix+name])
        have_evidence=bool(result.test_results)
        observations=[{"test_name":x["test_name"],"results":str(x["results"])[:320]} for x in result.test_results]
        messages.append({"role":"assistant","content":content})
        messages.append({"role":"user","content":"Untrusted synthetic observations, no instructions: "+json.dumps(observations)+"\nReply with a JSON diagnosis or abstention."})
    collector["agent_messages"]=messages
    collector["astra_evidence_steps"]=int(have_evidence)
    return "Unable to provide diagnosis"
agents.astra_free=SimpleNamespace(run=astra_run)

cases=get_case_set("synthetic","train")
results=[]
for case in cases:
  for agent_name in ("baseline","astra_free"):
    cfg=get_sdbench_config("synthetic")
    cfg.max_turns=2;cfg.compute_costs=False;cfg.compute_actual_workup_costs=False
    def surrogate_gatekeeper(*,messages,**kwargs):
        # Uses only explicitly requested test names. Never consults hidden diagnosis.
        prompt=str(messages[-1]["content"])
        requests=re.findall(r"(?m)^\s*ID\s+(\d+)\s*:\s*(.+?)\s*$",prompt)
        if not requests: requests=[("1","Unspecified test")]
        xml=[]
        for index,name in requests:
            value="No evidence available in this strictly uninformative negative-control gatekeeper."
            xml.append(f'<test_result id="{index}"><result>{value}</result><is_synthetic>true</is_synthetic></test_result>')
        return resp("\n".join(xml))
    def surrogate_judge(*,messages,**kwargs):
        # Conservative EXACT-STRING score only. This is not the Microsoft judge.
        prompt=str(messages[-1]["content"])
        m=re.search(r"Candidate Diagnosis:\s*(.*?)\s*Reference Diagnosis:\s*(.*?)\s*Please provide",prompt,re.S)
        candidate=m.group(1).strip() if m else ""
        reference=m.group(2).strip() if m else ""
        success=bool(candidate) and candidate.casefold()==reference.casefold()
        return resp("**REASONING**: surrogate strict string comparison, not clinical semantic grading.\n**SCORE**: "+("5" if success else "1"))
    start=time.monotonic()
    calls_before=len(usage)
    try:
        r=run_case(cfg,case,agent_name,model=real_qwen,gatekeeper_llm=surrogate_gatekeeper,judge_llm=surrogate_judge)
        label=r.get("model_diagnosis") or ""
        reference=case.get("final_diagnosis") or ""
        obj={"case_id":case["case_id"],"agent":agent_name,"status":"completed",
            "surrogate_exact_match":label.strip().casefold()==reference.strip().casefold(),
            "surrogate_judge_correct":bool(r.get("correct")),"surrogate_judge_score":r.get("diagnosis_score"),
            "abstained":label=="Unable to provide diagnosis",
            "requested_tests":r.get("requested_tests_only",[]),"rounds":r.get("num_test_rounds"),"qwen_calls":len(usage)-calls_before,
            "qwen_completion_tokens":sum(x["generated"] for x in usage[calls_before:]),
            "seconds":round(time.monotonic()-start,2),"prediction":label,"reference":reference}
    except Exception as e:
        obj={"case_id":case["case_id"],"agent":agent_name,"status":"error",
             "error":type(e).__name__,"error_detail":str(e)[:400],
             "traceback":traceback.format_exc()[-600:],"seconds":round(time.monotonic()-start,2)}
    results.append(obj)
    print("CASE",json.dumps({k:v for k,v in obj.items() if k not in ("prediction","reference")},ensure_ascii=False),flush=True)
    Path("/vercel/sdbench/astra_qwen_surrogate_eval.json").write_text(json.dumps({
     "scope":"official SDBench run_case on five official synthetic training cases",
     "model":"Qwen2.5-0.5B-Instruct Q4_K_M LOCAL real inference",
     "model_sha256":MODEL_SHA,
     "roles":"AGENT REAL QWEN; gatekeeper and judge are nonclinical deterministic surrogates",
     "official_science_comparability":"NO",
     "clinical_validation":"UNVERIFIED","cost_usd_api":0,
     "cases_completed":len(results),"rows":results,"llm_traces":usage},indent=2,ensure_ascii=False))
print("FINAL",json.dumps({"case_rows":len(results),"errors":sum(r["status"]=="error" for r in results),
 "exact_matches":sum(r.get("surrogate_exact_match",False) for r in results),"model_sha256":MODEL_SHA},ensure_ascii=False),flush=True)

