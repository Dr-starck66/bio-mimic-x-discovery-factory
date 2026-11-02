"""2018 public RNA independent identity reference: real GEO labels, synthetic adversarial matrix."""
import csv
import gzip
import io
import json
import tempfile
import unittest
from pathlib import Path
from validation.gse117720_open_rna_reference import (
    METADATA, NEURAL, ERYTHROID, PINNED_MARKERS,
    parse_public_vst, main
)

class Public2018RNATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta=json.loads(METADATA.read_text(encoding="utf8"))

    def fake_matrix(self, mislabeled=False, remove_gene=None):
        samples=self.meta["metadata_rows"]
        out=io.StringIO()
        writer=csv.writer(out,delimiter="\t")
        ids=[r["RNA_library_id"] for r in samples]
        if mislabeled:ids[0]="DOESNOTEXIST"
        writer.writerow(["ensembl_id","gene_symbol"]+ids)
        for i,g in enumerate(PINNED_MARKERS):
            if g==remove_gene:continue
            vals=[]
            for row in samples:
                is_neural=row["cell_type"]!="EPC"
                if g in NEURAL:
                    v=(9 if is_neural else 2)+i/10
                else:
                    v=(2 if is_neural else 9)+i/10
                if row["cell_type"]=="iNSC" and row["passage"] in ("P18","P19","P21"):
                    v+=0.4 if g in NEURAL else -0.2
                vals.append(round(v,3))
            writer.writerow([f"ENSG{i:011d}",g]+vals)
        return out.getvalue()

    def test_all_real_19_public_GEO_samples(self):
        a=self.meta["metadata_rows"]
        self.assertEqual(len(a),19)
        self.assertEqual(len(set(x["GSM"] if "GSM" in x else x["gsm"] for x in a)),19)
        self.assertEqual(len(set(x["RNA_library_id"] for x in a)),19)
        self.assertEqual({x["cell_type"] for x in a},{"smNPC","EPC","iNSC"})
        self.assertEqual({x["donor_pseudonym"] for x in a},{"R_107b","R_82b","MJD33b"})
        self.assertEqual(self.meta["RNA_2018_to_DNAm_2026_donor_identity"],
                         "UNVERIFIED_NO_INDEPENDENT_GENOTYPE_MATCH")

    def test_experimental_RNA_grouping_does_not_invent_six_donors(self):
        data=parse_public_vst(self.fake_matrix(),self.meta)
        self.assertEqual(data["library_count"],19)
        self.assertEqual(data["marker_counts"]["neural"],len(NEURAL))
        self.assertEqual(data["marker_counts"]["erythroid"],len(ERYTHROID))
        self.assertEqual(len(data["paired_EPC_to_iNSC_same_2018_donor"]),2)
        self.assertEqual(len(data["paired_iNSC_early_to_late_same_2018_donor"]),3)
        self.assertGreater(data["by_cell_type"]["iNSC"]["mean_RNA_identity_score"],
                           data["by_cell_type"]["EPC"]["mean_RNA_identity_score"])
        self.assertFalse(data["2018_RNA_expression_matched_to_six_2026_donors"])
        self.assertEqual(data["2026_age_clock_adjusted_with_RNA"],"UNVERIFIED_NOT_IDENTIFIABLE")

    def test_ambiguous_source_sample_header_fails(self):
        with self.assertRaisesRegex(ValueError,"sample-column ambiguity"):
            parse_public_vst(self.fake_matrix(mislabeled=True),self.meta)

    def test_missing_necessary_markers_fails(self):
        txt=self.fake_matrix()
        lines=txt.splitlines()
        lines=[x for x in lines if not any("\t"+g+"\t" in x for g in NEURAL[2:])]
        with self.assertRaisesRegex(ValueError,"insufficient independent"):
            parse_public_vst("\n".join(lines),self.meta)

    def test_real_bytes_not_fabricated_if_missing_file(self):
        with tempfile.TemporaryDirectory() as root:
            outfile=Path(root)/"out.json"
            rc=main(["--local-gzip",str(Path(root)/"absent.gz"),"--out",str(outfile)])
            data=json.loads(outfile.read_text())
            self.assertEqual(rc,1)
            self.assertEqual(data["status"],"PARTIAL_SOURCE_UNAVAILABLE")
            self.assertEqual(data["2026_RNA_ADJUSTED_AGE"],"UNVERIFIED")

    def test_true_gzip_fixture_does_not_masquerade_as_real_2026(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"fixture.gz"
            f.write_bytes(gzip.compress(self.fake_matrix().encode("utf-8")))
            out=Path(root)/"test-result.json"
            self.assertEqual(main(["--local-gzip",str(f),"--out",str(out)]),0)
            data=json.loads(out.read_text())
            self.assertTrue(data["reference_is_different_from_2026_six_donors"])
            self.assertEqual(data["2026_RNA_ADJUSTED_AGE"],"UNVERIFIED")
            self.assertTrue(data["independent_2018_RNA"]["fate_confounded_by_conversion"])

if __name__=="__main__":unittest.main()
