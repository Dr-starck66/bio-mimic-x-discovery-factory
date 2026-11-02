"""Strict REAL public source gates, separate synthetic molecular-expression tests."""
import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from validation.gse295849_rna_identity_gate import (
    METH, RNA, ERYTHROID, NEURAL, structural_gate, read_count_matrix,
    identity_scores, conditioned_age_delta, main,
)

class RnaOrthogonalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.methyl = json.loads(METH.read_text(encoding="utf-8"))
        cls.metadata = json.loads(RNA.read_text(encoding="utf-8"))

    def test_actual_48_SRA_restricted_and_35_condition_matches(self):
        r = structural_gate(self.methyl,self.metadata)
        self.assertEqual(r["rnaseq_run_count"],48)
        self.assertEqual(r["rnaseq_controlled_access_count"],48)
        self.assertEqual(r["condition_matched_RNA_runs"],35)
        self.assertEqual(r["DNAm_Clock_sample_count"],60)
        self.assertEqual(r["RNA_identity_score_status"],"UNVERIFIED")

    def test_exactly_six_RNA_D14_LP_paired_donors(self):
        r = structural_gate(self.methyl,self.metadata)
        self.assertEqual(r["independent_donors_with_RNA_D14_and_LP_condition_metadata"],6)
        self.assertEqual(r["D14_LP_paired_donor_genotypes"],["190","216","218","286","287","288"])
        self.assertTrue(r["no_same_biological_aliquot_claim"])
        self.assertTrue(all(not a["physical_aliquot_verified"] for a in r["RNA_to_DNAm_accession_links"]))

    def test_access_restriction_cannot_be_labeled_public(self):
        m = json.loads(json.dumps(self.metadata))
        m["rna_samples"][0]["rna_data_access"]="PUBLIC"
        with self.assertRaisesRegex(ValueError,"access status"):
            structural_gate(self.methyl,m)

    def test_wrong_rna_to_geo_GSM_mapping_rejected(self):
        m = json.loads(json.dumps(self.metadata))
        m["rna_samples"][0]["matched_DNAm_GSMs"]=["GSM00000000"]
        with self.assertRaisesRegex(ValueError,"crosswalk mismatch"):
            structural_gate(self.methyl,m)

    def test_missing_original_methylation_sample_rejected(self):
        m=json.loads(json.dumps(self.methyl))
        m["sample_level_ages"].pop()
        with self.assertRaisesRegex(ValueError,"60 unique"):
            structural_gate(m,self.metadata)

    def test_protected_data_is_never_opened_in_public_Github_CI(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"out.json"
            with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}):
                with self.assertRaisesRegex(PermissionError,"never in public GitHub Actions"):
                    main(["--rna-counts",str(Path(td)/"controlled.tsv"),
                          "--local-authorized","--out",str(out)])
            self.assertFalse(out.exists())

    def test_metadata_only_runtime_is_partial_not_mechanistic_pass(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"status.json"
            self.assertEqual(main(["--out",str(out)]),0)
            data=json.loads(out.read_text())
            self.assertEqual(data["status"],"PARTIAL_NO_AUTHORIZED_TRANSCRIPTOME")
            self.assertEqual(data["public_metadata"]["RNA_expression_status"],
                             "RESTRICTED_NO_COUNTS_AVAILABLE")
            self.assertEqual(data["public_metadata"]["age_effect_after_identity_adjustment"],
                             "UNVERIFIED")
            self.assertEqual(data["clinical_age_rejuvenation"],"UNVERIFIED")

    def fixture_full_rna_counts(self, f, markers_only=False):
        eligible={"190","216","218","286","287","288"}
        runs=[x for x in self.metadata["rna_samples"]
              if x["donor_genotype_from_public_SRA_title"] in eligible and
              x["cell_type"]=="iNSC" and x["harvest_stage"] in ("D14","LP") and x["matched_DNAm_GSMs"]]
        self.assertEqual(len(runs),12)
        with f.open("wt",encoding="utf-8",newline="") as fh:
            writer=csv.writer(fh,delimiter="\t")
            writer.writerow(["gene_symbol"]+[x["rna_run"] for x in runs])
            for gene in (*NEURAL,*ERYTHROID):
                values=[]
                for i,x in enumerate(runs):
                    is_lp=x["harvest_stage"]=="LP"
                    base=1200+((i%6)*70)
                    values.append(base+ (850 if is_lp and gene in NEURAL else 0) +
                                        (850 if not is_lp and gene in ERYTHROID else 0))
                writer.writerow([gene]+values)
            if not markers_only:
                for i in range(1100):
                    writer.writerow([f"NOISE{i:05d}"]+[100+(i+j)%19 for j in range(len(runs))])
        return [x["rna_run"] for x in runs]

    def test_expression_score_never_confuses_stage_label_for_measured_expression(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"rna.tsv"
            order=self.fixture_full_rna_counts(f)
            table=read_count_matrix(f,order)
            self.assertGreaterEqual(table["n_genes"],1000)
            scores=identity_scores(table)
            self.assertEqual(set(scores),set(order))
            self.assertGreater(len(set(round(s,3) for s in scores.values())),2)
            result=conditioned_age_delta(self.methyl,self.metadata,scores)
            self.assertEqual(result["donor_pairs"],6)
            self.assertEqual(result["age_reset_independent_of_cell_fate"],"UNVERIFIED")
            self.assertTrue(result["fit_residual_sd_years"]>=0)

    def test_real_normalized_values_are_rejected_as_raw_counts(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"rna.tsv"
            order=self.fixture_full_rna_counts(f,markers_only=True)
            s=f.read_text()
            f.write_text(s.replace("\t1200","\t1.2",1))
            with self.assertRaisesRegex(ValueError,"nonnegative integers"):
                read_count_matrix(f,order,min_genes=12)

    def test_missing_predeclared_identity_marker_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"rna.tsv"
            order=self.fixture_full_rna_counts(f,markers_only=True)
            s=f.read_text().replace("\nPAX6\t","\nPAX6_MISSING\t")
            f.write_text(s)
            with self.assertRaisesRegex(ValueError,"identity genes missing"):
                read_count_matrix(f,order,min_genes=12)

if __name__=="__main__":
    unittest.main()
