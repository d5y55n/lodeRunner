import zipfile
from types import SimpleNamespace
import numpy as np
import pytest
from app.multimap import profiles
from app.multimap.contract import sha256,write_json,identity
from app.multimap.crossings import History,features


def test_daily_publication_collection_is_verified_not_reconstructed(tmp_path,monkeypatch):
    monkeypatch.setattr(profiles,'SOURCE',tmp_path)
    (tmp_path/'integrity').mkdir();folder=tmp_path/'raw/daily-audit';folder.mkdir(parents=True)
    parts=[]
    for day in range(1,32):
        path=folder/f'BTCUSDT-aggTrades-2022-08-{day:02d}.zip'
        with zipfile.ZipFile(path,'w') as archive:archive.writestr('trades.csv','test fixture')
        digest=sha256(path)
        path.with_name(path.name+'.CHECKSUM').write_text(digest+' '+path.name)
        parts.append(dict(url='https://data.binance.vision/'+path.name,sha256=digest))
    report=dict(source_kind='official_daily_collection',passed=True,source_parts=parts,sha256=identity(parts))
    write_json(tmp_path/'integrity/2022-08-aggTrades.json',report)
    coverage=dict(source_hashes={'2022-08':identity(parts)})
    selected,_=profiles.verify_source('2022-08',coverage)
    assert len(selected)==31 and all(p.parent==folder for p in selected)
    selected[3].write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum'):profiles.verify_source('2022-08',coverage)
    with pytest.raises(ValueError):profiles.verify_source('2024-01',coverage)


def history(n):
    close=np.array([99,99,101,99,101,99.])[:n]
    return History(SimpleNamespace(known=np.array([2*3600000]),prices=np.array([100.]),
        reference=SimpleNamespace(ends=np.arange(1,n+1)*3600000),close=close,
        low=close-2,high=close+2),capacity=1)


def test_crossing_features_equal_physically_truncated_input():
    a=features(history(6),np.array([0]),4*3600000,100.,.002)
    b=features(history(4),np.array([0]),4*3600000,100.,.002)
    assert a==b and a['mean_prior_crossings']==2 and a['mean_prior_visits']==1
    with pytest.raises(ValueError):features(history(6),np.array([0]),3600000,100.,.002)


def test_pipeline_failure_does_not_start_replication(tmp_path,monkeypatch):
    from app.multimap import finish
    from app.multimap.contract import read
    calls=[]
    monkeypatch.setattr(finish,'ROOT',tmp_path)
    monkeypatch.setattr(finish,'BACKEND',tmp_path)
    def failure(args,**kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=9)
    monkeypatch.setattr(finish.subprocess,'run',failure)
    with pytest.raises(RuntimeError,match='development-profiles'):finish.main()
    assert len(calls)==1 and 'replication' not in calls[0]
    assert read(tmp_path/'pipeline-status.json')['status']=='FAILED'


def test_report_contrasts_preserve_missing_quarters():
    import pandas as pd
    from app.multimap.reports import differences
    rows=[]
    for period in ['ALL','2022-Q1','2022-Q2']:
        for bucket in [0,3]:
            if period=='2022-Q2' and bucket==3:continue
            rows.append(dict(period=period,bucket=bucket,complete=10,direction='LONG',tp=.003,sl=.005,horizon=4,tp_first_rate=.2+bucket/10))
    result=differences(pd.DataFrame(rows),'tp_first_rate')
    assert set(result.period)=={'ALL','2022-Q1'}
    np.testing.assert_allclose(result.difference,.3)
    replication=pd.DataFrame(rows)
    replication['bucket']=replication.bucket.replace({0:1})
    assert differences(replication,'tp_first_rate',bounds=(0,3)).empty


def test_report_curve_shapes_do_not_call_two_points_monotonic_evidence():
    from app.multimap.reports import curve_shape
    assert curve_shape([.1,.9])=='INSUFFICIENT_BUCKETS'
    assert curve_shape([.1,.2,.3])=='INCREASING'
    assert curve_shape([.3,.2,.1])=='DECREASING'
    assert curve_shape([.1,.3,.2])=='NONMONOTONIC'
    assert curve_shape([.2,.2,.2])=='FLAT'


@pytest.mark.parametrize('quantity',[0.,1.])
def test_empty_trade_interval_corroboration_blocks_observable_loss(tmp_path,monkeypatch,quantity):
    import pandas as pd
    from app.multimap import profile_coverage
    from app.multimap.contract import read
    monkeypatch.setattr(profile_coverage,'ROOT',tmp_path)
    for m in range(1,13):
        folder=tmp_path/'trade-profiles-15m'/f'2022-{m:02d}';folder.mkdir(parents=True)
        write_json(folder/'manifest.json',dict(missing_intervals=[100] if m==1 else []))
    folder=tmp_path/'candles/15m';folder.mkdir(parents=True)
    p=folder/'2022-01.parquet'
    pd.DataFrame([dict(open_time=100,volume=quantity,trade_count=int(quantity),taker_buy_volume=0.,open=100.,close=100.)]).to_parquet(p,index=False)
    write_json(folder/'development-coverage.json',dict(normalized={p.name:sha256(p)}))
    if quantity:
        with pytest.raises(ValueError,match='forensic'):profile_coverage.audit('development')
        assert read(tmp_path/'profile-coverage-development.json')['status']=='BLOCKED'
    else:
        r=profile_coverage.audit('development')
        assert r['no_imputation'] and r['evidence'][0]['classification']=='OFFICIAL_ZERO_ACTIVITY_CORROBORATED'
