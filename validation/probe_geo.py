#!/usr/bin/env python3
"""GEO acquisition/format probe. Never evaluates or inspects outcome directions."""
import urllib.request, hashlib, gzip, io, csv
from pathlib import Path
BASE='https://ftp.ncbi.nlm.nih.gov/geo/series/'
URLS={
 'GSE113081_Acomys':BASE+'GSE113nnn/GSE113081/suppl/GSE113081_aco_per_se_genes_counts_matrix.txt.gz',
 'GSE113081_Mus':BASE+'GSE113nnn/GSE113081/suppl/GSE113081_mus_per_se_genes_counts_matrix.txt.gz',
 'GSE74387_array':BASE+'GSE74nnn/GSE74387/matrix/GSE74387_series_matrix.txt.gz',
}
ROOT=Path('validation/cache');ROOT.mkdir(parents=True,exist_ok=True)
for key,url in URLS.items():
    path=ROOT/(key+'.gz')
    print('FETCH',key,url,flush=True)
    try:
        if not path.exists():
            req=urllib.request.Request(url,headers={'User-Agent':'BIO-MIMIC-X GEO validation academic research contact data GEOquery'})
            with urllib.request.urlopen(req,timeout=40) as r:
                path.write_bytes(r.read(40000000))
        raw=path.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        print('FILE',key,'bytes',len(raw),'SHA256',digest,flush=True)
        with gzip.open(path,'rt',encoding='utf-8',errors='replace') as f:
            shown=0;sampletitles=0;rows=0
            for line in f:
                if line.startswith('!Sample_title') or line.startswith('!Sample_geo_accession'):
                    print('SAMPLE_METADATA',line[:240].strip(),flush=True)
                    sampletitles+=1
                if not line.startswith('!') and not line.startswith('^') and not line.startswith('#'):
                    rows+=1
                    if shown<4:
                        tokens=next(csv.reader([line],delimiter='\t'))
                        print('MATRIX_ROW',key,'ncolumns',len(tokens),'first8',tokens[:8],flush=True);shown+=1
            print('MATRIX_TOTAL',key,'rows',rows,'samplemetadata',sampletitles,flush=True)
    except Exception as e:
        print('DATA_FETCH_FAILED',key,type(e).__name__,str(e),flush=True)
