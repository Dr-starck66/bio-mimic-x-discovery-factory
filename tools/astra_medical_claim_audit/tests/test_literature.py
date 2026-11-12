import copy
import io
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from literature import (pubmed_metadata, verify_reference, audit_with_literature,
                        fetch_official_pubmed_xml, MAX_RESPONSE_BYTES)
ROOT = Path(__file__).parent
XML = (ROOT / "fixtures/pubmed_22911011_SIMULATED.xml").read_bytes()
REF = {"url":"https://pubmed.ncbi.nlm.nih.gov/22911011/",
       "title":"Antiretroviral therapy for prevention of tuberculosis in adults with HIV: a systematic review and meta-analysis",
       "locator":"doi:10.1371/journal.pmed.1001270", "stance":"supports"}
CASE = {"case_id":"synthetic-literature-001", "claims":[{"id":"C1", "text":"Published literature metadata may be checked by PMID.", "kind":"other", "references":[REF]}]}

class FakeResponse:
    def __init__(self, buf, url): self.buf = io.BytesIO(buf); self.url=url
    def __enter__(self):return self
    def __exit__(self, *args): pass
    def geturl(self):return self.url
    def read(self,n=-1):return self.buf.read(n)

class LiteratureTests(unittest.TestCase):
    def test_parse_metadata(self):
        x=pubmed_metadata(XML)
        self.assertEqual((x["pmid"],x["doi"],x["abstract_present"]),("22911011","10.1371/journal.pmed.1001270",True))
    def test_fixture_cannot_earn_live_pass(self):
        x=verify_reference(REF, XML, "TEST_FIXTURE")
        self.assertEqual((x["bibliographic_identity"],x["live_retrieval"],x["clinical_validity"]),("PARTIAL","UNVERIFIED","UNVERIFIED"))
    def test_identifier_mismatch(self):
        x=copy.deepcopy(REF); x["url"]="https://pubmed.ncbi.nlm.nih.gov/1/"
        self.assertEqual(verify_reference(x,XML,"TEST_FIXTURE")["bibliographic_identity"],"FAIL")
    def test_doi_mismatch(self):
        x=copy.deepcopy(REF); x["locator"]="doi:10.1000/not_the_paper"
        self.assertEqual(verify_reference(x,XML,"TEST_FIXTURE")["bibliographic_identity"],"FAIL")
    def test_title_mismatch(self):
        x=copy.deepcopy(REF); x["title"]="Fake unrelated trial"
        self.assertEqual(verify_reference(x,XML,"TEST_FIXTURE")["bibliographic_identity"],"FAIL")
    def test_invalid_xml(self):
        self.assertEqual(verify_reference(REF,b"garbage","TEST_FIXTURE")["bibliographic_identity"],"UNVERIFIED")
    def test_offline_bridge_unverified(self):
        x=audit_with_literature(CASE)
        self.assertEqual((x["scientific_validity"],x["external_network_requests"],x["literature_bridge"]["live_retrieval_pass_count"]),("UNVERIFIED",0,0))
    def test_offline_fixture_bridge_unverified(self):
        x=audit_with_literature(CASE,fixture_xml={"22911011":XML})
        self.assertEqual(x["literature_bridge"]["publication_checks"][0]["bibliographic_identity"],"PARTIAL")
        self.assertEqual(x["scientific_validity"],"UNVERIFIED")
    def test_unsafe_direction_still_fails(self):
        p=copy.deepcopy(CASE);p["claims"][0]["text"]="Stop taking your chemotherapy today."
        x=audit_with_literature(p,fixture_xml={"22911011":XML})
        self.assertEqual(x["overall_audit_status"],"FAIL")
    def test_real_response_requires_allowlist(self):
        class Fake:
            def __init__(self, loc):self.loc=loc
            def __call__(self, req, timeout):return FakeResponse(XML,self.loc)
        self.assertEqual(pubmed_metadata(fetch_official_pubmed_xml("22911011",opener=Fake("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi")))["pmid"],"22911011")
        with self.assertRaises(ValueError):fetch_official_pubmed_xml("22911011",opener=Fake("https://evil.example/"))
    def test_live_mocked_not_actual_live(self):
        class Fake:
            def __call__(self,req,timeout):return FakeResponse(XML,"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi")
        x=audit_with_literature(CASE,allow_network=True,opener=Fake())
        self.assertEqual(x["literature_bridge"]["bibliographic_identity_pass_count"],1)
        self.assertEqual(x["scientific_validity"],"UNVERIFIED")
    def test_missing_abstract_partial(self):
        raw=XML.replace(b"<Abstract><AbstractText>",b"<Dummy><AbstractText>").replace(b"</AbstractText></Abstract>",b"</AbstractText></Dummy>")
        self.assertEqual(verify_reference(REF,raw,"TEST_FIXTURE")["abstract_present"],"PARTIAL")
    def test_reject_oversized_input(self):
        with self.assertRaises(ValueError):pubmed_metadata(b"X"*(MAX_RESPONSE_BYTES+1))
    def test_other_url_no_network(self):
        p=copy.deepcopy(CASE);p["claims"][0]["references"][0]["url"]="https://www.who.int/news"
        x=audit_with_literature(p,allow_network=True)
        self.assertEqual(x["literature_bridge"]["publication_checks"][0]["live_retrieval"],"UNVERIFIED")
if __name__=="__main__":unittest.main()

