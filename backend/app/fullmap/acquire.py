"""Authorized 2020-09..12 warm-up only, using existing integrity machinery."""
import json
import zipfile
import httpx
import pandas as pd
from app.market.aggregate_trades import download_file,sha256,write_json
from app.market.phase3_archives import process_trades,process_candles
from app.market.phase3_coverage import POLICY,read_windows,minute_trades,classify_minute,resolve_boundaries,merged_intervals,fingerprint
from app.research.models import identity
from app.research.phase3_plan import utc
from .contract import ROOT,SOURCE,permitted

WARM=ROOT/'warmup'
MONTHS=['2020-09','2020-10','2020-11','2020-12']


def capture(period,kind,daily=False):
    start=utc(period if daily else period+'-01')
    end=start+86400000 if daily else int((pd.Timestamp(start,unit='ms',tz='UTC')+pd.offsets.MonthBegin()).timestamp()*1000)
    permitted(start,end)
    if period[:7] not in MONTHS and not (daily and period=='2021-01-01'):
        raise ValueError('Only authorized warm-up and boundary audit requests')
    suffix='aggTrades' if kind=='aggTrades' else '1m' if daily else '1h'
    name=f'BTCUSDT-{suffix}-{period}.zip';frequency='daily' if daily else 'monthly'
    route=f'aggTrades/BTCUSDT/{name}' if kind=='aggTrades' else f'klines/BTCUSDT/{suffix}/{name}'
    url=f'https://data.binance.vision/data/futures/um/{frequency}/{route}'
    directory=WARM/'raw'/frequency/kind;directory.mkdir(parents=True,exist_ok=True)
    path=directory/name;checksum=directory/(name+'.CHECKSUM')
    with httpx.Client(timeout=180,follow_redirects=True) as client:
        download_file(client,url,path);download_file(client,url+'.CHECKSUM',checksum)
    parts=checksum.read_text().split();digest=sha256(path)
    if len(parts)!=2 or parts[0].lower()!=digest or parts[1].lstrip('*')!=name:raise ValueError('Official checksum mismatch')
    with zipfile.ZipFile(path) as z:
        if len(z.namelist())!=1 or not z.namelist()[0].endswith('.csv') or z.testzip() is not None:raise ValueError('ZIP CRC/member failure')
    return path,dict(month=period[:7],kind=kind,start=start,end=end,url=url,sha256=digest,
        bytes=path.stat().st_size,checksum_verified=True,zip_crc_verified=True,warmup_only=True)


def read_klines(path):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as stream:header=0 if stream.readline().startswith(b'open_time') else None
        with z.open(z.namelist()[0]) as stream:frame=pd.read_csv(stream,header=header)
    frame.columns=['minute','open','high','low','close','volume','end','quote','count','buy','buy_quote','ignore']
    return frame


