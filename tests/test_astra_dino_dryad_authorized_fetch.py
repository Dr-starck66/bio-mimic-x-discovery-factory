import hashlib, os, tempfile, unittest
from pathlib import Path
import urllib.request
from astra_dino_dryad_authorized_fetch import verify,download_one,ProtectedRedirect,AuthorizationError,IntegrityError

class TestFetch(unittest.TestCase):
    def test_verify_exact_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'one.txt';p.write_bytes(b'abc')
            self.assertEqual(verify(p,3,hashlib.sha256(b'abc').hexdigest())['status'],'PASS')
    def test_wrong_hash_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'one.txt';p.write_bytes(b'abc')
            with self.assertRaises(IntegrityError):verify(p,3,'0'*64)
    def test_wrong_size_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'one.txt';p.write_bytes(b'abc')
            with self.assertRaises(IntegrityError):verify(p,4,hashlib.sha256(b'abc').hexdigest())
    def test_empty_token_blocked_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(AuthorizationError): download_one('one.txt',1,3,'0'*64,d,'')
    def test_existing_valid_file_reused(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'one.txt').write_bytes(b'abc')
            got=download_one('one.txt',1,3,hashlib.sha256(b'abc').hexdigest(),d,'valid-nonempty')
            self.assertEqual(got['source'],'EXISTING_LOCAL_ORIGINAL')
    def test_redirect_strips_authorization(self):
        handler=ProtectedRedirect();req=urllib.request.Request('https://datadryad.org/api/v2/files/1/download',headers={'Authorization':'Bearer SECRET'})
        new=handler.redirect_request(req,None,302,'moved',{},'https://objects.example.org/data')
        self.assertFalse(any(k.lower()=='authorization' for k in new.headers))
    def test_same_origin_redirect_keeps_authorization(self):
        handler=ProtectedRedirect();req=urllib.request.Request('https://datadryad.org/api/v2/files/1/download',headers={'Authorization':'Bearer SECRET'})
        new=handler.redirect_request(req,None,302,'moved',{},'https://datadryad.org/api/v2/files/1/direct')
        self.assertTrue(any(k.lower()=='authorization' for k in new.headers))
    def test_http_redirect_blocked(self):
        handler=ProtectedRedirect();req=urllib.request.Request('https://datadryad.org/api/v2/files/1/download',headers={'Authorization':'Bearer SECRET'})
        with self.assertRaises(AuthorizationError):handler.redirect_request(req,None,302,'moved',{},'http://example.org/data')
    def test_fake_remote_success_sha(self):
        class Response:
            status=200
            def __init__(self):self.items=[b'abc',b'']
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,size):return self.items.pop(0)
        class Opener:
            def open(self,*args,**kwargs):return Response()
        with tempfile.TemporaryDirectory() as d:
            out=download_one('one.txt',1,3,hashlib.sha256(b'abc').hexdigest(),d,'SYNTHETIC',opener=Opener())
            self.assertEqual(out['status'],'PASS')
            self.assertEqual((Path(d)/'one.txt').read_bytes(),b'abc')
    def test_fake_remote_corrupt_rejected(self):
        class Response:
            status=200
            def __init__(self):self.items=[b'bad',b'']
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,size):return self.items.pop(0)
        class Opener:
            def open(self,*args,**kwargs):return Response()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(IntegrityError):
                download_one('one.txt',1,3,hashlib.sha256(b'abc').hexdigest(),d,'SYNTHETIC',opener=Opener())
            self.assertFalse((Path(d)/'one.txt').exists())
            self.assertFalse((Path(d)/'one.txt.part').exists())

if __name__=='__main__': unittest.main()
