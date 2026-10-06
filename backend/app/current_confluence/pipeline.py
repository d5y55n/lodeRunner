"""Finite current-price study with explicit development audit/freeze gate."""
import argparse
from datetime import datetime,timezone
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
from .contract import *


def tests(label):
    log=ROOT/'logs'/(label+'.log');log.parent.mkdir(exist_ok=True)
    with log.open('w',encoding='utf-8') as f:
        p=subprocess.run([sys.executable,'-m','pytest','-o','addopts=','-q','--junitxml='+str(ROOT/(label+'.xml'))],
            cwd=PROJECT/'backend',stdout=f,stderr=subprocess.STDOUT)
    suites=list(ET.parse(ROOT/(label+'.xml')).getroot().iter('testsuite'))
    counts={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','errors','failures','skipped']}
    write(ROOT/(label+'.json'),dict(returncode=p.returncode,**counts))
    if p.returncode:raise ValueError('Suite failed: '+str(log))


def review():
    import pandas as pd
    import numpy as np
    root=ROOT/'development'
    for name,folder in [('states-complete.json',root),('analysis/complete.json',root/'analysis')]:
        for rel,h in read(root/name)['hashes'].items():
            if digest(folder/rel)!=h:raise ValueError('Development artifact changed')
    if read(root/'classification-audit.json')['status']!='PASS':raise ValueError('Missing classification gate')
    f=pd.read_parquet(root/'analysis/cohorts.parquet')
    if not (f.complete+f.censored).eq(f.N).all():raise ValueError('Censor counts')
    if not np.allclose(f.loc[f.complete>0,['TP_FIRST','SL_FIRST','NEITHER','AMBIGUOUS']].sum(axis=1),1):raise ValueError('Outcome composition')
    if set(f.period)!={'ALL','1','2','3','4'} or set(f.horizon)!={16,32,96}:raise ValueError('Incomplete grids')
    write(root/'review.json',dict(status='REVIEWED_NO_SELECTION',same_P_audit_pass=True,
        no_replication_read=True,no_spatial=True,all_hypotheses_retained=True,utc=datetime.now(timezone.utc).isoformat()))


def freeze():
    if (ROOT/'development-freeze.json').exists():return check_freeze()
    review();tests('development-tests')
    from app.confluence.contract import check_freeze as previous_check
    previous=previous_check()
    files={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'development').rglob('*') if p.is_file()}
    files['development-tests.json']=digest(ROOT/'development-tests.json')
    value=dict(plan=PLAN,files=files,code={p.name:digest(p) for p in CODE.glob('*.py')},
        previous_phase5_freeze_id=previous['freeze_id'],utc=datetime.now(timezone.utc).isoformat())
    value['freeze_id']=hashlib.sha256(canonical(value).encode()).hexdigest()
    write(ROOT/'development-freeze.json',value)
    print('CURRENT_PRICE_FROZEN',value['freeze_id'],flush=True)


def preservation():
    check_freeze();base=read(PROJECT/'data/phase4/preserved-before.json')
    def add(path,h):
        key=str(path.relative_to(PROJECT))
        if key in base and base[key]!=h:raise ValueError('Conflicting preservation hash '+key)
        base[key]=h
    for tf in ['15m','4h','1d']:
        from app.multimap.freeze import check
        check(tf)
        for phase in ['development','replication']:
            root=PROJECT/'data/phase4'/tf/phase
            for name,folder in [('price-complete.json',root),('flow-complete.json',root),('crossings-complete.json',root),
                ('native-states-complete.json',root/'native-states'),('analysis/complete.json',root/'analysis')]:
                for rel,h in read(root/name)['hashes'].items():add(folder/rel,h)
    for phase in ['development','replication']:
        root=PROJECT/'data/phase5'/phase
        for name,folder in [('build-complete.json',root),('analysis/complete.json',root/'analysis')]:
            for rel,h in read(root/name)['hashes'].items():add(folder/rel,h)
        for source in [root/'source-hashes.json',ROOT/phase/'source-hashes.json']:
            for rel,h in read(source).items():add(PROJECT/rel,h)
    for previous in ['phase4','phase5']:
        for name,h in read(PROJECT/'data'/previous/'completion.json')['reports'].items():add(PROJECT/name,h)
    changed=[]
    for i,(rel,h) in enumerate(base.items()):
        p=PROJECT/rel
        if not p.is_file() or digest(p)!=h:changed.append(rel)
        if (i+1)%10000==0:print('CURRENT_PRICE_PRESERVATION',i+1,len(base),flush=True)
    write(ROOT/'preservation-audit.json',dict(status='PASS' if not changed else 'FAIL',files=len(base),changed=changed))
    if changed:raise ValueError('Frozen artifacts changed')


def main(states_only=False,development_only=False):
    initialize();stage='initialization'
    def status(name):
        nonlocal stage
        stage=name;write(ROOT/'pipeline-status.json',dict(status='RUNNING',stage=name));print('STAGE',name,flush=True)
    try:
        from .states import execute as states
        from .analyze import execute as analyze
        status('development-current-price-states');states('development')
        if states_only:
            write(ROOT/'pipeline-status.json',dict(status='CLASSIFICATION_AUDITED',stage='STOP_BEFORE_OUTCOMES'));return
        status('development-narrow-analysis');analyze('development')
        if development_only:
            write(ROOT/'pipeline-status.json',dict(status='DEVELOPMENT_COMPLETE',stage='STOP_BEFORE_FREEZE_REPLICATION'));return
        status('development-review-freeze');freeze()
        status('replication-current-price-states');states('replication')
        status('replication-narrow-analysis');analyze('replication')
        status('preservation');preservation()
        status('final-tests');tests('final-tests')
        status('reports')
        from .reports import generate
        generate();write(ROOT/'pipeline-status.json',dict(status='COMPLETE',stage='STOP_NO_2024_NO_LIVE_RULE'))
    except Exception:
        write(ROOT/'pipeline-status.json',dict(status='FAILED',stage=stage,error=traceback.format_exc()));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--states-only',action='store_true');parser.add_argument('--development-only',action='store_true')
    args=parser.parse_args();main(args.states_only,args.development_only)
