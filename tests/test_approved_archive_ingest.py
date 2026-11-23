import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'validation'))
from approved_archive_ingest import approved_url, ingest, inspect_zip, sha256


class TestArchiveImport(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.d = Path(self.folder.name)
        self.z = self.d / 'source-original.zip'
        self.dest = self.d / 'out'
        self.make_zip('probe.tsv', 'id\tsequence\nX\tACGT\n')

    def tearDown(self):
        self.folder.cleanup()

    def make_zip(self, name, body):
        with zipfile.ZipFile(self.z, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(name, body)

    def test_valid_local_archive_provenance(self):
        report = ingest(path=self.z, url=None, output=self.dest,
                        expected_sha256=sha256(self.z), expected_size=self.z.stat().st_size)
        self.assertEqual(report['status'], 'PASS_ARCHIVE_INGEST')
        self.assertEqual(report['zip_members'], 1)
        self.assertFalse(report['gmail_connector_permission_changed'])
        self.assertFalse(report['automatic_future_download_enabled'])
        self.assertTrue((self.dest / 'source_manifest.json').exists())

    def test_hash_mismatch_is_closed(self):
        with self.assertRaisesRegex(ValueError, 'sha256_mismatch'):
            ingest(path=self.z, url=None, output=self.dest, expected_sha256='0' * 64)
        self.assertFalse((self.dest / 'source.zip').exists())

    def test_size_mismatch_is_closed(self):
        with self.assertRaisesRegex(ValueError, 'size_mismatch'):
            ingest(path=self.z, url=None, output=self.dest, expected_size=19701321)

    def test_traversal_is_rejected(self):
        self.make_zip('../steal.tsv', 'bad')
        with self.assertRaisesRegex(ValueError, 'unsafe_member_path'):
            inspect_zip(self.z)

    def test_windows_traversal_is_rejected(self):
        self.make_zip('..\\steal.tsv', 'bad')
        with self.assertRaisesRegex(ValueError, 'unsafe_member_path'):
            inspect_zip(self.z)

    def test_fake_zip_is_rejected(self):
        self.z.write_text('not zip')
        with self.assertRaisesRegex(ValueError, 'not_a_zip_archive'):
            inspect_zip(self.z)

    def test_https_approved_host(self):
        self.assertEqual(approved_url('https://sec-assets.thermofisher.com/a.zip',
                                      {'sec-assets.thermofisher.com'}),
                         'https://sec-assets.thermofisher.com/a.zip')

    def test_https_unapproved_host_rejected(self):
        with self.assertRaisesRegex(ValueError, 'host_not_approved'):
            approved_url('https://unapproved.example.com/a.zip', {'sec-assets.thermofisher.com'})

    def test_http_and_userinfo_rejected(self):
        for url in ['http://sec-assets.thermofisher.com/a.zip',
                    'https://user:pass@sec-assets.thermofisher.com/a.zip']:
            with self.assertRaisesRegex(ValueError, 'https_host_only'):
                approved_url(url, {'sec-assets.thermofisher.com'})

    def test_suspicious_ratio_rejected(self):
        self.make_zip('danger.txt', 'A' * 1000000)
        with self.assertRaisesRegex(ValueError, 'suspicious_compression_ratio'):
            inspect_zip(self.z)

    def test_source_cannot_be_replaced_different_hash(self):
        ingest(path=self.z, url=None, output=self.dest)
        self.make_zip('another.tsv', 'new')
        with self.assertRaisesRegex(FileExistsError, 'different_sha256'):
            ingest(path=self.z, url=None, output=self.dest)

    def test_official_20261123_thermo_url_is_approved(self):
        # Source supplied by the vendor scientist, not guessed from filename.
        url = ('https://www.thermofisher.com/store/v3/products/sec/assets?url='
               'TFS-Assets/LSG/Support-Files/MoGene-2_0-st-v1-mm10-probe-tab.zip')
        self.assertEqual(approved_url(url, {'www.thermofisher.com'}), url)

    def test_vendor_url_to_existing_converter_offline_integration(self):
        # A mocked download: proves wiring ONLY, not remote archive retrieval.
        import shutil
        url = ('https://www.thermofisher.com/store/v3/products/sec/assets?url='
               'TFS-Assets/LSG/Support-Files/MoGene-2_0-st-v1-mm10-probe-tab.zip')
        probe = 'ACGTACGTACGTACGTACGTACGTA'
        self.make_zip('MoGene-2_0-st-v1-mm10-probe-tab.txt',
                      'Probe Set Name\\tProbe X\\tProbe Y\\tProbe Interrogation Position\\t'
                      'Probe Sequence\\tTarget Strandedness\\n'
                      f'17200001\\t1\\t2\\t13\\t{probe}\\tsense\\n')
        def copy_only(request_url, target, approved_hosts):
            self.assertEqual(approved_url(request_url, approved_hosts), url)
            shutil.copyfile(self.z, target)
        with patch('approved_archive_ingest.download', side_effect=copy_only):
            result = ingest(path=None, url=url, output=self.dest,
                            expected_size=self.z.stat().st_size, convert_probes=True)
        self.assertEqual(result['status'], 'PASS_ARCHIVE_INGEST')
        self.assertEqual(result['probe_conversion']['probe_rows'], 1)
        self.assertFalse(result['probe_conversion']['gene_annotation_complete'])
        self.assertFalse(result['probe_conversion']['cross_species_probe_alignment_executed'])

    def test_both_sources_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly_one_source_required'):
            ingest(path=self.z, url='https://sec-assets.thermofisher.com/a.zip', output=self.dest)


if __name__ == '__main__':
    unittest.main()
