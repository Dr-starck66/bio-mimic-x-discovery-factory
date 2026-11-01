"""Synthetic-only negative controls for real 391-CpG clock pipeline."""
import gzip
import math
import tempfile
import unittest
from pathlib import Path

from validation.gse295849_skinblood_clock import inverse_age, collect_clock_cpgs

class RealClockSafetyTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.f=Path(self.d.name)/"fixture.gz"
    def put(self,body):
        with gzip.open(self.f,"wt") as h:
            h.write(body)
    def test_inverse_age_branch(self):
        self.assertAlmostEqual(inverse_age(0),20.0)
        self.assertAlmostEqual(inverse_age(-1),21*math.exp(-1)-1)
        self.assertAlmostEqual(inverse_age(1),41.0)
    def test_two_complete_features(self):
        self.put("204027260051_R01C01\t204027260051_R02C01\ncg00000001\t0.25\t0.75\ncg00000002\t0.5\t0.5\n")
        h,mat=collect_clock_cpgs(self.f,["cg00000001","cg00000002"])
        self.assertEqual(len(h),2)
        self.assertEqual(mat["cg00000001"],[0.25,0.75])
    def test_labeled_cpg_header(self):
        self.put("IlmnID\t204027260051_R01C01\t204027260051_R02C01\n"+
                 "cg00000001\t0.2\t0.6\n"+
                 "cg00000002\t0.3\t0.7\n")
        ids,vals=collect_clock_cpgs(self.f,["cg00000001","cg00000002"])
        self.assertEqual(ids,["204027260051_R01C01","204027260051_R02C01"])
        self.assertEqual(vals["cg00000002"],[0.3,0.7])

    def test_sample_only_header_with_final_blank(self):
        self.put("204027260051_R01C01\t204027260051_R02C01\t\n"+
                 "cg00000001\t0.2\t0.6\n"+
                 "cg00000002\t0.3\t0.7\n")
        ids,vals=collect_clock_cpgs(self.f,["cg00000001","cg00000002"])
        self.assertEqual(ids,["204027260051_R01C01","204027260051_R02C01"])
        self.assertEqual(vals["cg00000001"],[0.2,0.6])

    def test_missing_feature_never_imputed(self):
        self.put("204027260051_R01C01\t204027260051_R02C01\ncg00000001\t0.25\t0.75\n")
        with self.assertRaisesRegex(ValueError,"coverage 1/2"):
            collect_clock_cpgs(self.f,["cg00000001","cg00000002"])
    def test_duplicate_probe_fails(self):
        self.put("204027260051_R01C01\ncg00000001\t0.5\ncg00000001\t0.5\n")
        with self.assertRaisesRegex(ValueError,"duplicate"):
            collect_clock_cpgs(self.f,["cg00000001"])
    def test_wrong_sample_header_fails(self):
        self.put("example\tSample\ncg00000001\t0.5\t0.5\n")
        with self.assertRaisesRegex(ValueError,"unexpected"):
            collect_clock_cpgs(self.f,["cg00000001"])
    def test_value_out_of_range_rejected(self):
        self.put("204027260051_R01C01\ncg00000001\t1.5\n")
        with self.assertRaisesRegex(ValueError,"non-beta"):
            collect_clock_cpgs(self.f,["cg00000001"])

if __name__=="__main__":
    unittest.main()
