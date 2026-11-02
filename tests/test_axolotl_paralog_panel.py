import json
import unittest
from validation.axolotl_paralog_panel import (
    FAMILIES,parse_current_gene,make_preflight,compare_scores,
    parse_old_assembly_mapping,parse_gene_rows
)

class ParalogPanelTests(unittest.TestCase):
    def test_predeclared_four_families(self):
        self.assertEqual(FAMILIES,(("HAND1","HAND2"),("PAX6","PAX7"),
                                   ("SOX2","SOX3"),("SHH","DHH")))

    def test_duplicate_gene_id_not_counted_as_independent_case(self):
        hits={g:[] for pair in FAMILIES for g in pair}
        row={"legacy_gene_id":"AMEX60DD030069","chr":"chr3q",
             "length":28911,"start_1based":632140538,"end_1based":632169448,
             "historical_name":"HAND1 [nr]|HAND2 [hs]"}
        hits["HAND1"]=[row]
        hits["HAND2"]=[row]
        cases=make_preflight(hits,{"chr3q":"CM010932.2"})
        self.assertEqual(cases[0]["status"],"ELIGIBLE")
        self.assertEqual(cases[1]["status"],"DUPLICATE_OR_CONFLICTING_GENE_NAME_ON_SAME_HISTORIC_LOCUS")
        self.assertEqual(sum(z["status"]=="ELIGIBLE" for z in cases),1)
        self.assertTrue(cases[1]["duplicate_historic_id"])

    def test_missing_and_multiple_gene_candidates_are_kept_as_failures(self):
        hits={g:[] for pair in FAMILIES for g in pair}
        row={"legacy_gene_id":"A","chr":"chr3q","length":1000}
        hits["PAX6"]=[row,{**row,"legacy_gene_id":"B"}]
        cases=make_preflight(hits,{"chr3q":"CM010932.2"})
        status={z["symbol"]:z["status"] for z in cases}
        self.assertEqual(status["PAX6"],"AMBIGUOUS_LEGACY_GENE_COUNT")
        self.assertEqual(status["PAX7"],"AMBIGUOUS_LEGACY_GENE_COUNT")

    def test_provenance_parse_modern_gene_exact_assembly(self):
        x={"reports":[{"gene":{"symbol":"PAX6","gene_id":"42","tax_id":8296,
           "annotations":[{"assembly_accession":"GCF_040938575.1",
               "genomic_locations":[{"genomic_accession_version":"NC_090926.1",
               "genomic_range":{"begin":"1000","end":"3000"}}]}]}}]}
        r=parse_current_gene(json.dumps(x).encode(),"PAX6")
        self.assertEqual(r["start"],1000)
        self.assertEqual(r["end"],3000)
        self.assertEqual(r["length"],2001)
        with self.assertRaises(ValueError):
            parse_current_gene(json.dumps(x).encode(),"PAX7")

    def test_wrong_taxon_rejected(self):
        x={"reports":[{"gene":{"symbol":"PAX6","tax_id":9606,"gene_id":"42",
           "annotations":[]}}]}
        with self.assertRaises(ValueError):
            parse_current_gene(json.dumps(x).encode(),"PAX6")

    def test_missing_assembly_sha_rejected(self):
        with self.assertRaises(ValueError):
            parse_old_assembly_mapping(b"# synthetic spoofing")

    def test_missing_gtf_sha_rejected(self):
        with self.assertRaises(ValueError):
            parse_gene_rows(b"\x1f\x8b fake")

    def test_only_large_decisive_score_gap_can_prefer(self):
        metrics={
          "A":{"length_normalized_edit_distance":0.0008},
          "B":{"length_normalized_edit_distance":0.50},
        }
        self.assertEqual(compare_scores("A","B",metrics),"FAVORS_ORIGINAL")
        self.assertEqual(compare_scores("B","A",metrics),"FAVORS_PARALOG")
        metrics["B"]["length_normalized_edit_distance"]=0.11
        self.assertEqual(compare_scores("A","B",metrics),"INCONCLUSIVE")

    def test_both_bad_matches_never_make_inferred_truth(self):
        metrics={
          "A":{"length_normalized_edit_distance":0.72},
          "B":{"length_normalized_edit_distance":0.92},
        }
        self.assertEqual(compare_scores("A","B",metrics),"INCONCLUSIVE")

if __name__=="__main__":
    unittest.main()
