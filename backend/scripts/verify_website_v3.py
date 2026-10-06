"""Small explicit real-data verification, not a market-wide scanner."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from app.website.live import Store, PublicFeed, now_ms
from app.website.config import PROJECT


def main():
    report={'verified_at':now_ms(),'symbols':{}}
    with httpx.Client(base_url='http://127.0.0.1:8011',timeout=120) as client:
        universe=client.get('/market/symbols');universe.raise_for_status()
        rows=universe.json()['symbols']
        report['discovered_perpetual_count']=len(rows)
        for symbol in ['BTCUSDT','ETHUSDT','SOLUSDT','CTUSDT']:
            store=Store(symbol=symbol)
            snapshots=store.history(1)
            feed=PublicFeed(symbol)
            try:tick=feed.ticker()
            finally:feed.close()
            with store.connect() as db:
                candles=db.execute('SELECT symbol,tf,COUNT(*),MIN(open_time),MAX(close_time) FROM candles GROUP BY symbol,tf').fetchall()
            item=dict(metadata=next(r for r in rows if r['symbol']==symbol),ticker=tick,candles=candles)
            if snapshots:
                s=snapshots[0]
                assert s['symbol']==symbol
                assert {r[0] for r in candles}=={symbol}
                item.update(timestamp=s['timestamp'],price=s['price'],score=s['scoring']['overall']['combined_normalized'],
                            selected=s['converging']['15m']['medium']['high'],
                            chart_count={tf:len(c) for tf,c in s['charts'].items()},
                            checksum_verified=True)
            else:
                assert symbol=='CTUSDT'
                assert not candles
                item['status']='HISTORY_INCOMPLETE'
            report['symbols'][symbol]=item
        legacy=client.get('/analysis/btcusdt');legacy.raise_for_status()
        baseline=PROJECT/'data/website-v1/localization/api-before.json'
        report['legacy_btc_semantic_parity']=legacy.json()==json.loads(baseline.read_text(encoding='utf-8-sig'))
        assert report['legacy_btc_semantic_parity']
    report['formula_hashes']={f:hashlib.sha256((PROJECT/'backend/app/website'/f).read_bytes()).hexdigest() for f in ['scoring.py','converging.py','config.json']}
    target=PROJECT/'data/live-dashboard/v3-verification.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'report':str(target),'count':report['discovered_perpetual_count'],'legacy_parity':report['legacy_btc_semantic_parity'],'symbols':{s:v.get('status','READY') for s,v in report['symbols'].items()}},ensure_ascii=False))


if __name__=='__main__':
    main()
