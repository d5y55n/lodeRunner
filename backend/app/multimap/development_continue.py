"""Finite development continuation; never starts replication or touches 2024."""
import traceback
from .contract import ROOT,write_json
from .profiles import build
from .flow import execute as flow
from .analyze import execute as analyze


def main():
    path=ROOT/'development-continuation.json'
    stage='profiles'
    try:
        for month in range(1,13):
            stage=f'profiles/2022-{month:02d}'
            write_json(path,dict(status='RUNNING',stage=stage))
            build(f'2022-{month:02d}')
        stage='15m/flow';write_json(path,dict(status='RUNNING',stage=stage))
        flow('15m','development')
        stage='15m/analysis';write_json(path,dict(status='RUNNING',stage=stage))
        analyze('15m','development')
        write_json(path,dict(status='COMPLETE_REVIEW_AND_FREEZE_PENDING',stage=stage))
    except Exception:
        write_json(path,dict(status='FAILED',stage=stage,error=traceback.format_exc()))
        raise


if __name__=='__main__':main()
