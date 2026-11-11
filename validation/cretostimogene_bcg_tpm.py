#!/usr/bin/env python3
"""BIO-MIMIC X | GSE244895 paired BCG RNA TPM analysis (NOT cretostimogene efficacy).

No artificial observations are ever included in a real-data report. The GEO source
may be downloaded on a machine with authorized network access, or supplied via
--input; never uploads any patient-level data.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np

GSE = 'GSE244895'
FILENAME = 'GSE244895_Bladder_BCG_STAR_RSEM_TPM_raw_.txt.gz'
URLS = (
    f'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE244nnn/{GSE}/suppl/{FILENAME}',
    f'https://www.ncbi.nlm.nih.gov/geo/download/?acc={GSE}&format=file&file={FILENAME}',
)
# Names of samples from GEO GSE244895 (GSM7831849--GSM7831883) in accession order.
GEO_SAMPLE_TITLES = (
    'P-6','P-8','P-3','P-7','P-1','P-5','P-9','P-13','P-2','P-4','P-14','P-10','P-12',
    'P-6_1','P-6_2','P-6_3','P-6_4','P-8_1','P-8_2','P-3_1','P-7_1','P-7_2',
    'P-1_1','P-1_2','P-5_1','P-11_1','P-11_2','P-9_1','P-13_1','P-2_1','P-2_2',
    'P-4_1','P-4_2','P-10_1','P-12_1',
)
GEO_GSM_LABELS = dict(zip((f'GSM{k}' for k in range(7831849, 7831884)),GEO_SAMPLE_TITLES))
PREDECLARED_MARKERS = (
    'CXADR', 'RB1', 'E2F1', 'CD8A', 'CD8B', 'CD68', 'CD163', 'FOXP3',
    'IFNG', 'STAT1', 'CXCL9', 'CXCL10', 'IL17A', 'IL21', 'IL26', 'PDCD1',
    'CTLA4', 'HAVCR2', 'LAG3', 'MKI67', 'HLA-A', 'HLA-B',
)
SEED = 20261108
MAX_COMPRESSED = 20_000_000
# Exact public compressed artifact audited on 2026-11-11. Its last data row is
# incomplete at source; permit quarantine ONLY for this fingerprint and row.
PINNED_GEO_SHA256 = '712480491eb29d56e645650893692f9db2fa3e7ebc30bb41c08e5f9ccc30bac8'


def fetch_source(path: Path) -> tuple[str,str]:
    if path.exists():
        return 'existing_local',path.as_posix()
    errors=[]
    for u in URLS:
        try:
            req=urllib.request.Request(u,headers={'User-Agent':'BIO-MIMIC-X/1.0 academic research, read-only GEO accession'})
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read(MAX_COMPRESSED+1)
            if len(raw)>MAX_COMPRESSED or not raw.startswith(b'\x1f\x8b'):
                raise ValueError('not a valid bounded gzip payload')
            gzip.decompress(raw)
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(raw)
            return 'downloaded',u
        except Exception as e:
            errors.append(f'{type(e).__name__}: {str(e)[:175]}')
    raise RuntimeError('GEO_DOWNLOAD_BLOCKED; '+json.dumps(errors))


def sample_metadata_audit():
    groups=defaultdict(lambda:{'pre':0,'post':0})
    for label in GEO_SAMPLE_TITLES:
        p,pre=parse_sample_label(label)
        groups[p]['pre' if pre else 'post']+=1
    return {'status':'PASS_METADATA_ONLY','accession':GSE,'source':'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE244895',
            'source_note':'sample titles transcribed from publicly indexed GEO record; not downloaded from GEO in this run',
            'n_specimens':len(GEO_SAMPLE_TITLES),
            'n_patients':len(groups),'n_pre':sum(x['pre'] for x in groups.values()),
            'n_post':sum(x['post'] for x in groups.values()),
            'n_paired_patients':sum(bool(x['pre'] and x['post']) for x in groups.values()),
            'unpaired_ids':[p for p,x in groups.items() if not(x['pre'] and x['post'])],
            'patient_counts':dict(sorted(groups.items(),key=lambda z:int(z[0].split('-')[1]))),
            'clinical_response_annotation':'UNVERIFIED','expression_matrix':'NOT_ACQUIRED'}

def parse_sample_label(s: str) -> tuple[str,bool]:
    s=s.strip().strip('"\'')
    s=GEO_GSM_LABELS.get(s,s)
    # Accept standard GEO identifiers P-6 or P-6_1, allow optional suffix .bam-like.
    m=re.search(r'(P-\d{1,3})(?:_(\d+))?(?=$|\b|\.)',s,re.I)
    if not m: raise ValueError('Unrecognized GEO sample label: '+repr(s))
    return m.group(1).upper(),m.group(2) is None


def header_to_labels(headers: list[str]) -> list[str]:
    out=[]
    for s in headers:
        s=s.strip()
        if s in GEO_GSM_LABELS:
            out.append(GEO_GSM_LABELS[s])
        else:
            out.append(s)
    return out


def validate_tail_quarantine(bad_rows: list[dict], last_record_line: int, digest: str, expected_columns: int) -> list[dict]:
    """Fail closed except for one independently observed terminal DEFB110 row.

    Never silently discard an analysis marker or an arbitrary malformed record.
    """
    if not bad_rows:
        return []
    if (digest != PINNED_GEO_SHA256 or len(bad_rows) != 1 or
        bad_rows[0].get('gene') != 'DEFB110' or
        bad_rows[0].get('line') != last_record_line or
        bad_rows[0].get('observed_columns') != 7 or
        expected_columns != 36 or
        'DEFB110' in PREDECLARED_MARKERS):
        raise ValueError('GEO_SOURCE_INTEGRITY_GATE: malformed row not in SHA256-pinned terminal exception')
    return bad_rows


def read_tpm(path: Path) -> tuple[list[str], np.ndarray, list[str],dict]:
    raw=path.read_bytes()
    if len(raw)>MAX_COMPRESSED or not raw.startswith(b'\x1f\x8b'):
        raise ValueError('Expected bounded compressed GEO matrix')
    digest=hashlib.sha256(raw).hexdigest()
    names=[]; vals=[]; samples=None;bad_rows=[];last_record_line=0
    with gzip.open(io.BytesIO(raw),'rt',encoding='utf-8-sig',errors='strict',newline='') as f:
        rd=csv.reader(f,delimiter='\t')
        for row in rd:
            line_num=rd.line_num
            if not row or row[0].startswith(('#','!')):continue
            last_record_line=line_num
            if samples is None:
                samples=header_to_labels(row[1:])
                if len(samples)<4 or len(samples)!=len(set(samples)):
                    raise ValueError('Empty or duplicate or insufficient sample headers')
                for s in samples:parse_sample_label(s)
                continue
            if len(row)!=len(samples)+1:
                bad_rows.append({'gene':row[0].strip() if row else '', 'line':line_num, 'observed_columns':len(row)})
                continue
            if not row[0].strip():continue
            try: values=np.array([float(v) for v in row[1:]],dtype=np.float64)
            except ValueError as e:raise ValueError('Non-numeric TPM values') from e
            if not np.isfinite(values).all() or np.any(values<0):raise ValueError('Nonfinite or negative TPM')
            names.append(row[0].strip());vals.append(values)
    quarantined=validate_tail_quarantine(bad_rows,last_record_line,digest,len(samples)+1 if samples is not None else 0)
    if not vals:raise ValueError('No measured genes')
    if len(names)!=len(set(names)):raise ValueError('Duplicate gene identifiers; need annotation mapping before analysis')
    x=np.vstack(vals)
    if samples is None:raise ValueError('No sample labels')
    qc={'matrix_sha256':digest,'compressed_bytes':len(raw),'genes':len(names),'columns':len(samples),'source_accession':GSE,
        'quarantined_source_rows':quarantined,'source_integrity_gate':'PASS_PINNED_TERMINAL_EXCEPTION' if quarantined else 'PASS_ALL_ROWS'}
    return names,x,samples,qc


def patient_deltas(x:np.ndarray, samples:list[str]):
    groups=defaultdict(lambda:{'pre':[],'post':[]})
    for j,s in enumerate(samples):
        pid,pre=parse_sample_label(s)
        groups[pid]['pre' if pre else 'post'].append(j)
    paired=[pid for pid in sorted(groups,key=lambda v:int(v.split('-')[1])) if groups[pid]['pre'] and groups[pid]['post']]
    if len(paired)<3:raise ValueError('Insufficient patient-matched pre/post specimens')
    # Average technical/longitudinal post samples WITHIN patient, not per specimen.
    log=np.log2(1+x)
    delta=np.column_stack([np.mean(log[:,groups[p]['post']],axis=1)-np.mean(log[:,groups[p]['pre']],axis=1) for p in paired])
    return paired,delta,{p:{'pre':len(groups[p]['pre']),'post':len(groups[p]['post'])} for p in groups}


def exact_signflip_p(d:np.ndarray)->float:
    """Exact two-sided sign-flip p-value, pre/post paired; no normality premise.
    Valid under symmetric null and exchangeability of pair signs, not guaranteed
    for every gene.
    """
    d=np.asarray(d,dtype=float)
    if len(d)>16:raise ValueError('Exact enumeration restricted to at most 16 patients')
    observed=abs(float(np.mean(d)));n=len(d); count=0
    for k in range(1<<n):
        signs=1-2*np.fromiter(((k>>j)&1 for j in range(n)),dtype=float,count=n)
        if abs(float(np.mean(d*signs)))+1e-12>=observed:count+=1
    return count/(1<<n)


def bh(pvalues:dict[str,float])->dict[str,float]:
    pairs=sorted(pvalues.items(),key=lambda q:q[1]); n=len(pairs);out={};best=1.
    for ix in range(n-1,-1,-1):
        key,p=pairs[ix];best=min(best,p*n/(ix+1));out[key]=float(best)
    return out


def gene_key(raw:str)->str:
    # Exact HGNC labels or ID|SYMBOL; Ensembl-only rows are retained but not mis-mapped.
    raw=raw.upper()
    return raw.rsplit('|',1)[-1].split('.')[0]


def analyze(names:list[str],x:np.ndarray,samples:list[str],qc:dict,boot:int=2000):
    paired,delta,sample_counts=patient_deltas(x,samples)
    total_specimens=sum(a['pre']+a['post'] for a in sample_counts.values())
    selected={}
    for i,name in enumerate(names):
        tag=gene_key(name)
        if tag in PREDECLARED_MARKERS:
            if tag in selected:raise ValueError('Ambiguous duplicate gene label '+tag)
            selected[tag]=i
    if len(selected)==0: raise ValueError('No predeclared gene labels matched: supply verified Ensembl-to-HGNC map; no gene effects claimed')
    rng=np.random.default_rng(SEED)
    pvalues={};effects={}
    for key,i in selected.items():
        d=delta[i];p=exact_signflip_p(d)
        boots=np.mean(d[rng.integers(0,len(d),size=(boot,len(d)))],axis=1)
        effects[key]={'mean_delta_log2_tpm1':round(float(np.mean(d)),6),
                      'median_delta_log2_tpm1':round(float(np.median(d)),6),
                      'two_sided_exact_signflip_p':round(float(p),8),
                      'bootstrap_95pct_ci':[round(float(t),6) for t in np.quantile(boots,[0.025,0.975])]}
        pvalues[key]=p
    qs=bh(pvalues)
    for key,record in effects.items():record['bh_fdr_within_predeclared_markers']=round(float(qs[key]),8)
    null_rng=np.random.default_rng(SEED+1)
    # Negative control: flip BCG-pair direction per patient, preserving within-pair dependency.
    negative_signs=null_rng.choice([-1,1],size=len(paired))
    neg={key:{'mean_delta_log2_tpm1':round(float(np.mean(delta[i]*negative_signs)),6),
              'exact_signflip_p':round(exact_signflip_p(delta[i]*negative_signs),8)}
         for key,i in selected.items()}
    # This is a single negative-control resampling, not proof of a null model.
    # Under fixed d, signs change the observed statistic and often the p-value.
    assert all(0 <= neg[k]['exact_signflip_p'] <= 1 for k in selected)
    # Do not interpret a caller-supplied filename or string as proof of GEO origin.
    if qc.get('source_accession')==GSE:
        if (len(names)<1000 or len(samples)!=35 or set(samples)!=set(GEO_SAMPLE_TITLES)):
            raise ValueError('GEO_COHORT_IDENTITY_GATE: expected exactly 35 known GEO specimens and >1000 genes')
    status=('EXPLORATORY_GEO_DOWNLOADED' if qc.get('retrieval')=='downloaded_geo' else
            'EXPLORATORY_UNVERIFIED_PROVENANCE' if qc.get('source_accession')==GSE else 'FIXTURE_ONLY')
    return {'status':status,
            'dataset':GSE,'scope':'paired pre/post BCG only; NO BCG clinical response and NO cretostimogene treated patients',
            'qc':{**qc,'n_patients_with_pairs':len(paired),'n_unique_patients':len(sample_counts),
                  'n_specimens':total_specimens,'n_pre_specimens':sum(v['pre'] for v in sample_counts.values()),
                  'n_post_specimens':sum(v['post'] for v in sample_counts.values()),
                  'patient_ids':paired,'repeated_posts_averaged_within_patient':True},
            'predeclared_gene_effects':effects,
            'negative_control':{'type':'fixed-seed patient-level random sign flip (one placebo contrast)','results':neg},
            'analysis_seed':SEED,
            'caveats':['No randomization or untreated comparator; pre/post effects can reflect time, recurrence, sampling.',
                       'Post specimens from a patient averaged; unequal sampling timepoints not modeled.',
                       'GEO cohort does not label cretostimogene outcome; no therapy prediction claim.',
                       'No external BCG validation or clinical predictive-performance evaluation.',
                       'Sign-flip exchangeability and sample annotations require independent verification.']}


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path,default=Path('validation/cache')/FILENAME)
    ap.add_argument('--output',type=Path,default=Path('reports/cretostimogene/gse244895_paired_exploratory.json'))
    ap.add_argument('--download',action='store_true')
    args=ap.parse_args()
    retrieval=None
    if args.download:
        source,url=fetch_source(args.input)
        retrieval='downloaded_geo' if source=='downloaded' else 'local_cached_unverified'
        print(json.dumps({'acquisition':source,'url':url}))
    elif not args.input.is_file():
        raise SystemExit('MATRIX_NOT_AVAILABLE: give --input local file or add --download in authorized network')
    names,x,samples,qc=read_tpm(args.input)
    qc['retrieval']=retrieval or 'local_supplied_unverified'
    report=analyze(names,x,samples,qc)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'matrix_sha256':qc['matrix_sha256'],
                      'n_pairs':report['qc']['n_patients_with_pairs'],
                      'markers':len(report['predeclared_gene_effects'])}))
    return 0

if __name__=='__main__':raise SystemExit(main())