def replace_invalid_month(month,rejected):
    """Select the complete official daily publication, never fill invented rows."""
    rejection=WARM/'integrity'/f'{month}-aggTrades-monthly-rejected.json'
    if not rejection.exists():write_json(rejection,rejected)
    paths=[];sources=[]
    dates=pd.date_range(pd.Timestamp(rejected['start'],unit='ms',tz='UTC'),
                        pd.Timestamp(rejected['end']-1,unit='ms',tz='UTC'),freq='D')
    for date in dates:
        day=date.strftime('%Y-%m-%d');path,source=capture(day,'aggTrades',True)
        paths.append(path);sources.append(source)
        print('DAILY_REPLACEMENT',day,flush=True)
    selected={k:rejected[k] for k in ['month','kind','start','end','url','warmup_only']}
    selected.update(source_kind='official_daily_collection',source_parts=sources,
        sha256=identity(sources),monthly_sha256=rejected['sha256'],checksum_verified=True,zip_crc_verified=True,
        replacement_reason=rejected.get('error'),rejected_monthly_report_sha256=sha256(rejection))
    selected=process_trades(paths,selected,WARM)
    # Inspect the replaced missing dates at minute resolution against official klines.
    evidence=[];audit_sources=[];quarantines=[]
    for day in rejected.get('missing_dates',[]):
        start=utc(day);end=start+86400000
        raw,_=capture(day,'aggTrades',True)
        trades=minute_trades(read_windows(raw,[(start,end)])).set_index('minute')
        raw,source=capture(day,'klines',True);audit_sources.append(source);klines=read_klines(raw).set_index('minute')
        local=[]
        for t in range(start,end,60000):
            row=trades.loc[t].to_dict() if t in trades.index else dict(quantity=0.,count=0.)
            valid=t in klines.index and int(klines.loc[t,'end'])==t+59999
            q=float(klines.loc[t,'volume']) if valid else None
            local.append(dict(minute=t,quantity=float(row['quantity']),kline_quantity=q,trade_count=int(row['count']),
                first_time=row.get('first_time'),last_time=row.get('last_time'),source_agrees=True,
                decision=classify_minute(float(row['quantity']),q,True,valid)))
        local=resolve_boundaries(local);evidence.extend(local)
        quarantines.extend(r['minute'] for r in local if r['decision']=='QUARANTINE')
    audit=dict(month=month,decision='SELECT_COMPLETE_VERIFIED_OFFICIAL_DAILY_COLLECTION',
        monthly_missing_dates=rejected.get('missing_dates',[]),monthly_rows=rejected.get('rows'),
        selected_daily_rows=selected['rows'],source_agreement_scope='daily vs official klines; monthly missing dates do not agree',
        minute_evidence=evidence,kline_sources=audit_sources,
        quarantine_intervals=merged_intervals(quarantines),unresolved_minutes=sum(r['decision']=='UNRESOLVED' for r in evidence),
        policy=POLICY,outcomes_used=False)
    (WARM/'coverage').mkdir(exist_ok=True);write_json(WARM/'coverage'/f'{month}-publication.json',audit)
    if audit['unresolved_minutes']:raise ValueError('Daily replacement coverage unresolved')
    return selected


