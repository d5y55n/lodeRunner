"""Finite development -> definition freeze -> replication -> audit pipeline."""
import argparse
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from .contract import *


def tests(label):
    log=ROOT/'logs'/(label+'.log');log.parent.mkdir(exist_ok=True)
    with log.open('w',encoding='utf-8') as f:
        p=subprocess.run([sys.executable,'-m','pytest','-o','addopts=','-q','--junitxml='+str(ROOT/(label+'.xml'))],
                         cwd=PROJECT/'backend',stdout=f,stderr=subprocess.STDOUT)
    suites=list(ET.parse(ROOT/(label+'.xml')).getroot().iter('testsuite'))
    result={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
    write(ROOT/(label+'.json'),dict(returncode=p.returncode,**result))
    if p.returncode:raise RuntimeError('Tests failed: '+str(log))


def review_development():
    import pandas as pd
    root=ROOT/'development'
    build=read(root/'build-complete.json');analysis=read(root/'analysis/complete.json')
    for relative,h in build['hashes'].items():
        if digest(root/relative)!=h:raise ValueError('Development build changed')
    for relative,h in analysis['hashes'].items():
        if digest(root/'analysis'/relative)!=h:raise ValueError('Development analysis changed')
    f=pd.read_parquet(root/'analysis/cohorts.parquet')
    import numpy as np
    if not (f.complete+f.censored).eq(f.n).all():raise ValueError('Censoring composition')
    nonempty=f[f.complete>0]
    if not np.allclose(nonempty[['TP_FIRST','SL_FIRST','NEITHER','AMBIGUOUS']].sum(axis=1),1):raise ValueError('Outcome composition')
    if set(f.direction)!={'LONG','SHORT'} or set(f.horizon)!={16,32,96} or set(f.period)!={'ALL','1','2','3','4'}:
        raise ValueError('Incomplete grid')
    contrasts=pd.read_parquet(root/'analysis/contrasts.parquet')
    write(root/'review.json',dict(status='REVIEWED_NO_SELECTION',rows=len(f),contrasts=len(contrasts),
        all_grids=True,quarters=True,missing_cells_retained=True,no_ranking=True,
        no_2023_read=True,completed_utc=datetime.now(timezone.utc).isoformat()))


def freeze():
    if (ROOT/'development-freeze.json').exists():
        return check_freeze()
    review_development()
    tests('development-tests')
    from .reports import contract_report
    contract_report()
    files={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'development').rglob('*') if p.is_file()}
    files['development-tests.json']=digest(ROOT/'development-tests.json')
    code={p.name:digest(p) for p in CODE.glob('*.py')}
    value=dict(plan=PLAN,files=files,code=code,completed_utc=datetime.now(timezone.utc).isoformat(),
        contract_report_sha256=digest(PROJECT/'PHASE5_CONFLUENCE_CONTRACT.md'))
    value['freeze_id']=hashlib.sha256(canonical(value).encode()).hexdigest()
    write(ROOT/'development-freeze.json',value)
    print('PHASE5_FROZEN',value['freeze_id'],flush=True)


def preservation():
    check_freeze()
    baseline=read(PROJECT/'data/phase4/preserved-before.json')
    # Prior signed manifests are read-only. Do not call old audit functions that write old outputs.
    for tf in ['15m','4h','1d']:
        from app.multimap.freeze import check
        check(tf)
        for phase in ['development','replication']:
            base=PROJECT/'data/phase4'/tf/phase
            for name,folder in [('price-complete.json',base),('flow-complete.json',base),('crossings-complete.json',base),
                                ('native-states-complete.json',base/'native-states'),('analysis/complete.json',base/'analysis')]:
                manifest=read(base/name)
                for rel,h in manifest['hashes'].items():
                    path=folder/rel
                    key=str(path.relative_to(PROJECT))
                    if key in baseline and baseline[key]!=h:raise ValueError('Conflicting frozen manifests')
                    baseline[key]=h
    for phase in ['development','replication']:
        for name,h in read(ROOT/phase/'source-hashes.json').items():
            if name in baseline and baseline[name]!=h:raise ValueError('Source differed from prior frozen hash: '+name)
            baseline[name]=h
    for name,h in read(PROJECT/'data/phase4/completion.json')['reports'].items():baseline[name]=h
    changed=[name for name,h in baseline.items() if not (PROJECT/name).is_file() or digest(PROJECT/name)!=h]
    write(ROOT/'preservation-audit.json',dict(status='PASS' if not changed else 'FAIL',files=len(baseline),changed=changed))
    if changed:raise ValueError('Native research changed')


def main(stop_after_development=False):
    initialize();stage='initialization'
    def status(s):
        nonlocal stage
        stage=s;write(ROOT/'pipeline-status.json',dict(status='RUNNING',stage=s))
        print('STAGE',s,flush=True)
    try:
        from .build import execute as build
        from .analyze import execute as analyze
        from .reports import contract_report, generate
        if not (ROOT/'development-freeze.json').exists():contract_report()
        status('development-build');build('development')
        status('development-analysis');analyze('development')
        if stop_after_development:
            write(ROOT/'pipeline-status.json',dict(status='DEVELOPMENT_COMPLETE_PENDING_REVIEW_FREEZE',stage='STOP_BEFORE_2023'))
            return
        status('development-review-freeze');freeze();check_freeze()
        status('replication-build');build('replication')
        status('replication-analysis');analyze('replication')
        status('preservation');preservation()
        status('final-tests');tests('final-tests')
        status('reports');generate()
        write(ROOT/'pipeline-status.json',dict(status='COMPLETE',stage='STOP_NO_2024_NO_LIVE_RULE'))
    except Exception:
        write(ROOT/'pipeline-status.json',dict(status='FAILED',stage=stage,error=traceback.format_exc()))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--development-only',action='store_true')
    main(parser.parse_args().development_only)
