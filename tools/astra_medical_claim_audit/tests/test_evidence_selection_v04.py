import unittest
from scifact_specialized_open_v04 import select_evidence_sentences
class EvidenceSelectionV04Tests(unittest.TestCase):
 def test_overlap_select(self):
  items=["Fish swim underwater.","Cancer treatments affect survival.","The lung cancer patients responded."]
  out=select_evidence_sentences("lung cancer survival",items,limit=2)
  self.assertNotIn("Fish",out)
  self.assertIn("survival",out)
  self.assertIn("lung cancer",out)
 def test_no_gold_ids(self):
  out=select_evidence_sentences("protein response",["irrelevant text","protein response observed"],limit=1)
  self.assertEqual(out,"protein response observed")
 def test_no_text(self):self.assertEqual(select_evidence_sentences("any",[],limit=3),"")
 def test_deterministic(self):
  s=["foo first","foo second","other"]
  self.assertEqual(select_evidence_sentences("foo",s,limit=2),"foo first foo second")
 def test_limit_guard(self):
  with self.assertRaises(ValueError):select_evidence_sentences("hi",["test"],limit=0)
if __name__=="__main__":unittest.main()