def audit_gap(gap,reports):
    start=max(utc('2020-09-01'),(gap['before']['timestamp']//60000-5)*60000)
    end=min(utc('2021-01-02'),(gap['after']['timestamp']//60000+6)*60000)
    gid=identity([gap['before']['id'],gap['after']['id']]);dest=WARM/'coverage';dest.mkdir(exist_ok=True)
    path=dest/f'{gid}.json'
    if path.exists():return json.loads(path.read_text())
    monthly=[];daily=[];klines=[];sources=[]
    days=pd.date_range(pd.Timestamp(start,unit='ms',tz='UTC').floor('D'),pd.Timestamp(end-1,unit='ms',tz='UTC').floor('D'),freq='D')
    for month in sorted(set(days.strftime('%Y-%m'))):
        raw=(WARM/'raw/monthly/aggTrades' if month in MONTHS else SOURCE/'raw/aggTrades')/f'BTCUSDT-aggTrades-{month}.zip'
        assert sha256(raw)==reports[month].get('monthly_sha256',reports[month]['sha256'])
        monthly.append(read_windows(raw,[(start,end)]))
    for date in days:
        day=date.strftime('%Y-%m-%d')
        raw,source=capture(day,'aggTrades',True);sources.append(source);daily.append(read_windows(raw,[(start,end)]))
        raw,source=capture(day,'klines',True);sources.append(source);klines.append(read_klines(raw))
    m=pd.concat(monthly,ignore_index=True);d=pd.concat(daily,ignore_index=True);k=pd.concat(klines,ignore_index=True)
    same=len(m)==len(d) and fingerprint(m)==fingerprint(d)
    minutes=minute_trades(m).set_index('minute');evidence=[]
    for t in range(start,end,60000):
        row=minutes.loc[t].to_dict() if t in minutes.index else dict(quantity=0.,count=0.)
        kr=k[k.minute==t];valid=len(kr)==1 and int(kr.iloc[0]['end'])==t+59999
        q=float(kr.iloc[0].volume) if valid else None
        decision=classify_minute(float(row['quantity']),q,same,valid)
        evidence.append(dict(minute=t,quantity=float(row['quantity']),kline_quantity=q,
            first_time=row.get('first_time'),last_time=row.get('last_time'),source_agrees=same,decision=decision,
            trade_count=int(row['count']),aggregate_high=row.get('high'),aggregate_low=row.get('low'),
            kline_high=float(kr.iloc[0].high) if valid else None,kline_low=float(kr.iloc[0].low) if valid else None))
    evidence=resolve_boundaries(evidence)
    bad=merged_intervals([r['minute'] for r in evidence if r['decision']=='QUARANTINE'])
    unresolved=any(r['decision']=='UNRESOLVED' for r in evidence)
    result=dict(gap=gap,timestamp_gap_ms=gap['after']['timestamp']-gap['before']['timestamp'],
        price_change_fraction=gap['after']['price']/gap['before']['price']-1,daily_monthly_agree=same,
        decision='UNRESOLVED' if unresolved else 'PARTIAL_MINUTE_QUARANTINE' if bad else 'RETAIN_WARNING',
        minute_evidence=evidence,quarantine_intervals=bad,policy=POLICY,sources=sources,outcomes_used=False)
    write_json(path,result);return result


def main():
    WARM.mkdir(parents=True,exist_ok=True);(WARM/'integrity').mkdir(exist_ok=True)
    write_json(WARM/'plan.json',dict(months=MONTHS,usage='850-day warm-up/history only; never performance samples',
        coverage_policy=POLICY,no_2024=True,outcomes_used=False))
    reports={}
    for month in MONTHS:
        for kind in ['klines','aggTrades']:
            path=WARM/'integrity'/f'{month}-{kind}.json'
            if path.exists() and json.loads(path.read_text()).get('passed'):
                report=json.loads(path.read_text())
            else:
                print('ACQUIRE_WARMUP',month,kind,flush=True)
                prior=json.loads(path.read_text()) if path.exists() else None
                archive,report=capture(month,kind)
                if kind=='aggTrades' and prior and not prior.get('passed'):
                    report=replace_invalid_month(month,prior)
                else:
                    try:
                        report=(process_trades if kind=='aggTrades' else process_candles)(archive,report,WARM)
                    except Exception as exc:
                        report.update(passed=False,error=str(exc));write_json(path,report)
                        if kind!='aggTrades':raise
                        report=replace_invalid_month(month,report)
                write_json(path,report)
            if kind=='aggTrades':reports[month]=report
            print('VERIFIED_WARMUP',month,kind,report['rows'],flush=True)
    reports['2021-01']=json.loads((SOURCE/'integrity/2021-01-aggTrades.json').read_text())
    gaps=[g for m in MONTHS for g in reports[m].get('gaps',[])]
    previous=None
    for month,report in reports.items():
        if previous:
            step=report['first_aggregate_id']-previous['last_aggregate_id']
            if step<=0 or report['first_timestamp']<previous['last_timestamp']:raise ValueError('Cross-month order violation')
            if step>1:gaps.append(dict(before=previous['last_record'],after=report['first_record'],id_step=step))
        previous=report
    audits=[audit_gap(g,reports) for g in gaps]
    publications=[json.loads(p.read_text()) for p in sorted((WARM/'coverage').glob('*-publication.json'))]
    result=dict(ready=all(a['decision']!='UNRESOLVED' for a in audits) and not any(p['unresolved_minutes'] for p in publications),warmup_only=True,
        aggregate_rows=sum(reports[m]['rows'] for m in MONTHS),gap_decisions=audits,
        publication_decisions=publications,
        quarantine_intervals=merged_intervals([t for a in audits+publications for left,right in a['quarantine_intervals'] for t in range(left,right,60000)]),
        profile_hashes={m:reports[m]['profile_sha256'] for m in MONTHS},
        source_hashes={m:reports[m]['sha256'] for m in MONTHS},outcomes_used=False)
    write_json(WARM/'coverage.json',result)
    if not result['ready']:raise ValueError('Warm-up coverage unresolved')
    print('WARMUP_READY',result['aggregate_rows'],len(gaps),flush=True)


if __name__=='__main__':main()
