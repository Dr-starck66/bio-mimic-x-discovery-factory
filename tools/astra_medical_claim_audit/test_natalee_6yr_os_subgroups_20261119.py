import math
import unittest
from natalee_6yr_os_subgroups_20261119 import SUBGROUPS, audit, holm, log_hr_se, compare

class Tests(unittest.TestCase):
    def test_seven_pairs(self): self.assertEqual(len(SUBGROUPS),7)
    def test_se_positive(self): self.assertGreater(log_hr_se(.79,.407,1.533)[1],0)
    def test_loghr(self): self.assertAlmostEqual(log_hr_se(.79,.407,1.533)[0],math.log(.79))
    def test_zero_refused(self):
        with self.assertRaises(ValueError): log_hr_se(0,.4,1.)
    def test_bad_order_refused(self):
        with self.assertRaises(ValueError): log_hr_se(.7,.8,1.)
    def test_nan_refused(self):
        with self.assertRaises(ValueError): log_hr_se(float("nan"),.4,1.)
    def test_missing_category_refused(self):
        with self.assertRaises(ValueError): compare([("a",.7,.4,1.)])
    def test_duplicate_category_refused(self):
        with self.assertRaises(ValueError): compare([("a",.7,.4,1.),("a",.8,.4,1.2)])
    def test_equal_hr(self):
        self.assertAlmostEqual(compare([("a",.8,.6,1.),("b",.8,.6,1.)])["p_Wald_approx"],1.)
    def test_holm(self): self.assertEqual(holm([.001,.04,.05]),[.003,.08,.08])
    def test_holm_invalid(self):
        with self.assertRaises(ValueError): holm([-.1,.5])
    def test_all_no_low_p(self): self.assertEqual(audit()["n_raw_p_lt_005"],0)
    def test_all_no_holm_p(self): self.assertEqual(audit()["n_holm_p_lt_005"],0)

if __name__=="__main__":unittest.main(verbosity=2)
