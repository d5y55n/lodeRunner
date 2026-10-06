"""Verify real cached prices and current event state without printing credentials."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from app.website.config import PROJECT


def main():
    with httpx.Client(base_url='http://127.0.0.1:8011',timeout=120) as client:
        def get(url,**params):
            r=client.get(url,params=params);r.raise_for_status();return r.json()
        current=get('/dashboard/BTCUSDT/price')
        at=datetime.fromtimestamp(current['timestamp']/1000,timezone.utc).isoformat()
        same=get('/dashboard/BTCUSDT/price',price=str(current['price']),at=at)
        manual=get('/dashboard/BTCUSDT/price',price='70000',at=at)
        assert current['scoring']==same['scoring']
        assert current['converging']==manual['converging']
        assert current['charts']==manual['charts']
        assert current['scoring']!=manual['scoring']
        assert all(current['scoring']['timeframes'][tf]['map_support_count']==manual['scoring']['timeframes'][tf]['map_support_count'] for tf in current['charts'])
        events=get('/events/status')
        assert events['youtube']['channel_id']=='UCZJ9ZukOgTjKcjN9SJQPf7w'
        legacy=get('/analysis/btcusdt')
        baseline=json.loads((PROJECT/'data/website-v1/localization/api-before.json').read_text(encoding='utf-8-sig'))
        assert legacy==baseline
        report=dict(timestamp=current['timestamp'],market_close=current['price'],manual_price=manual['analysis_price'],current_score=current['scoring']['overall'],manual_score=manual['scoring']['overall'],converging_unchanged=True,current_parity=True,legacy_parity=True,events=events)
        path=PROJECT/'data/live-dashboard/v4-verification.json'
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        assert 'calendar' not in events
        print(json.dumps(dict(path=str(path),current_parity=True,converging_unchanged=True,calendar='iframe-only',youtube=events['youtube']['state'],channel_id=events['youtube']['channel_id'])))


if __name__=='__main__':main()
