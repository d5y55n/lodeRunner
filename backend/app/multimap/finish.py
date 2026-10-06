"""Finite Phase 4 dependency pipeline; failures stop, never bypass a research gate."""
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from .contract import ROOT,read,write_json,sha256
from .freeze import check

BACKEND=Path(__file__).resolve().parents[2]


def main():
    status=ROOT/'pipeline-status.json';logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    stage_name='initialization'
    def stage(name,module,*args,proof=None):
        nonlocal stage_name
        stage_name=name
        if proof is not None and proof.exists():
            print('STAGE_ALREADY_COMPLETE',name,flush=True);return
        write_json(status,dict(status='RUNNING',stage=name,log=str(logs/(name+'.log'))))
        print('STAGE_START',name,flush=True)
        with (logs/(name+'.log')).open('w',encoding='utf-8') as stream:
            result=subprocess.run([sys.executable,'-m',module,*args],cwd=BACKEND,stdout=stream,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError(f'{name} failed ({result.returncode}); see {logs/(name+".log")}')
        print('STAGE_COMPLETE',name,flush=True)
    try:
        stage('development-profiles','app.multimap.profiles','development')
        for tf in ['4h','1d','15m']:
            root=ROOT/tf/'development'
            stage(f'{tf}-development-crossings','app.multimap.crossings',tf,'development',proof=root/'crossings-complete.json')
            stage(f'{tf}-development-flow','app.multimap.flow',tf,'development',proof=root/'flow-complete.json')
            proof=root/'analysis/complete.json'
            valid=proof.exists() and read(proof)['analysis_code_sha256']==sha256(BACKEND/'app/multimap/analyze.py')
            stage(f'{tf}-development-analysis','app.multimap.analyze',tf,'development',proof=proof if valid else None)
        if not all((ROOT/tf/'development-freeze.json').exists() for tf in ['15m','4h','1d']):
            stage('development-review-freeze','app.multimap.freeze','freeze')
        for tf in ['15m','4h','1d']:check(tf)
        for tf in ['15m','4h','1d']:
            stage(f'{tf}-replication-candles','app.multimap.data','replication',tf,proof=ROOT/'candles'/tf/'replication-coverage.json')
        stage('replication-profiles','app.multimap.profiles','replication')
        for tf in ['4h','1d','15m']:
            check(tf);root=ROOT/tf/'replication'
            stage(f'{tf}-replication-price','app.multimap.run',tf,'replication',proof=root/'price-complete.json')
            stage(f'{tf}-replication-crossings','app.multimap.crossings',tf,'replication',proof=root/'crossings-complete.json')
            stage(f'{tf}-replication-flow','app.multimap.flow',tf,'replication',proof=root/'flow-complete.json')
            stage(f'{tf}-replication-analysis','app.multimap.analyze',tf,'replication',proof=root/'analysis/complete.json')
        stage('preservation-audit','app.multimap.audit')
        stage_name='final-tests';write_json(status,dict(status='RUNNING',stage=stage_name))
        with (logs/'final-tests.log').open('w',encoding='utf-8') as stream:
            r=subprocess.run([sys.executable,'-m','pytest','-o','addopts=','-q','--junitxml='+str(ROOT/'final-tests.xml')],cwd=BACKEND,stdout=stream,stderr=subprocess.STDOUT)
        suites=list(ET.parse(ROOT/'final-tests.xml').getroot().iter('testsuite'))
        counts={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
        write_json(ROOT/'final-tests.json',dict(returncode=r.returncode,**counts))
        if r.returncode:raise RuntimeError('Final suite failed; no completion report published')
        stage('final-reports','app.multimap.reports')
        write_json(status,dict(status='COMPLETE',stage='STOP_NO_CONFLUENCE',completion=str(ROOT/'completion.json')))
    except Exception:
        write_json(status,dict(status='FAILED',stage=stage_name,error=traceback.format_exc()))
        raise


if __name__=='__main__':main()
