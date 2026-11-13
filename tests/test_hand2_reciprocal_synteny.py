import gzip,io,unittest\nfrom unittest.mock import patch\nfrom urllib.error import HTTPError
from validation.hand2_reciprocal_synteny import (
    parse_old_chr6q,find_flanking_candidates,compare_reciprocal,verified_modern_anchors,CHROM,
)
def fixture():
    rows=[
      'chr3q\tx\tgene\t1\t100\t.\t+\t.\tgene_id "wrong"; gene_name "HAND1 [nr]|HAND2 [hs]";',
      'chr6q\tx\tgene\t100\t400\t.\t+\t.\tgene_id "sap"; gene_name "SAP30 [nr]";',
      'chr6q\tx\tgene\t600\t4800\t.\t-\t.\tgene_id "unknown"; gene_name "uncharacterized";',
      'chr6q\tx\tgene\t5000\t5500\t.\t+\t.\tgene_id "fbxo"; gene_name "FBXO8 [hs]";',
      'chr6q\tx\ttranscript\t600\t4800\t.\t-\t.\tgene_id "bad"; gene_name "HAND2 [hs]";'
    ]
    b=io.BytesIO()
    with gzip.GzipFile(fileobj=b,mode="wb",mtime=0) as f:f.write(("\n".join(rows)+"\n").encode())
    return b.getvalue()

class Hand2ReciprocalSyntenyTests(unittest.TestCase):
    def setUp(self):
        self.genes=parse_old_chr6q(fixture(),verify=False)
        self.modern={"SAP30":{"start":900,"end":950},
                     "FBXO8":{"start":930000000,"end":930000100}}
    def test_ncbi_500_retries_then_fails_closed(self):
        calls=[]
        def unavailable(url,limit):
            calls.append(url)
            raise HTTPError(url,500,"server error",{},None)
        with patch("validation.hand2_reciprocal_synteny.time.sleep"):
            modern,receipts,failures=verified_modern_anchors(unavailable)
        self.assertEqual(modern,{})
        self.assertEqual(receipts,{})
        self.assertEqual(len(calls),24)
        self.assertEqual(failures["SAP30"]["status"],"UNVERIFIED_MODERN_SOURCE")
        self.assertEqual(len(failures["SAP30"]["attempts"]),3)
    def test_nontransient_source_failure_is_not_retried(self):
        calls=[]
        def invalid(url,limit):
            calls.append(url)
            raise ValueError("bad payload")
        with patch("validation.hand2_reciprocal_synteny.time.sleep"):
            modern,receipts,failures=verified_modern_anchors(invalid)
        self.assertEqual(modern,{})
        self.assertEqual(len(calls),8)
        self.assertEqual(len(failures["FBXO8"]["attempts"]),1)
    def test_only_full_gene_rows_on_chr6q(self):
        self.assertEqual([g["gene_id"] for g in self.genes],["sap","unknown","fbxo"])
    def test_bracket_not_same_as_identity(self):
        result=find_flanking_candidates(self.genes,self.modern)
        self.assertEqual(result["status"],"PARTIAL_TWO_SYNTENIC_FLANKS")
        self.assertEqual([g["gene_id"] for g in result["candidates"]],["unknown"])
        self.assertEqual(compare_reciprocal({"status":"UNVERIFIED_NO_FLANKING_ANCHORS"})["whole_genome_unique"],"UNVERIFIED")
    def test_plain_unambiguous_gene_names_are_anchors(self):
        raw=fixture().replace(b"SAP30 [nr]",b"SAP30").replace(b"FBXO8 [hs]",b"FBXO8")
        genes=parse_old_chr6q(raw,verify=False)
        self.assertEqual(find_flanking_candidates(genes,self.modern)["status"],"PARTIAL_TWO_SYNTENIC_FLANKS")
    def test_missing_anchor_blocks_shortlist(self):
        result=find_flanking_candidates(self.genes,{"SAP30":self.modern["SAP30"]})
        self.assertEqual(result["status"],"UNVERIFIED_NO_FLANKING_ANCHORS")
        self.assertEqual(result["candidates"],[])
        self.assertEqual(result["valid_anchor_count"],1)
        self.assertEqual(result["modern_right_anchor_count"],0)
        self.assertEqual(result["anchor_failures"]["flanking_pair"],"MISSING_MODERN_LEFT_OR_RIGHT")
    def test_conflicting_paralog_label_blocks_anchor(self):
        bad=dict(self.genes[0],symbols=["SAP30","SAP30L"])
        result=find_flanking_candidates([bad]+self.genes[1:],self.modern)
        self.assertEqual(result["status"],"UNVERIFIED_NO_FLANKING_ANCHORS")
        self.assertIn("SAP30",result["anchor_failures"])
    def test_duplicate_anchor_blocks_shortlist(self):
        bad=dict(self.genes[0],gene_id="another_sap")
        result=find_flanking_candidates(self.genes+[bad],self.modern)
        self.assertEqual(result["status"],"UNVERIFIED_NO_FLANKING_ANCHORS")

if __name__=="__main__":unittest.main()
