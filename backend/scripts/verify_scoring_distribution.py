"""Offline verification against real operational candles; no archive/network writes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
from app.website.live import Store
from app.website.config import settings, PROJECT
from app.website.scoring_distribution import attach, samples
from app.website import scoring
from app.website.config import STEPS

out=[]
for symbol in ['BTCUSDT','ETHUSDT','SOLUSDT']:
    store=Store(symbol=symbol)
    snapshot=store.history(1)[0]
    result=attach(snapshot,store,settings())
    assert result['scoring']==snapshot['scoring']
    assert result['converging']==snapshot['converging']
    cfg=settings()
    rows,_=samples(store,cfg,snapshot['timestamp'])
    for ts,value in rows[-2:]:
        frames={tf:store.read(tf,0,ts) for tf in STEPS}
        price=float(frames['15m'].close.iloc[-1])
        expected=scoring.combine({tf:scoring.score(f,tf,price,ts,cfg) for tf,f in frames.items()},cfg)
        assert abs(value-expected['combined_normalized'])<1e-14
    r=result['scoring_percentile']
    out.append(dict(timestamp=snapshot['timestamp'],**r))
    print(json.dumps({k:out[-1][k] for k in ['symbol','timestamp','observation_score','direction','percentile','sample_count','coverage_start','coverage_end','statistics']},ensure_ascii=False),flush=True)
assert len({r['distribution_key'] for r in out})==3
(PROJECT/'data/live-dashboard/scoring-percentile-verification.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
