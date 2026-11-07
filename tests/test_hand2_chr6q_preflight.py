import gzip
import hashlib
import io
import unittest
from unittest.mock import patch
from validation.hand2_chr6q_preflight import (
    scan_gene_features, _verified_source, fetch_pinned_gtf,
)

def gtf(*rows):
    data = "##gtf-version 2.2\n" + "\n".join(rows) + "\n"
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as out:
        out.write(data.encode())
    return buf.getvalue()

def gene(chrom, start, end, ident, name):
    return f'{chrom}\tAmexT_v47\tgene\t{start}\t{end}\t.\t+\t.\tgene_id "{ident}"; gene_name "{name}";'

class Hand2Chr6qTests(unittest.TestCase):
    def test_chr6q_hand2_text_label_only_candidate(self):
        raw = gtf(gene("chr3q",100,200,"A","HAND1 [nr]|HAND2 [hs]"),gene("chr6q",5,30,"B","HAND2 [nr]"))
        r = scan_gene_features(raw,hashlib.sha256(raw).hexdigest())
        self.assertEqual(r["status"],"PARTIAL_CHR6Q_LABEL_SCAN")
        self.assertEqual(r["historic_hand2_identity"],"UNVERIFIED")
        self.assertEqual(r["chr6q_hand2_labeled_candidates"][0]["gene_id"],"B")
        self.assertEqual(len(r["mixed_hand1_hand2_labeled_features"]),1)

    def test_no_6q_label_does_not_imply_gene_absence(self):
        raw=gtf(gene("chr3q",100,200,"AMEX60DD030069","HAND1 [nr]|HAND2 [hs]"),gene("chr6q",12,40,"X","uncharacterized"))
        r=scan_gene_features(raw,hashlib.sha256(raw).hexdigest())
        self.assertEqual(r["status"],"PARTIAL_NO_CHR6Q_HAND2_LABEL")
        self.assertEqual(r["chr6q_gene_feature_count"],1)
        self.assertIn("does NOT",r["warning"])

    def test_not_substring_or_transcript(self):
        raw=gtf(gene("chr6q",1,4,"X","SHAND2LIKE"),'chr6q\tAmexT\ttranscript\t5\t9\t.\t+\t.\tgene_id "Y"; gene_name "HAND2 [hs]";')
        self.assertEqual(scan_gene_features(raw,hashlib.sha256(raw).hexdigest())["historical_hand_labeled_gene_features"],[])

    def test_modified_or_corrupt_source_rejected(self):
        raw=gtf(gene("chr6q",1,5,"X","HAND2 [nr]"))
        with self.assertRaises(ValueError):scan_gene_features(raw,"0"*64)
        with self.assertRaises(ValueError):_verified_source(raw)
        with self.assertRaises(ValueError):scan_gene_features(b"not-gzip",None)

    def test_fallback_only_uses_exact_same_checksum(self):
        raw=gtf(gene("chr6q",1,5,"X","HAND2 [nr]"))
        class Stream:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,n):return raw
        with patch("validation.hand2_chr6q_preflight.urllib.request.urlopen",side_effect=[OSError("primary down"),Stream()]),patch("validation.hand2_chr6q_preflight.GTF_SHA256",hashlib.sha256(raw).hexdigest()),patch("validation.hand2_chr6q_preflight.ZENODO_MD5",hashlib.md5(raw).hexdigest()):
            body,receipt=fetch_pinned_gtf()
        self.assertEqual(body,raw)
        self.assertIn("zenodo.org",receipt["url"])
        self.assertEqual(len(receipt["source_failures"]),1)

if __name__=="__main__":
    unittest.main()
