#!/usr/bin/env python3
"""OOI Escargot HITL exclusion gate; layer onto existing QARTOD-based analyzer.

No network activity. Accepts a verified offline OOI annotation JSON export and
pinned OOI NetCDF4 sample. A missing snapshot is a hard scientific gate, not
permission to interpret all QARTOD-pass points as eligible.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
from pathlib import Path

SENSOR = 'RS03INT1-MJ03C-10-TRHPHA301'
STREAM = 'trhph_sample'
PARAM = 'vent_fluid_temperature'
NTP_EPOCH = datetime(1900,1,1,tzinfo=timezone.utc)


def _timestamp(value, *, end=False):
    if value is None and end: return datetime.max.replace(tzinfo=timezone.utc)
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        # OOI annotation API uses epoch milliseconds; accept seconds only with
        # explicit ISO datetime to avoid 1000x ambiguity.
        if value < 1_000_000_000_000:
            raise ValueError('expected_unix_milliseconds_not_seconds')
        return datetime.fromtimestamp(value/1000,tz=timezone.utc)
    if isinstance(value,str):
        value=value.strip().replace('Z','+00:00')
        v=datetime.fromisoformat(value)
        if v.tzinfo is None: raise ValueError('annotation_time_timezone_required')
        return v.astimezone(timezone.utc)
    raise ValueError('invalid_annotation_time')


def _same_sensor(r):
    if r.get('refdes') and r['refdes'] != SENSOR:
        return False
    for key,val in (('subsite','RS03INT1'),('node','MJ03C'),('sensor','10-TRHPHA301')):
        if r.get(key) and r[key]!=val:return False
    if r.get('stream') and r['stream']!=STREAM:return False
    if r.get('parameter') and r['parameter']!=PARAM:return False
    # At least one identifying field required: avoid applying anonymous
    # intervals from other sensors to this science variable.
    return any(r.get(k) for k in ('refdes','subsite','node','sensor'))


def parse_annotations(data):
    """Parse OOI M2M-style JSON; preserve annotation provenance separately."""
    records=data.get('annotations') if isinstance(data,dict) else data
    if not isinstance(records,list):raise ValueError('annotation_export_must_be_list')
    normalized=[]
    for index,r in enumerate(records):
        if not isinstance(r,dict):raise ValueError('invalid_annotation_row')
        if not _same_sensor(r):continue
        start=_timestamp(r.get('beginDT',r.get('startDT',r.get('start'))))
        end=_timestamp(r.get('endDT',r.get('end')),end=True)
        if end<start:raise ValueError('annotation_negative_interval')
        qc=r.get('qcFlag',r.get('qc_flag'))
        if qc in (None,''):
            qc=None  # Unclassified annotation => fail closed on overlap.
        else:
            try: qc=int(qc)
            except (TypeError,ValueError):raise ValueError('invalid_annotation_qc_flag')
            if qc not in (1,2,3,4,9):raise ValueError('invalid_annotation_qc_flag')
        normalized.append({'start':start,'end':end,'qcFlag':qc,
          'id':str(r.get('id',f'row-{index}')),
          'text':str(r.get('annotation',r.get('comment','')))[:400]})
    return normalized


def apply_hitl(times_ntp, qartod, annotations):
    if len(times_ntp)!=len(qartod):raise ValueError('length_mismatch')
    mask=list(qartod)
    affected=[]
    unknown=[]
    accepted=[]
    for i,(stamp,q) in enumerate(zip(times_ntp,qartod)):
        utc=NTP_EPOCH+timedelta(seconds=float(stamp))
        matches=[r for r in annotations if r['start']<=utc<=r['end']]
        if not matches:continue
        if any(r['qcFlag'] in (None,2,3,4,9) for r in matches):
            if int(q)==1:mask[i]=4
            affected.append(i)
            if any(r['qcFlag'] is None for r in matches):unknown.append(i)
        else:
            accepted.append(i)
    return mask, {'n_hitl_excluded_from_qartod_pass':sum(int(a)==1 and int(b)!=1 for a,b in zip(qartod,mask)),
                  'hitl_affected_indices':affected,'unclassified_annotation_indices':unknown,
                  'hitl_pass_annotated_indices':accepted}


def analyze_with_hitl(input_path:Path,annotation_path:Path,source_url:str):
    if not source_url.startswith('https://'): raise ValueError('official_annotation_source_url_required')
    import h5py
    import ooi_axial_hydrothermal as ooi
    # This validates the source HDF5 signature, exact 36 samples, variable IDs
    # and input hash using the preexisting analyzer, without a duplicate engine.
    original=ooi.analyze_file(input_path)
    raw=annotation_path.read_bytes()
    normalized=parse_annotations(json.loads(raw))
    with h5py.File(input_path,'r') as f:
        times=f['time'][:].tolist()
        temperatures=f[PARAM][:].tolist()
        flags=f[f'{PARAM}_qartod_results'][:].tolist()
    masked,gate=apply_hitl(times,flags,normalized)
    result=ooi.screen(times,temperatures,masked)
    result.update({
      'source_filename':original['source_filename'],
      'source_sha256':original['source_sha256'],
      'annotation_snapshot_sha256':sha256(raw).hexdigest(),
      'annotation_source_url':source_url,
      'n_matching_annotation_records':len(normalized),
      'qartod_counts_before_hitl':original['qartod_counts'],
      'hitl_gate':gate,'analysis_version':'astra.ooi.axial.escargot.hitl.v2',
      'science_readiness':'HITL_QARTOD_SCREEN_ONLY_NO_PHYSICAL_EVENT_VALIDATION',
      'physical_event_confirmed':False,
    })
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--annotations',type=Path,required=True,help='Export JSON with OOI metadata; absent=BLOCKED')
    p.add_argument('--annotation-source-url',required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if not args.annotations.is_file():p.error('BLOCKED: no reviewed HITL annotations snapshot')
    if not args.input.is_file():p.error('UNVERIFIED: OOI measurement bytes absent')
    result=analyze_with_hitl(args.input,args.annotations,args.annotation_source_url)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'n_excluded_by_hitl':result['hitl_gate']['n_hitl_excluded_from_qartod_pass'],
      'source_sha256':result['source_sha256'],'annotation_sha256':result['annotation_snapshot_sha256']}))

if __name__=='__main__':main()
