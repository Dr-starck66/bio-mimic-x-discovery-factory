import unittest
from retrieval_scifact import BM25, evaluate
DOCS=[
 {"doc_id":1,"title":"cancer lung chemotherapy randomized","abstract":["The control group had similar survival."]},
 {"doc_id":2,"title":"heart clinical trial","abstract":["Cardiovascular effect was observed."]},
 {"doc_id":3,"title":"random biology","abstract":["A new protein was isolated."]}]
class RetrievalTests(unittest.TestCase):
 def setUp(self):self.i=BM25(DOCS)
 def test_unique_and_deterministic(self):
  self.assertEqual(self.i.rank("heart cardiovascular"),self.i.rank("heart cardiovascular"))
 def test_actual_retrieval(self):
  self.assertEqual(self.i.rank("heart cardiovascular",2)[0]["doc_id"],"2")
 def test_query_no_keyword(self):self.assertEqual(self.i.rank(""),[])
 def test_query_wrong_type(self):
  with self.assertRaises(TypeError):self.i.rank({"evidence":1})
 def test_duplicate_ids(self):
  with self.assertRaises(ValueError):BM25(DOCS+[DOCS[0]])
 def test_k_guard(self):
  with self.assertRaises(ValueError):self.i.rank("heart",0)
 def test_gold_is_only_evaluation(self):
  claims=[{"id":99,"claim":"heart cardiovascular","cited_doc_ids":[1],"evidence":{"2":[{"label":"SUPPORT","sentences":[0]}]}}]
  res=evaluate(self.i,claims,ks=(1,3),store_topk=1)
  self.assertEqual(res["retrieved"][0]["topk"][0]["doc_id"],"2")
  self.assertEqual(res["hit_counts"]["1"],1)
 def test_negative_control_no_gold(self):
  claims=[{"id":1,"claim":"random biology","evidence":{},"cited_doc_ids":[1]}]
  res=evaluate(self.i,claims,ks=(1,),store_topk=1)
  self.assertEqual(res["n_with_gold_evidence"],0)
  self.assertIsNone(res["recall_at_k"]["1"])
if __name__=="__main__":unittest.main()
