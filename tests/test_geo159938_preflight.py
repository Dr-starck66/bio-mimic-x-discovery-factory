"""Offline tests; constructed records are NOT GEO scientific observations."""
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "science" / "geo159938_preflight.py"
spec = importlib.util.spec_from_file_location("geo159938_preflight", MODULE_PATH)
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)


def entry(i, sp, day, tissue="dorsal dermis", genotype="WT", region="Center"):
    organism = "Acomys cahirinus" if sp == "Acomys" else "Mus musculus"
    return (f"^SAMPLE = GSM{i}\n!Sample_title = Constructed test sample\n"
            f"!Sample_organism_ch1 = {organism}\n"
            f"!Sample_characteristics_ch1 = tissue: {tissue}\n"
            f"!Sample_characteristics_ch1 = post-wound day (pwd): {day}\n"
            f"!Sample_characteristics_ch1 = region: {region}\n"
            f"!Sample_characteristics_ch1 = genotype: {genotype}\n")


class TestGeo159938Preflight(unittest.TestCase):
    def test_real_geo_metadata_fields_from_three_public_pages_do_not_pass(self):
        # Metadata fields transcribed from GSM4850927, GSM4850938, GSM4850939.
        soft = (entry(4850927, "Mus", 14) +
                entry(4850938, "Acomys", 14, region="N.A.") +
                entry(4850939, "Acomys", 21, region="N.A.")).encode()
        report = gate.audit(soft, expected_samples=3)
        self.assertEqual(report["status"], "NOT_COMPARABLE_ORIGINAL_TIMEPOINTS_AND_STRATA")
        self.assertEqual(report["sample_count"], 3)
        self.assertFalse(any(x["all_six_cells_at_least_three_GSM"] for x in report["strata"]))

    def test_matching_accessions_are_not_causal_or_donor_pass(self):
        soft = "".join(entry(1000+i*100+j, sp, day)
                       for i, (sp, day) in enumerate([(sp, d) for sp in ("Acomys", "Mus") for d in (0, 7, 14)])
                       for j in range(3)).encode()
        report = gate.audit(soft, expected_samples=18)
        self.assertEqual(report["status"], "UNVERIFIED_DONOR_AND_ASSAY_QC")
        self.assertEqual(report["possible_eligible_strata"], 1)
        self.assertEqual(report["total_accessions_by_species"], {"Acomys": 9, "Mus": 9})

    def test_different_tissue_cannot_fill_missing_cell(self):
        soft = (entry(1, "Acomys", 0) + entry(2, "Mus", 0, tissue="dorsal epidermis")).encode()
        report = gate.audit(soft, expected_samples=2)
        self.assertEqual(report["status"], "NOT_COMPARABLE_ORIGINAL_TIMEPOINTS_AND_STRATA")

    def test_duplicate_gsm_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            gate.audit((entry(1234,"Mus",0)*2).encode(), expected_samples=2)

    def test_incomplete_manifest_is_not_analysed(self):
        report = gate.audit(entry(1234,"Mus",0).encode(), expected_samples=25)
        self.assertEqual(report["status"], "UNVERIFIED_METADATA_INCOMPLETE")

    def test_missing_day_rejected(self):
        with self.assertRaisesRegex(ValueError,"day"):
            gate.audit(entry(1234,"Mus",0).replace("day (pwd): 0", "day (pwd): unknown").encode(), expected_samples=1)


if __name__ == '__main__':
    unittest.main()
