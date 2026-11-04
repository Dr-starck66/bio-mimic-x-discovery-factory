"""Real public metadata request evidence is not controlled RNA data access."""
import json
import unittest
from pathlib import Path

from validation.gse295849_rna_identity_gate import METH, RNA, structural_gate

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"reports/factory/GSE295849-RNA-LAWFUL-ACCESS-REQUEST-2026-11-02.json"

class LawfulRNARequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet=json.loads(PKG.read_text(encoding="utf-8"))
        cls.meth=json.loads(METH.read_text(encoding="utf-8"))
        cls.rna=json.loads(RNA.read_text(encoding="utf-8"))

    def test_processed_data_still_not_obtained(self):
        p=self.packet
        self.assertEqual(p["NIH_molecular_metadata"]["derived_Seq_RNA_Expression_samples"],47)
        self.assertFalse(p["NIH_molecular_metadata"]["processed_matrix_public_download_verified"])
        self.assertEqual(p["observed"]["independent_RNA_expression_values_obtained"],0)
        self.assertEqual(p["observed"]["adjusted_aging_signal_status"],"UNVERIFIED_NO_AUTHORIZED_2026_RNA_EXPRESSION")
        self.assertFalse(p["observed"]["dbGaP_DAR_submitted"])
        self.assertFalse(p["observed"]["request_sent"])

    def test_exact_six_donors_and_12_condition_matches(self):
        p=self.packet
        g=p["eligibility"]["paired_donors"]
        rows=p["eligibility"]["RNA_DNAm_metadata_link"]
        self.assertEqual(g,["190","216","218","286","287","288"])
        self.assertEqual(len(rows),12)
        self.assertEqual(len(set(x["RNA_run"] for x in rows)),12)
        self.assertEqual(len(set((x["donor_genotype"],x["stage"]) for x in rows)),12)
        self.assertEqual({x["stage"] for x in rows},{"D14","LP"})
        for x in rows:
            self.assertTrue(x["matched_methylation_GSMs"])
            self.assertTrue(x["NOT_verified_same_physical_aliquot"])
            self.assertTrue(x["NOT_verified_RNA_treatment"])

    def test_matches_existing_non_sensitive_public_NCBI_SRA_bridge(self):
        rna=self.rna["rna_samples"]
        for row in self.packet["eligibility"]["RNA_DNAm_metadata_link"]:
            found=[r for r in rna if r["rna_run"]==row["RNA_run"]]
            self.assertEqual(len(found),1)
            self.assertEqual(found[0]["matched_DNAm_GSMs"],row["matched_methylation_GSMs"])
            self.assertEqual(found[0]["rna_data_access"],"DBGAP_AUTHORIZED_ACCESS_ONLY")
        structural=structural_gate(self.meth,self.rna)
        self.assertEqual(structural["condition_matched_RNA_runs"],35)

    def test_fail_closed_mailguard_and_no_authorization_inferred(self):
        p=self.packet
        self.assertTrue(all(r["outbound_permission"]=="FAIL_CLOSED" for r in p["validated_institutional_contacts"]))
        self.assertTrue(all(r["mailbox_control_proof"]=="UNVERIFIED" for r in p["validated_institutional_contacts"]))
        self.assertIn("institution",p["access_routes"]["A"].lower())
        self.assertIn("authorized",p["access_routes"]["C"].lower())

if __name__=="__main__":unittest.main()
