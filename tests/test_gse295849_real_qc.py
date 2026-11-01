"""Synthetic fixtures only. They do NOT demonstrate real epigenetic rejuvenation."""
import gzip
import tempfile
import unittest
from pathlib import Path
from validation.gse295849_real_qc import audit_local

class GSE295849PublicBetaQCTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.p = Path(self.t.name) / "synthetic.gz"

    def fixture(self, body):
        with gzip.open(self.p, "wt") as fh:
            fh.write(body)

    def test_numeric_and_gzip_fully_valid(self):
        self.fixture("CpG\tdonorA\tdonorB\n" +
                     "".join(f"cg{i:06}\t0.25\t0.75\n" for i in range(100)))
        r = audit_local(self.p, "synthetic-fixture", min_bytes=30)
        self.assertEqual(r["rows"], 100)
        self.assertEqual(r["columns"], 2)
        self.assertEqual([v["mean_beta"] for v in r["column_summary"]], [0.25, 0.75])
        self.assertEqual(r["methylation_clock_reproduction"], "UNVERIFIED")

    def test_truncated_gzip_never_passes(self):
        self.fixture("CpG\tA\tB\n" +
                     "".join(f"cg{i}\t0.2\t0.3\n" for i in range(100)))
        self.p.write_bytes(self.p.read_bytes()[:-5])
        with self.assertRaises((EOFError, OSError)):
            audit_local(self.p, "synthetic-fixture", min_bytes=30)

    def test_out_of_range_beta_is_rejected(self):
        self.fixture("CpG\tA\tB\n" +
                     "".join(f"cg{i}\t1.4\t0.2\n" for i in range(100)))
        with self.assertRaisesRegex(ValueError, "invalid beta"):
            audit_local(self.p, "synthetic-fixture", min_bytes=30)

    def test_column_mismatch_is_rejected(self):
        self.fixture("CpG\tA\tB\n" +
                     "".join(f"cg{i}\t0.2\n" for i in range(100)))
        with self.assertRaisesRegex(ValueError, "row width"):
            audit_local(self.p, "synthetic-fixture", min_bytes=30)

    def test_real_author_header_without_probe_label(self):
        # Column-only header was observed in the authentic GSE295849 matrix.
        self.fixture("204027260051_R01C01\t204027260051_R02C01\n" +
                     "".join(f"cg{i:08}\t0.25\t0.75\n" for i in range(100)))
        r = audit_local(self.p, "synthetic-real-format", min_bytes=30)
        self.assertEqual(r["rows"], 100)
        self.assertEqual(r["columns"], 2)
        self.assertEqual([v["mean_beta"] for v in r["column_summary"]], [0.25, 0.75])

    def test_wrong_hash_is_rejected(self):
        self.fixture("CpG\tA\tB\n" +
                     "".join(f"cg{i}\t0.2\t0.3\n" for i in range(100)))
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            audit_local(self.p, "synthetic-fixture", expected_sha256="0"*64, min_bytes=30)

if __name__=="__main__":
    unittest.main()
