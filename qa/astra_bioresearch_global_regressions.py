#!/usr/bin/env python3
"""Pre-merge full-checkout regression gate for BIO-MIMIC X (stdlib, no CI/cron).

Requires a local checkout containing both the pinned main ancestor and the
candidate branch. Runs tests on an ephemeral git archive, not on production.
Never claims global PASS when the checkout, baseline, tests or logs are absent.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time

PINNED_BASE = 'faba6ec64b5d54195a5594a00012dd135970bd2d'
BASE_BLOBS = 427
ALLOWED_ADDITIONS = {
    'docs/ASTRA-BIORESEARCH-INSERM-MESH.md',
    'examples/florence-apparailly-mission.json',
    'examples/florence-apparailly-validated-mission.json',
    'factory/inserm_mesh.py',
    'tests/test_inserm_mesh.py',
    'tests/test_inserm_mesh_integration.py',
    'qa/astra_bioresearch_global_regressions.py',
}


def command(argv, cwd, timeout=20, env=None):
    try:
        p = subprocess.run(argv, cwd=cwd, text=True, capture_output=True,
                           timeout=timeout, env=env, check=False)
        return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {'returncode':None,'stdout':'','stderr':type(e).__name__ + ': ' + str(e)}


def git_files(checkout, rev):
    res = subprocess.run(['git','ls-tree','-rz',rev], cwd=checkout,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         timeout=30, check=False)
    if res.returncode:
        raise RuntimeError(res.stderr.decode('utf-8','replace')[:1000])
    tree={}
    for entry in res.stdout.split(b'\0'):
        if not entry:
            continue
        head, path = entry.split(b'\t',1)
        mode,kind,sha=head.split(b' ')
        if kind==b'blob':
            tree[path.decode('utf-8')]=sha.decode('ascii')
    return tree


def execute(checkout, output_dir, timeout=240):
    output_dir.mkdir(parents=True, exist_ok=True)
    report={'schema':'astra-bioresearch-global-regression/1.0',
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'repository':str(checkout),'base':PINNED_BASE,
            'status':'UNVERIFIED','checks':{},'runs':{},
            'new_cost_eur':0,'new_crons':0,'github_actions_used':False,
            'production_modified':False}
    report_path=output_dir/'global-regressions.json'

    def finalize(status,reason):
        report['status']=status
        report['reason']=reason
        report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        return report

    rev=command(['git','rev-parse','--show-toplevel'],checkout)
    if rev['returncode']!=0 or Path(rev['stdout'].strip()).resolve()!=checkout.resolve():
        return finalize('UNVERIFIED','FULL_GIT_CHECKOUT_UNAVAILABLE')
    base=command(['git','cat-file','-e',PINNED_BASE+'^{commit}'],checkout)
    if base['returncode']!=0:
        return finalize('UNVERIFIED','PINNED_MAIN_COMMIT_UNAVAILABLE')
    try:
        before=git_files(checkout,PINNED_BASE)
        after=git_files(checkout,'HEAD')
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
        return finalize('UNVERIFIED','TREE_READ_ERROR: '+str(e)[:1000])
    removed=sorted(set(before)-set(after))
    changed=sorted(p for p,v in before.items() if after.get(p) not in (v,))
    added=sorted(set(after)-set(before))
    unexplained=sorted(set(added)-ALLOWED_ADDITIONS)
    report['checks']['tree']={'base_blob_count':len(before),'head_blob_count':len(after),
        'unchanged_legacy_blobs':sum(after.get(p)==v for p,v in before.items()),
        'removed':removed,'changed':changed,'added':added,'unexplained':unexplained}
    if len(before)!=BASE_BLOBS or removed or changed or unexplained or not ALLOWED_ADDITIONS.issubset(after):
        return finalize('FAIL','GIT_TREE_BASELINE_MISMATCH')
    if len([p for p in after if p.startswith('tests/test_') and p.endswith('.py')])<47:
        return finalize('UNVERIFIED','INCOMPLETE_PYTHON_TEST_COLLECTION')
    if not {'state/factory/programs.json','factory/hypothesis_engine.py',
            'factory/debate_engine.py','factory/experiment_planner.py'}.issubset(after):
        return finalize('UNVERIFIED','SCIENTIFIC_SOURCE_FILES_MISSING')

    # Archive the tracked full candidate tree into a temporary directory to
    # ensure tests cannot mutate actual checkout, production state or Git refs.
    with tempfile.TemporaryDirectory(prefix='astra-bioresearch-global-') as tmp:
        workspace=Path(tmp)/'source'
        workspace.mkdir()
        tarpath=Path(tmp)/'candidate.tar'
        with tarpath.open('wb') as out:
            arch=subprocess.run(['git','archive','--format=tar','HEAD'],cwd=checkout,
                                stdout=out,stderr=subprocess.PIPE,timeout=90)
        if arch.returncode:
            return finalize('UNVERIFIED','CANDIDATE_ARCHIVE_FAILED')
        with tarfile.open(tarpath) as src:
            for entry in src.getmembers():
                dest=(workspace/entry.name).resolve()
                if not dest.is_relative_to(workspace.resolve()) or entry.issym() or entry.islnk():
                    return finalize('FAIL','UNSAFE_ARCHIVE_MEMBER')
            src.extractall(workspace,filter='data')
        report['checks']['complete_checkout']={'status':'PASS','files_extracted':len(after)}
        # Syntax-check every checked-in Python file without creating __pycache__.
        broken=[];py_count=0
        for relative in sorted(p for p in after if p.endswith('.py')):
            py_count+=1
            try:
                compile((workspace/relative).read_bytes(),relative,'exec')
            except (OSError,SyntaxError,ValueError) as e:
                broken.append({'file':relative,'error':str(e)[:500]})
        report['checks']['python_syntax']={'status':'PASS' if not broken else 'FAIL',
                                           'modules':py_count,'errors':broken}
        if broken:
            return finalize('FAIL','SYNTAX_REGRESSIONS')
        # Explicit timeout and safe environment. No custom secrets passed in.
        env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),
             'HOME':str(Path(tmp)), 'PYTHONDONTWRITEBYTECODE':'1',
             'PYTHONPATH':str(workspace), 'LC_ALL':'C.UTF-8'}
        scripts=[('targeted', [sys.executable,'-m','unittest','discover','-s','tests',
                               '-p','test_inserm_mesh*.py','-v']),
                 ('global',[sys.executable,'-m','unittest','discover','-s','tests',
                            '-p','test_*.py','-v']),
                 ('scientific_cycle',[sys.executable,'factory/inserm_mesh.py',
                            '--mission','examples/florence-apparailly-validated-mission.json',
                            '--programs','state/factory/programs.json',
                            '--out',str(Path(tmp)/'scientific-cycle.json')])]
        for name,argv in scripts:
            t=time.monotonic()
            outcome=command(argv,workspace,timeout=timeout,env=env)
            (output_dir/(name+'.stdout.log')).write_text(outcome['stdout'],encoding='utf-8')
            (output_dir/(name+'.stderr.log')).write_text(outcome['stderr'],encoding='utf-8')
            report['runs'][name]={'status':'PASS' if outcome['returncode']==0 else 'FAIL',
                                  'exit_code':outcome['returncode'],
                                  'elapsed_seconds':round(time.monotonic()-t,2),
                                  'stdout_log':name+'.stdout.log',
                                  'stderr_log':name+'.stderr.log'}
            if outcome['returncode']!=0:
                return finalize('FAIL','TEST_FAILED_OR_TIMED_OUT: '+name)
        cycle_path=Path(tmp)/'scientific-cycle.json'
        try:
            cycle=json.loads(cycle_path.read_text(encoding='utf-8'))
            assert cycle['summary']['technical_pipeline']=='PASS'
            assert cycle['summary']['biological_validation']=='UNVERIFIED'
            assert cycle['summary']['roles_executed']==23
            assert cycle['real_wetlab_experiments']==0
            report['checks']['scientific_boundary']='PASS'
        except (OSError,ValueError,KeyError,AssertionError) as e:
            return finalize('FAIL','SCIENTIFIC_BOUNDARY_BROKEN: '+str(e)[:100])
    return finalize('PASS','FULL_CHECKOUT_REGRESSIONS_PASSED_NOT_BIOLOGICAL_VALIDATION')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--checkout',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--out',type=Path,default=Path('/tmp/astra-bioresearch-global-regressions'))
    ap.add_argument('--timeout',type=int,default=240)
    a=ap.parse_args()
    r=execute(a.checkout,a.out,timeout=a.timeout)
    print(json.dumps({'status':r['status'],'reason':r['reason'],
                      'report':str(a.out/'global-regressions.json')},ensure_ascii=False))
    return 0 if r['status']=='PASS' else 2 if r['status']=='UNVERIFIED' else 1

if __name__=='__main__':sys.exit(main())
