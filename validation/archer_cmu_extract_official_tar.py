"""Extract just the authenticated quarter-resolution TAR from the ORIGINAL UCI ZIP.

This helper does not alter GitHub or deploy any site. The TAR remains local;
its contents (photographs) must not be committed or republished.
"""
import argparse, hashlib, io, zipfile
from pathlib import Path
from validation.archer_vision_real_cmu import DATASET_SHA256
from validation.archer_cmu_mirror_audit import MIRROR_SHA256


def extract_local(zip_path:Path, dest:Path)->dict:
    src=zip_path.read_bytes()
    official=hashlib.sha256(src).hexdigest()
    if official!=DATASET_SHA256:
        raise ValueError(f'Official UCI SHA-256 mismatch: {official}')
    with zipfile.ZipFile(io.BytesIO(src)) as z:
        found=[x for x in z.infolist() if x.filename.split('/')[-1]=='faces_4.tar.gz']
        if len(found)!=1 or found[0].file_size>3_000_000:
            raise ValueError('Expected exactly one bounded TAR inside ZIP')
        b=z.read(found[0])
    sha=hashlib.sha256(b).hexdigest()
    if sha!=MIRROR_SHA256:
        raise ValueError(f'Nested TAR SHA-256 mismatch: {sha}')
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(b)
    return {'status':'PASS_OFFICIAL_ZIP_AND_NESTED_TAR','official_sha256':official,
            'nested_tar_sha256':sha,'nested_tar_bytes':len(b),'local_path':str(dest)}

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--official-zip',type=Path,required=True)
    a.add_argument('--out',type=Path,default=Path('data/CMU_FACES4_GITHUB_MIRROR.tar.gz'))
    x=a.parse_args()
    print(extract_local(x.official_zip,x.out))
