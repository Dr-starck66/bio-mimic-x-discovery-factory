import copy,unittest
from validation.hand2_sequence_flank_gate import evaluate
class Tests(unittest.TestCase):
 def setUp(self):
  self.r={"k":31,"cross_checks":{"local_window_length_validation":"PASS_4_OF_4"},"results":[]}
  for old in ("old_left","old_right"):
   for modern in ("modern_left","modern_right"):
    for orient in ("forward","reverse_complement"):
     n=3888 if (old,modern,orient)==("old_left","modern_right","reverse_complement") else 4268 if (old,modern,orient)==("old_right","modern_left","reverse_complement") else 0
     self.r["results"].append({"old":old,"modern":modern,"modern_orientation":orient,"shared_distinct_31mers":n})
 def test_positive(self):self.assertEqual(evaluate(self.r)["status"],"PARTIAL_SEQUENCE_FLANK_RECIPROCITY")
 def test_negative_nonzero(self):
  x=copy.deepcopy(self.r);x["results"][0]["shared_distinct_31mers"]=1
  self.assertEqual(evaluate(x)["status"],"FAIL_CROSSCHECK")
 def test_missing(self):
  x=copy.deepcopy(self.r);x["results"].pop()
  self.assertEqual(evaluate(x)["status"],"FAIL_CROSSCHECK")
 def test_duplicate(self):
  x=copy.deepcopy(self.r);x["results"].append(x["results"][0])
  with self.assertRaises(ValueError):evaluate(x)
 def test_wrong_positive(self):
  x=copy.deepcopy(self.r);x["results"][3]["shared_distinct_31mers"]=3887
  self.assertEqual(evaluate(x)["status"],"FAIL_CROSSCHECK")
if __name__=="__main__":unittest.main()
