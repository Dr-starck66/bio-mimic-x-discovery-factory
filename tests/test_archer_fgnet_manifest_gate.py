import unittest,io,zipfile,hashlib
from validation.archer_fgnet_manifest_gate import parse_points,census
def make_zip(files):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        for k,v in files.items():z.writestr(k,v)
    return b.getvalue()
class ManifestGateTests(unittest.TestCase):
    def test_parse_standard_pts(self):
        s=b"version: 1\nn_points: 68\n{\n"+b"12.5 17.5\n"*68+b"}\n"
        self.assertEqual(len(parse_points(s)),68)
    def test_reject_nonfinite(self):
        with self.assertRaisesRegex(ValueError,"Invalid coordinate"):parse_points(b"nan 2\n")
    def test_reject_altered_zip_md5(self):
        with self.assertRaisesRegex(ValueError,"MD5 mismatch"):
            census(make_zip({"FGNET/images/001A03.jpg":b"fake"}))
    def test_minimum_25_prespecified(self):
        pts=b"version: 1\nn_points: 68\n{\n"+b"12.5 17.5\n"*68+b"}\n"
        raw=make_zip({"FGNET/images/001A03.jpg":b"fake","FGNET/points/001A03.pts":pts})
        r=census(raw,expected_md5=hashlib.md5(raw).hexdigest())
        self.assertEqual(r["status"],"FAIL_CLOSED_INSUFFICIENT_ANNOTATED_IDENTITIES")
    def test_zip_path_traversal_rejected(self):
        raw=make_zip({"../001A03.jpg":b"fake"})
        with self.assertRaisesRegex(ValueError,"Unsafe ZIP member"):
            census(raw,expected_md5=hashlib.md5(raw).hexdigest())
if __name__=="__main__":unittest.main()
