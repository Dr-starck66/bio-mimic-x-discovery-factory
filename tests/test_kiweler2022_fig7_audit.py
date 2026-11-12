"""Negative-control-first tests for Kiweler Fig 7 research audit."""
import importlib.util, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
class Figure7Audit(unittest.TestCase):
    def test_bound_scenarios(self):
        m=load("analysis","validation/kiweler2022_fig7_reanalysis.py")
        rows=m.published_binary_bounds()
        self.assertEqual([r["kd_without_macrometastases"] for r in rows],[5,6,7,8,9])
        self.assertAlmostEqual(rows[0]["fisher_two_sided_p"],0.02941176470588235)
        self.assertTrue(all(0<=r["fisher_two_sided_p"]<=.02941177 for r in rows))
    def test_negative_primary_tumor_weight(self):
        m=load("analysis","validation/kiweler2022_fig7_reanalysis.py")
        self.assertEqual(m.PANELS["7c"]["p"],0.9474)
        self.assertEqual(m.PANELS["7g"]["n"],{"SCR":7,"MTHFD1L_KD":9})
    def test_reject_incomplete_animal_mapping(self):
        m=load("analysis","validation/kiweler2022_fig7_reanalysis.py")
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"animals.csv";file.write_text("panel,group,mouse_id,value\n7e,SCR,id1,1\n")
            with self.assertRaises(ValueError):m.read_animal_csv(file)
    def test_explicit_xlsx_link_only(self):
        m=load("download","validation/kiweler2022_source_fetch.py")
        html='<a href="https://static-content.springer.com/path/source.xlsx">Source Data</a>'
        self.assertEqual(m.from_html(html),["https://static-content.springer.com/path/source.xlsx"])
    def test_no_moesm_guess(self):
        m=load("download","validation/kiweler2022_source_fetch.py")
        self.assertEqual(m.from_html("<h1>Source Data XLSX</h1>"),[])
    def test_reject_unknown_host(self):
        m=load("download","validation/kiweler2022_source_fetch.py")
        with self.assertRaises(ValueError):m.guard("https://other.example.com/source.xlsx")
    def test_explicit_pmc_xml_href(self):
        m=load("download","validation/kiweler2022_source_fetch.py")
        xml='<article xmlns:xlink="http://www.w3.org/1999/xlink"><supplementary-material><media xlink:href="file.xlsx" /></supplementary-material></article>'
        self.assertEqual(m.from_xml(xml),["https://pmc.ncbi.nlm.nih.gov/articles/PMC9110368/bin/file.xlsx"])
if __name__=="__main__":unittest.main()
