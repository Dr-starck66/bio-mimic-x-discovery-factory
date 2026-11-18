"""Regression tests against the actual astra_run function extracted from the GitHub-synced file."""
import ast,json,unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE=Path(__file__).with_name("astra_qwen_surrogate_eval.py")
tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="astra_run"]
assert len(functions)==1
ns={"json":json}
exec(compile(ast.Module(body=functions,type_ignores=[]),str(SOURCE),"exec"),ns)
astra_run=ns["astra_run"]

class FakeRunner:
    def __init__(self,result):
        self.turns_left=3
        self.result=result
        self.orders=[]
    def __call__(self,names):
        self.orders.extend(names)
        self.turns_left-=1
        results=[] if self.result is None else [{"test_name":names[0],"results":self.result}]
        return SimpleNamespace(test_results=results,limit_messages=[])

class FakeLLM:
    def __init__(self,actions):
        self.actions=iter(actions)
    def __call__(self,*,messages,**kwargs):
        a=next(self.actions)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(role="assistant",content=json.dumps(a)))])

def exercise(result,actions=None):
    acts=actions if actions is not None else [
        {"action":"test","name":"CBC"},
        {"action":"diagnosis","value":"SYNTHETIC-PLACEHOLDER"}]
    runner=FakeRunner(result)
    collector={}
    diagnosis=astra_run("Entirely synthetic research summary",runner,FakeLLM(acts),collector,SimpleNamespace(debug=False))
    return diagnosis,collector,runner

class CorrectedEvidenceGuardTests(unittest.TestCase):
    def assert_abstain(self,result):
        result_text,col,r=exercise(result)
        self.assertEqual(result_text,"Unable to provide diagnosis")
        self.assertEqual(col["astra_evidence_steps"],0)
        self.assertEqual(len(r.orders),1)
    def test_uninformative_gatekeeper(self):
        self.assert_abstain("No evidence available in this strictly uninformative negative-control gatekeeper.")
    def test_missing_results(self):
        self.assert_abstain("Results not available for Test to order: CBC")
    def test_explicit_no_diagnostic_evidence(self):
        self.assert_abstain("No diagnostic evidence at this time")
    def test_uninformative_uppercase(self):
        self.assert_abstain("NO EVIDENCE AVAILABLE")
    def test_empty_string(self):
        self.assert_abstain("")
    def test_whitespace(self):
        self.assert_abstain("  ")
    def test_zero_results(self):
        self.assert_abstain(None)
    def test_informative_result_allows_decision(self):
        pred,col,r=exercise("Fabricated test result: value 12.0")
        self.assertEqual(pred,"SYNTHETIC-PLACEHOLDER")
        self.assertEqual(col["astra_evidence_steps"],1)
    def test_no_prior_only_diagnosis(self):
        pred,col,r=exercise("UNUSED",[{"action":"diagnosis","value":"SYNTHETIC-PLACEHOLDER"}])
        self.assertEqual(pred,"Unable to provide diagnosis")
        self.assertEqual(len(r.orders),0)
    def test_explicit_abstention(self):
        pred,col,r=exercise("UNUSED",[{"action":"abstain"}])
        self.assertEqual(pred,"Unable to provide diagnosis")
        self.assertEqual(len(r.orders),0)
    def test_repeated_test_is_rejected(self):
        pred,col,r=exercise("Diagnostic marker measured",[
            {"action":"test","name":"CBC"},{"action":"test","name":"CBC"},
            {"action":"diagnosis","value":"SYNTHETIC-PLACEHOLDER"}])
        self.assertEqual(pred,"Unable to provide diagnosis")
        self.assertEqual(len(r.orders),1)

if __name__=="__main__":unittest.main(verbosity=2)

