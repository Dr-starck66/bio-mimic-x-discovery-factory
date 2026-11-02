import json
import unittest
from validation.gse295849_metadata_bridge import parse_matrix_metadata, explicit_join, build_report

class GEOMetadataBridgeTests(unittest.TestCase):
    def sample_records(self, match=True):
        geo="""!Series_title\t"Original independent scientific series"
!Sample_geo_accession\t"GSM1001"\t"GSM1002"
!Sample_title\t"EPC old donor D1"\t"iNSC donor D1 late passage"
!Sample_characteristics_ch1\t"donor id: D1"\t"donor id: D1"
!Sample_characteristics_ch1\t"cell state: EPC"\t"cell state: iNSC"
!Sample_supplementary_file\t"ftp://example.org/204027260051_R01C01_Grn.idat"\t"ftp://example.org/204027260051_R02C01_Red.idat"
"""
        if not match:
            geo=geo.replace("204027260051_", "111111111111_")
        return parse_matrix_metadata(geo)

    def test_parses_real_GEO_style_vectors_and_repeated_characteristics(self):
        out=self.sample_records()
        self.assertEqual(len(out),2)
        self.assertEqual(out[0]["fields"]["characteristics_ch1"],["donor id: D1","cell state: EPC"])
        self.assertEqual(out[1]["chip_ids"],["204027260051_R02C01"])

    def test_two_unique_literal_join(self):
        ages=[{"chip_sample_id":"204027260051_R01C01","age_years":73.5},
              {"chip_sample_id":"204027260051_R02C01","age_years":12.3}]
        matched=explicit_join(self.sample_records(),ages)
        self.assertEqual([x["gsm"] for x in matched],["GSM1001","GSM1002"])

    def test_no_position_based_inference(self):
        ages=[{"chip_sample_id":"204027260051_R01C01","age_years":73.5}]
        self.assertIsNone(explicit_join(self.sample_records(match=False),ages)[0]["gsm"])

    def test_duplicate_source_chip_rejected_even_if_identical_donor(self):
        rec=self.sample_records()
        rec[1]["chip_ids"]=rec[0]["chip_ids"][:]
        res=explicit_join(rec,[{"chip_sample_id":"204027260051_R01C01","age_years":73.5}])[0]
        self.assertEqual(res["status"],"UNVERIFIED_NO_UNIQUE_SOURCE_MATCH")
        self.assertEqual(len(res["candidate_gsms"]),2)

    def test_duplicate_gsm_accessions_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicated"):
            parse_matrix_metadata('!Sample_geo_accession\t"GSM1"\t"GSM1"\n!Sample_title\t"x"\t"y"')

    def test_no_stages_inferred_as_pairs(self):
        ages={"computed_ages_years":[{"chip_sample_id":"204027260051_R01C01","age_years":73.5}]}
        result=build_report(self.sample_records(),ages)
        self.assertEqual(result["literal_gsm_matches"],1)
        self.assertEqual(result["donor_condition_passage_pairs"],"UNVERIFIED")
        self.assertEqual(result["independent_paired_deaging"],"UNVERIFIED")

if __name__=="__main__":
    unittest.main()
