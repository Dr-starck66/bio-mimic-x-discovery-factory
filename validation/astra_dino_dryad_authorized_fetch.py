#!/usr/bin/env python3
"""ASTRA DINO Ω: download only public Dryad original files with a user-authorized
API bearer token, then fail closed against official SHA-256 and byte lengths.
No token persisted, printed, or exposed in any URL. Zero external dependencies.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

DOI = '10.5061/dryad.3ffbg79w8'
FILES = (
    ('Morphometrics.txt',4416574,5295,'4722f565feeda8290d3985b4a65d9e0c4e91690270264cfc931d26f24cc51555'),
    ('pPCAeigen.txt',4416577,6421,'d615bd8dd3fd22091b971b20f18a49832d1f2afaf390a30ea3465f6a276b5bff'),
    ('Prun64_3miss2mafNoZ_1.vcf.gz',4416598,59719262,'471db73a5eb65a8bb6af8f25872a5a2d0bc0115556203250f69eb61988163d34'),
)
BASE='https://datadryad.org/api/v2/files/'

class AuthorizationError(Exception): pass
class IntegrityError(Exception): pass

class ProtectedRedirect(urllib.request.HTTPRedirectHandler):
    """Do not forward bearer headers to a different HTTPS origin."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old=urllib.parse.urlsplit(req.full_url)
        new=urllib.parse.urlsplit(newurl)
        if new.scheme!='https':
            raise AuthorizationError('UNSAFE_REDIRECT_BLOCKED')
        request=super().redirect_request(req,fp,code,msg,headers,newurl)
        if request is None: return None
        if (old.hostname,old.port)!=(new.hostname,new.port):
            for k in list(request.headers):
                if k.lower() in ('authorization','proxy-authorization','cookie'):
                    del request.headers[k]
            for k in list(request.unredirected_hdrs):
                if k.lower() in ('authorization','proxy-authorization','cookie'):
                    del request.unredirected_hdrs[k]
        return request


def verify(path:Path,size:int,expected:str):
    if path.stat().st_size!=size: raise IntegrityError('FILE_SIZE_MISMATCH:'+path.name)
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    if h.hexdigest().lower()!=expected.lower():
        raise IntegrityError('SHA256_MISMATCH:'+path.name)
    return {'file':path.name,'bytes':size,'sha256':expected,'status':'PASS'}


def download_one(name,fid,size,sha,directory,token,opener=None):
    if not token or not token.strip() or '\n' in token or '\r' in token:
        raise AuthorizationError('DRYAD_API_TOKEN_REQUIRED')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    out=directory/name;part=directory/(name+'.part')
    if out.exists(): return {**verify(out,size,sha),'source':'EXISTING_LOCAL_ORIGINAL'}
    part.unlink(missing_ok=True)
    request=urllib.request.Request(BASE+str(fid)+'/download',headers={
        'Authorization':'Bearer '+token,'Accept':'application/octet-stream',
        'User-Agent':'ASTRA-DINO-OMEGA-data-integrity/1.0'
    })
    opener=opener or urllib.request.build_opener(ProtectedRedirect())
    h=hashlib.sha256();total=0
    try:
        with opener.open(request,timeout=60) as response,part.open('wb') as stream:
            if response.status!=200: raise AuthorizationError('DOWNLOAD_NOT_200:'+str(response.status))
            while True:
                chunk=response.read(1024*1024)
                if not chunk: break
                total+=len(chunk)
                if total>size: raise IntegrityError('TOO_MANY_BYTES:'+name)
                stream.write(chunk);h.update(chunk)
        if total!=size: raise IntegrityError('FILE_SIZE_MISMATCH:'+name)
        if h.hexdigest()!=sha: raise IntegrityError('SHA256_MISMATCH:'+name)
        part.replace(out)
        return {'file':name,'bytes':total,'sha256':sha,'status':'PASS','source':'AUTHORIZED_DRYAD_API'}
    except urllib.error.HTTPError as e:
        if e.code in (401,403): raise AuthorizationError('DRYAD_API_ACCESS_DENIED_'+str(e.code)) from None
        raise AuthorizationError('DRYAD_HTTP_'+str(e.code)) from None
    except urllib.error.URLError:
        raise AuthorizationError('NETWORK_UNAVAILABLE') from None
    finally:
        part.unlink(missing_ok=True)


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='dryad_originals',help='directory for verified originals')
    ap.add_argument('--verify-only',action='store_true',help='verify local files without a token')
    args=ap.parse_args(argv)
    results=[]
    try:
        for row in FILES:
            name,fid,size,sha=row
            if args.verify_only: results.append(verify(Path(args.out)/name,size,sha))
            else: results.append(download_one(*row,args.out,os.environ.get('DRYAD_TOKEN','')))
        print(json.dumps({'status':'PASS','dataset_doi':DOI,'verified':results},indent=2))
        return 0
    except (AuthorizationError,IntegrityError,OSError) as exc:
        print(json.dumps({'status':'FAIL_CLOSED','reason':str(exc),'verified_before_failure':results}))
        return 2
if __name__=='__main__':sys.exit(main())
