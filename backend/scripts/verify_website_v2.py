"""Deterministic inspection fixtures, not performance evaluation or strategy mining."""
import hashlib
import json
from pathlib import Path
import urllib.request
from app.website.live import Store, Dashboard
from app.website.config import STEPS, DAY, settings
from app.website import converging

root=Path('../data/live-dashboard')
store=Store();cfg=settings()
status=json.load(urllib.request.urlopen('http://127.0.0.1:8011/market/btcusdt/status'))
t=status['snapshot']['timestamp']
with store.connect() as db:
    coverage=[dict(zip(['tf','count','start','end'],r)) for r in db.execute('SELECT tf,COUNT(*),MIN(open_time),MAX(close_time)+1 FROM candles GROUP BY tf')]
f=store.read('15m',0,t);streams=converging.observations(f,2)
found={}
for j in range(max(0,len(f)-7*96),len(f)):
    for side in ['high','low']:
        r=converging.point(f,streams,2,side,j,cfg)
        category='up' if r.get('state')=='EXTREME' and r.get('actual_direction')=='UP' else 'down' if r.get('state')=='EXTREME' and r.get('actual_direction')=='DOWN' else 'normal' if r.get('state')=='NORMAL' else None
        if category and category not in found:found[category]=(int(f.close_time.iloc[j])+1,side)
        if j>0 and streams[side]['source'][j]!=streams[side]['source'][j-1] and 'reset' not in found:found['reset']=(int(f.close_time.iloc[j])+1,side)
    if len(found)==4:break
d=Dashboard(store=store,cfg=cfg)
cases={}
for label,(stamp,side) in found.items():
    s=d.replay(stamp);r=s['converging']['15m']['short'][side]
    assert r['known_at']<=stamp and max(x['close_time'] for x in s['charts']['15m'])<stamp
    if label in ['up','down']:assert r['state']=='EXTREME' and r['actual_direction']==label.upper()
    if label=='reset':assert r['velocity'] is None and r['acceleration'] is None
    if label=='normal':assert r['state']=='NORMAL'
    cases[label]={'timestamp':stamp,'side':side,'row':r,'price':s['price'],'scoring':s['scoring']['overall']}
d.stop()
before=Path('../data/website-v1/localization/api-before.json').read_bytes()
after=urllib.request.urlopen('http://127.0.0.1:8011/analysis/btcusdt',timeout=120).read()
assert before==after
report=dict(coverage=coverage,cases=cases,v1_exact_response_parity=True,
            rule='First matching 15m N2 high then low observation in chronological order over the last seven cached days. No future outcomes inspected.',
            formula_hashes={p:hashlib.sha256(Path('app/website',p).read_bytes()).hexdigest() for p in ['scoring.py','converging.py','config.json']})
(root/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'coverage':coverage,'cases':{k:{'timestamp':v['timestamp'],'side':v['side'],'percentile':v['row']['percentile']} for k,v in cases.items()}},indent=2))
