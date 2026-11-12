import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmark import benchmark, evaluate, control_predict
EX=[{"id":1,"claim":"A increases B","ground_truth":"SUPPORT","RoBERTa (fine-tuned)":"SUPPORT"},
    {"id":2,"claim":"A does not increase B","ground_truth":"CONTRADICT","RoBERTa (fine-tuned)":"SUPPORT"},
    {"id":3,"claim":"No results", "ground_truth":"NEI","RoBERTa (fine-tuned)":"CONTRADICT"},
    {"id":4,"claim":"A works","ground_truth":"CONTRADICT","RoBERTa (fine-tuned)":"CONTRADICT"}]
class BenchmarkTests(unittest.TestCase):
    def test_confusion(self):
        r=evaluate(EX,"RoBERTa (fine-tuned)")["contradiction_positive_binary"]
        self.assertEqual((r["TP"],r["FP"],r["FN"],r["TN"]),(1,1,1,1))
    def test_ast_negative_control(self):
        r=evaluate(EX,"ASTRA_NEGATIVE_CONTROL")["contradiction_positive_binary"]
        self.assertEqual((r["TP"],r["FP"],r["FN"],r["TN"]),(1,1,1,1))
    def test_nei_counted_negative_not_removed(self):
        r=evaluate(EX,"RoBERTa (fine-tuned)")
        self.assertEqual(sum(r["multiclass_confusion_gold_rows_prediction_cols"]["NEI"].values()),1)
    def test_duplicate_fail(self):
        with self.assertRaises(ValueError):evaluate(EX+[EX[0]],"ASTRA_NEGATIVE_CONTROL")
    def test_invalid_label_fail(self):
        a=json.loads(json.dumps(EX)); a[0]["ground_truth"]="FAKE"
        with self.assertRaises(ValueError):evaluate(a,"ASTRA_NEGATIVE_CONTROL")
    def test_no_unknown_zero_denominator(self):
        r=evaluate(EX[:1],"ASTRA_NEGATIVE_CONTROL")["contradiction_positive_binary"]
        self.assertIsNone(r["recall"])
    def test_reproducibility(self):
        raw=json.dumps(EX,sort_keys=True).encode()
        self.assertEqual(benchmark(raw),benchmark(raw))
    def test_negative_control_only_claim(self):
        self.assertEqual(control_predict("A does not increase risk"),"CONTRADICT")
if __name__=="__main__":unittest.main()
