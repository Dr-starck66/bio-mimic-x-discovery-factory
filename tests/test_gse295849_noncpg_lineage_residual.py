"""Adversarial non-clock CpG fate proxy: no fake RNA and strict GEO source pins."""
import copy
import json
import unittest

from validation.gse295849_noncpg_lineage_residual import (
    AGES, FEATURE_COUNT, MODEL_SHA, PART_SHA, PART_SAMPLES,
    PAT_CPG, clock_probes_from_pinned_model, gate_report,
    merge_parts, selected_probe,
)


class CpGMolecularIdentityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ages=json.loads(AGES.read_text(encoding="utf-8"))["sample_level_ages"]
        assert len(cls.ages)==60

    def test_predeclared_hash_sampling_independent_of_age_and_donor(self):
        x=selected_probe("cg12140144")
        self.assertEqual(x,selected_probe("cg12140144"))
        self.assertFalse(selected_probe("not_a_probed_CpG"))
        self.assertFalse(selected_probe("cg001"))
        self.assertEqual(FEATURE_COUNT,200)

    def test_fake_model_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"SHA changed"):
            clock_probes_from_pinned_model(b"fake torch weights")

    def test_wrong_shard_count_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"three verified shards"):
            merge_parts([],self.ages)

    def test_wrong_source_sha_fails_closed(self):
        fake=[{"part":p,"source_sha256":"0"*64,"model_sha256":MODEL_SHA,
               "sample_chips":[],"nonclock_probes":{}} for p in ("1","2","3")]
        with self.assertRaisesRegex(ValueError,"SHA not pinned"):
            merge_parts(fake,self.ages)

    def test_wrong_or_duplicate_chip_fails_closed(self):
        chips=[x["chip_sample_id"] for x in self.ages]
        fake=[]
        pos=0
        for part in ("1","2","3"):
            n=PART_SAMPLES[part]
            fake.append({"part":part,"source_sha256":PART_SHA[part],
                         "model_sha256":MODEL_SHA,
                         "sample_chips":chips[pos:pos+n],
                         "nonclock_probes":{}})
            pos+=n
        fake[1]["sample_chips"][0]=fake[0]["sample_chips"][0]
        with self.assertRaisesRegex(ValueError,"duplicated chip"):
            merge_parts(fake,self.ages)

    def test_full_synthetic_proxy_never_establishes_mechanistic_independence(self):
        # Synthetic methylation is used ONLY to test the code path, never
        # compared as though real sample-level data had been retrieved.
        actual=self.ages
        rows=[]
        for i,x in enumerate(actual):
            cell=x["cell_type"]
            stage=x["stage"]
            # This synthetic assay exhibits massive cell-state effects
            # despite true clock values coming from the published age JSON.
            identity=(0.1 if cell=="EPC" else
                      0.9 if cell=="smNPC" else
                      0.4 if stage=="D14" else
                      0.65 if stage=="LP" else 0.7)
            rows.append((x["chip_sample_id"],identity))
        chips=[x for x,s in rows]
        identifiers=[f"cg{i:08d}" for i in range(60000) if selected_probe(f"cg{i:08d}")][:3400]
        self.assertEqual(len(identifiers),3400)
        fake=[]
        pos=0
        for part in ("1","2","3"):
            size=PART_SAMPLES[part]
            sample=rows[pos:pos+size]
            features={}
            for i,cpg in enumerate(identifiers):
                # Stable informative signature, no clock probe leakage.
                features[cpg]=[round(max(0,min(1,identity+((i%9)-4)*.0002)),6)
                               for chip,identity in sample]
            fake.append({"part":part,"source_sha256":PART_SHA[part],
                         "model_sha256":MODEL_SHA,
                         "sample_chips":[x[0] for x in sample],
                         "nonclock_probes":features})
            pos+=size
        report=gate_report(fake,{"sample_level_ages":actual})
        self.assertEqual(report["n_actual_paired_D14_LP_donors"],6)
        self.assertEqual(report["reference_training_donors"],9)
        self.assertEqual(report["cell_fate_independent_rejuvenation"],"UNVERIFIED")
        self.assertEqual(report["orthogonal_transcriptomics"],"UNVERIFIED_PROTECTED_ACCESS")
        self.assertEqual(report["n_common_preselected_clock_excluded_CpGs"],3400)
        self.assertEqual(report["RNA_2026_expressions_loaded"],False)
        self.assertEqual(report["n_identity_shifts_towards_mature_neural_reference"],6)


if __name__=="__main__":
    unittest.main()
