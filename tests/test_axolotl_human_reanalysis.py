import gzip
import unittest

from validation.axolotl_human_reanalysis import parse_gtf, read_axolotl, read_human, orthology_check


class RealDataParserSafetyTests(unittest.TestCase):
    """Synthetic minimal parser fixtures only; NEVER scientific evidence."""

    def test_gtf_requires_unique_human_tag(self):
        raw=(
            'chr1\tsrc\tgene\t1\t2\t.\t+\t.\tgene_id "AMEX60DD000123"; gene_name "HAND2 [hs]";\n'
            'chr1\tsrc\tgene\t3\t4\t.\t+\t.\tgene_id "AMEX60DD000124"; gene_name "SHH [hs]|HAND2 [hs]";\n'
        )
        self.assertEqual(parse_gtf(gzip.compress(raw.encode())),{"HAND2":["AMEX60DD000123"]})

    def test_axolotl_requires_four_replicates_each(self):
        groups=[f"AnteriorBlastemaHI_Rep{i}" for i in range(1,5)]+[f"PosteriorBlastemaHI_Rep{i}" for i in range(1,5)]
        inp=","+",".join(groups)+"\n"
        inp+="AMEX60DD000123,"+",".join(["100"]*4+["200"]*4)+"\n"
        inp+="AMEX60DD000124,"+",".join(["100"]*8)+"\n"
        x=read_axolotl(gzip.compress(inp.encode()),{"HAND2":["AMEX60DD000123"]})
        self.assertEqual(x["samples"],8)
        self.assertGreater(x["genes"]["HAND2"]["log2_cpm_posterior_minus_anterior"],0)

    def test_human_paired_differences_only(self):
        gsms=[f"GSM{i}" for i in range(6)]
        titles=[f"Patient {i}, {phase}" for i in range(1,4)
                for phase in ("intact skin sample","3rd post-operative day sample")]
        matrix=[
            "!Sample_title\t"+"\t".join(f'"{t}"' for t in titles),
            "!Sample_geo_accession\t"+"\t".join(f'"{g}"' for g in gsms),
            "!series_matrix_table_begin",
            '"ID_REF"\t'+"\t".join(f'"{g}"' for g in gsms),
            '"probe_a"\t'+"\t".join(map(str,[2,4,3,5,4,6])),
            "!series_matrix_table_end"
        ]
        r=read_human(gzip.compress(("\n".join(matrix)+"\n").encode()),{"HAND2":{"probe_a"}})
        self.assertEqual(r["paired_patients"],3)
        self.assertEqual(r["genes"]["HAND2"]["log2_array_day3_minus_intact"],2)

    def test_unknown_orthologs_fail_closed_without_query(self):
        result=orthology_check({})
        self.assertEqual(result["HAND2"]["status"],"UNVERIFIED_GTF_AMBIGUITY")


if __name__=="__main__":
    unittest.main()
