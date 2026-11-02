"""Synthetic fixtures; NOT evidence of a biological effect."""
import unittest
from validation.gse295849_paired_analysis import analyze_crosswalk

class GSE295849PairedTests(unittest.TestCase):
    def synthetic(self):
        rows=[]; ages={}
        for d in range(1,13):
            for j,(cell,stage,tx) in enumerate([("EPC","D0","None"),("iNSC","LP","None"),("iNSC","LP","Glycerol"),("smNPC","LP","None"),("iNSC","D14","None")]):
                chip=f"{d:012d}_R{j+1:02d}C01"
                rows.append({"chip_sample_id":chip,"gsm":f"GSM{d*10+j}",
                             "donor_genotype":str(d),"cell_type":cell,
                             "harvest_stage":stage,"treatment":tx})
                ages[chip]=float(60+d) if j==0 else (float(10+d) if j==1 else float(20+d))
        return {"samples":rows},ages
    def test_one_donor_one_vote(self):
        cw,ages=self.synthetic()
        r=analyze_crosswalk(cw,ages)
        self.assertEqual(r["status"],"PASS_DESCRIPTIVE_WITHIN_DONOR_PAIRED_CLOCK_COMPARISON")
        self.assertEqual(r["donor_count"],12)
        self.assertEqual(r["aggregate"]["paired_mean_delta_years"],-50)
        self.assertEqual(r["aggregate"]["n_negative_deltas"],12)
        self.assertEqual(len(r["primary_contrasts"]),12)
    def test_metadata_permutation_does_not_change_results(self):
        cw,ages=self.synthetic()
        baseline=analyze_crosswalk(cw,ages)["aggregate"]["paired_mean_delta_years"]
        cw["samples"].reverse()
        self.assertEqual(analyze_crosswalk(cw,ages)["aggregate"]["paired_mean_delta_years"],baseline)
    def test_near_zero_clock_ages_never_produce_impossible_percent(self):
        cw,ages=self.synthetic()
        donor1=[r["chip_sample_id"] for r in cw["samples"] if r["donor_genotype"]=="1" and r["treatment"]=="None"]
        self.assertEqual(len(donor1),3)  # EPC D0, untreated LP and D14
        ages[donor1[0]]=0.42
        ages[donor1[1]]=-0.26
        result=analyze_crosswalk(cw,ages)
        sample=result["primary_contrasts"][0]
        self.assertIsNone(sample["reduction_pct_of_EPC_clock_age"])
        self.assertFalse(sample["relative_metric_usable"])
        self.assertEqual(sample["difference_LP_minus_D0_years"],-0.68)
        self.assertEqual(result["sensitivity_excluding_near_zero_clock_ages"]["n_donors"],11)
        self.assertEqual(result["aggregate"]["n_negative_deltas"],12)

    def test_missing_chips_fails_closed(self):
        cw,ages=self.synthetic();ages.pop(next(iter(ages)))
        with self.assertRaisesRegex(ValueError,"requires full 60"):
            analyze_crosswalk(cw,ages)
    def test_duplicate_chip_in_source_fails_closed(self):
        cw,ages=self.synthetic();cw["samples"][0]["chip_sample_id"]=cw["samples"][1]["chip_sample_id"]
        with self.assertRaisesRegex(ValueError,"not bijective"):
            analyze_crosswalk(cw,ages)
    def test_treated_LP_and_smNPC_excluded(self):
        cw,ages=self.synthetic();r=analyze_crosswalk(cw,ages)
        self.assertEqual(r["primary_contrasts"][0]["n_untreated_LP_chips"],1)
        self.assertTrue(r["negative_controls"]["treated_LP_excluded_from_primary"])
        self.assertTrue(r["negative_controls"]["smNPC_excluded_from_primary"])

if __name__=="__main__":unittest.main()
