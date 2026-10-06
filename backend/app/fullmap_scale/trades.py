"""Additional authoritative trade history; coverage adjudication is outcome-blind."""
import json
import pandas as pd
from app.market.aggregate_trades import sha256,write_json
from app.market.phase3_archives import process_trades
from app.market.phase3_coverage import POLICY,read_windows,minute_trades,classify_minute,resolve_boundaries,merged_intervals,fingerprint
from app.fullmap.acquire import read_klines
from app.research.models import identity
from .history import ROOT,HISTORY,REFERENCE,MONTHS,archive


def inspect(start,end,selected,require_monthly_agreement):
    days=pd.date_range(pd.Timestamp(start,unit='ms',tz='UTC').floor('D'),pd.Timestamp(end-1,unit='ms',tz='UTC').floor('D'),freq='D')
    daily=[];klines=[];sources=[]
    for date in days:
        day=date.strftime('%Y-%m-%d');p,r=archive(day,'aggTrades','daily');sources.append(r);daily.append(read_windows(p,[(start,end)]))
        p,r=archive(day,'klines','daily','1m');sources.append(r);klines.append(read_klines(p))
    d=pd.concat(daily,ignore_index=True);k=pd.concat(klines,ignore_index=True)
    m=pd.concat([read_windows(p,[(start,end)]) for p in selected],ignore_index=True) if selected else d
    same=len(m)==len(d) and fingerprint(m)==fingerprint(d)
    minutes=minute_trades(d).set_index('minute');evidence=[]
    for t in range(start,end,60000):
        row=minutes.loc[t].to_dict() if t in minutes.index else dict(quantity=0.,count=0.)
        kr=k[k.minute==t];valid=len(kr)==1 and int(kr.iloc[0]['end'])==t+59999
        q=float(kr.iloc[0].volume) if valid else None
        evidence.append(dict(minute=t,quantity=float(row['quantity']),kline_quantity=q,trade_count=int(row['count']),
            first_time=row.get('first_time'),last_time=row.get('last_time'),source_agrees=same,
            aggregate_high=row.get('high'),aggregate_low=row.get('low'),
            kline_high=float(kr.iloc[0].high) if valid else None,kline_low=float(kr.iloc[0].low) if valid else None,
            decision=classify_minute(float(row['quantity']),q,same if require_monthly_agreement else True,valid)))
    evidence=resolve_boundaries(evidence)
    return dict(start=start,end=end,sources=sources,daily_monthly_agree=same,minute_evidence=evidence,
        comparison='daily versus monthly and official kline' if require_monthly_agreement else 'complete selected daily publication versus official kline; monthly rejection preserved',
        unresolved=any(r['decision']=='UNRESOLVED' for r in evidence),
        quarantine_intervals=merged_intervals([r['minute'] for r in evidence if r['decision']=='QUARANTINE']),outcomes_used=False)


def main():
    (HISTORY/'coverage').mkdir(parents=True,exist_ok=True)
    write_json(HISTORY/'trade-policy.json',dict(policy=POLICY,months=MONTHS,earliest_day='2019-12-31',outcomes_used=False,
        rule='same coverage-v4, retain ID-only warnings, objectively bounded observable-loss quarantine, full daily publication if monthly dates missing'))
    reports={};audits=[]
    for period in ['2019-12-31']+MONTHS:
        month=period[:7];dest=HISTORY/'integrity'/f'{month}-aggTrades.json'
        if dest.exists() and json.loads(dest.read_text()).get('passed'):
            report=json.loads(dest.read_text());reports[month]=report;continue
        path,report=archive(period,'aggTrades','daily' if len(period)==10 else 'monthly')
        try:process_trades(path,report,HISTORY)
        except ValueError as exc:
            report.update(passed=False,error=str(exc));write_json(HISTORY/'integrity'/f'{month}-monthly-rejected.json',report)
            if not report.get('missing_dates'):raise
            parts=[];sources=[]
            for date in pd.date_range(pd.Timestamp(report['start'],unit='ms',tz='UTC'),pd.Timestamp(report['end']-1,unit='ms',tz='UTC'),freq='D'):
                p,r=archive(date.strftime('%Y-%m-%d'),'aggTrades','daily');parts.append(p);sources.append(r)
            rejected=report;report={k:report[k] for k in ['month','kind','start','end','url','warmup_only']}
            report.update(source_kind='official_daily_collection',source_parts=sources,sha256=identity(sources),monthly_sha256=rejected['sha256'],
                checksum_verified=True,zip_crc_verified=True)
            process_trades(parts,report,HISTORY)
            for day in rejected['missing_dates']:
                start=int(pd.Timestamp(day,tz='UTC').timestamp()*1000)
                evidence=inspect(start,start+86400000,[],False)
                write_json(HISTORY/'coverage'/f'publication-{day}.json',evidence)
        write_json(dest,report);reports[month]=report
        print('EXTENDED_TRADES',month,report['rows'],flush=True)
    reports['2020-09']=json.loads((REFERENCE/'warmup/integrity/2020-09-aggTrades.json').read_text())
    previous=None;gaps=[]
    for month,report in reports.items():
        gaps.extend(report.get('gaps',[]))
        if previous:
            step=report['first_aggregate_id']-previous['last_aggregate_id']
            if step<=0 or report['first_timestamp']<previous['last_timestamp']:raise ValueError('Cross-period sequence error')
            if step>1:gaps.append(dict(before=previous['last_record'],after=report['first_record'],id_step=step))
        previous=report
    for gap in gaps:
        start=max(1577750400000,(gap['before']['timestamp']//60000-5)*60000)
        end=(gap['after']['timestamp']//60000+6)*60000;path=HISTORY/'coverage'/(identity(gap)+'.json')
        if path.exists():continue
        months=pd.date_range(pd.Timestamp(start,unit='ms',tz='UTC').floor('D'),pd.Timestamp(end-1,unit='ms',tz='UTC').floor('D'),freq='D').strftime('%Y-%m')
        paths=[]
        for month in sorted(set(months)):
            root=REFERENCE/'warmup' if month=='2020-09' else HISTORY
            path_raw=root/'raw/monthly/aggTrades'/f'BTCUSDT-aggTrades-{month}.zip'
            if month=='2019-12':path_raw=HISTORY/'raw/daily/aggTrades/BTCUSDT-aggTrades-2019-12-31.zip'
            paths.append(path_raw)
        evidence=inspect(start,end,paths,True)
        evidence.update(gap=gap,timestamp_gap_ms=gap['after']['timestamp']-gap['before']['timestamp'],
            price_change_fraction=gap['after']['price']/gap['before']['price']-1)
        write_json(path,evidence)
    audits=[json.loads(p.read_text()) for p in sorted((HISTORY/'coverage').glob('*.json'))]
    result=dict(ready=not any(a['unresolved'] for a in audits),outcomes_used=False,
        aggregate_rows=sum(r['rows'] for m,r in reports.items() if m!='2020-09'),aggregate_gaps=len(gaps),
        quarantine_intervals=merged_intervals([t for a in audits for lo,hi in a['quarantine_intervals'] for t in range(lo,hi,60000)]),
        source_hashes={m:r['sha256'] for m,r in reports.items()},profile_hashes={m:r['profile_sha256'] for m,r in reports.items()},
        forensic_hashes={p.name:sha256(p) for p in sorted((HISTORY/'coverage').glob('*.json'))})
    write_json(HISTORY/'trade-coverage.json',result)
    print('EXTENDED_TRADE_COVERAGE',result['ready'],result['aggregate_rows'],flush=True)


if __name__=='__main__':main()
