"""Synthetic verification only; no NHANES observations in this file."""
import importlib.util
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

SRC=Path(__file__).resolve().parents[1]/"research"/"astra_obesity_omega"/"nhanes_analysis.py"
spec=importlib.util.spec_from_file_location("astra_nhanes", SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture(n=540, seed=11):
    rng=np.random.default_rng(seed)
    ids=np.arange(n)+100000
    bmi=np.clip(rng.normal(28,5,n),17,53)
    wc=43+1.48*bmi+rng.normal(0,6,n)
    height=rng.normal(166,9,n)
    age=rng.integers(20,80,n)
    a1c=5.2+.09*(bmi-21)+.006*(wc-90)+.009*(age-40)+rng.normal(0,.68,n)
    group=np.arange(n)%18
    demo=pd.DataFrame({"SEQN":ids,"RIDAGEYR":age,"RIAGENDR":rng.integers(1,3,n),
         "RIDEXPRG":np.full(n,2.),"SDMVSTRA":100+group//2,"SDMVPSU":1+group%2})
    bmx=pd.DataFrame({"SEQN":ids,"BMXBMI":bmi,"BMXWAIST":wc,"BMXHT":height})
    ghb=pd.DataFrame({"SEQN":ids,"LBXGH":a1c,"WTPH2YR":rng.uniform(.2,10,n)})
    return [demo,bmx,ghb]

class TestNHANES(unittest.TestCase):
    def test_unique_merge(self):
        a,b,c=fixture()
        a=pd.concat([a,a.iloc[:1]])
        with self.assertRaises(Exception):
            m.prepare([a,b,c])

    def test_no_pregnant(self):
        frames=fixture()
        frames[0].loc[0,"RIDEXPRG"]=1
        x,stats=m.prepare(frames)
        self.assertEqual(len(x),539)

    def test_age_adults(self):
        frames=fixture()
        frames[0].loc[0,"RIDAGEYR"]=19
        x,stats=m.prepare(frames)
        self.assertEqual(len(x),539)

    def test_phlebotomy_positive(self):
        frames=fixture()
        frames[2].loc[0,"WTPH2YR"]=0
        x,stats=m.prepare(frames)
        self.assertEqual(len(x),539)

    def test_no_imputation(self):
        frames=fixture()
        frames[1].loc[0,"BMXWAIST"]=np.nan
        x,stats=m.prepare(frames)
        self.assertEqual(len(x),539)

    def test_lab_threshold_not_diagnosis(self):
        x,_=m.prepare(fixture())
        self.assertTrue((x.y==(x.LBXGH>=6.5).astype(int)).all())

    def test_group_holdout(self):
        x,_=m.prepare(fixture())
        out=m.evaluate(x)
        self.assertEqual(len(out["folds"]),5)
        self.assertFalse(out["geographically_independent"])
        self.assertFalse(out["intervention_effect_evaluated"])

    def test_negative_control_present(self):
        x,_=m.prepare(fixture())
        out=m.evaluate(x)
        self.assertIn("NEGATIVE_SHUFFLED_WHTR",out["weighted_metrics"])

    def test_deterministic_scoring(self):
        x,_=m.prepare(fixture())
        self.assertEqual(m.evaluate(x),m.evaluate(x))

    def test_insufficient_cases(self):
        with self.assertRaisesRegex(ValueError,"Insufficient"):
            m.prepare(fixture(n=100))

    def test_insufficient_groups(self):
        frames=fixture()
        frames[0]["SDMVSTRA"]=100
        frames[0]["SDMVPSU"]=1
        with self.assertRaisesRegex(ValueError,"Insufficient"):
            m.prepare(frames)

    def test_no_invented_clinical_effect(self):
        self.assertIn("NOT a clinical obesity diagnosis",m.__doc__)

if __name__=="__main__":
    unittest.main()
