import json
from pathlib import Path
from bisect import bisect_right
from app.research.models import validate_candles,identity
from app.fullmap.contract import HOUR,LOOKBACK,FINAL_START,WIDTHS
from app.market.aggregate_trades import sha256,write_json

PROJECT=Path(__file__).resolve().parents[3]
ROOT=PROJECT/'data/phase4'
STEPS={'15m':HOUR//4,'1h':HOUR,'4h':4*HOUR,'1d':24*HOUR}
FLOW_CANDLES={'15m':[1,4,8],'4h':[1,2,4],'1d':[1,2,4]}
HORIZONS={'15m':[16,32,96],'4h':[1,2,6],'1d':[1,2,3]}
CONFIGS=[('A',{}),('B',{'width':1}),('B',{'width':2}),('C',{'reversal_fraction':.003}),('C',{'reversal_fraction':.005})]
PLAN=dict(version='phase4-native-v1',timeframes=['15m','4h','1d'],steps=STEPS,widths=WIDTHS,
    lookback_ms=LOOKBACK,flow_native_candles=FLOW_CANDLES,outcome_native_candles=HORIZONS,
    tp_sl=[.003,.005],daily_role='structural/context; native horizons 24/48/72h, not 4h entry timing',
    decision='one fully closed native candle at a time; UTC exchange alignment; no forward fill',
    groups='development-only quartiles per timeframe/config; no cross-timeframe score normalization',
    flow='current-T side unions; strictly [T-duration,T); missing granularity never approximated',
    statistics='all grids and UTC quarters; shared seven-day UTC block resampling, 1000 draws, seed 4101',
    replication='previously inspected replication period',no_2024=True,no_confluence=True,no_score_sum=True)

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def permitted(start,end):
    if not 0<=start<end<=FINAL_START:raise ValueError('2024 market access forbidden')

class Clock:
    def __init__(self,candles,timeframe,lookback=LOOKBACK):
        self.step=STEPS[timeframe];self.cs=candles;self.lookback=lookback
        if not candles or lookback<=0 or lookback%self.step:raise ValueError('Invalid native window')
        validate_candles(candles);permitted(candles[0].start,candles[-1].end)
        if any(c.start%self.step or c.end-c.start!=self.step for c in candles):raise ValueError('Non-native candle alignment')
        self.ends=[c.end for c in candles]
    def window(self,t):
        if t%self.step or t>=FINAL_START:raise ValueError('Not an eligible native close')
        right=bisect_right(self.ends,t);left=right-self.lookback//self.step
        if left<0 or right==0 or self.ends[right-1]!=t or self.cs[left].start!=t-self.lookback:
            raise ValueError('INSUFFICIENT_COMPLETE_850_DAY_HISTORY')
        return self.cs[left:right]

def latest_closed(rows,t):
    """Alignment lookup only. No join, score aggregation, or performance evaluation."""
    if t>=FINAL_START:raise ValueError('2024 forbidden')
    times=[r['last_closed_candle_end'] for r in rows]
    if times!=sorted(set(times)):raise ValueError('Sorted unique native states required')
    if any(r['decision_timestamp']!=r['last_closed_candle_end'] for r in rows):raise ValueError('Unfinished or delayed state')
    i=bisect_right(times,t)-1
    return rows[i] if i>=0 else None

def initialize():
    ROOT.mkdir(exist_ok=True)
    if (ROOT/'plan.json').exists():
        if read(ROOT/'plan.json')!=PLAN:raise ValueError('Plan changed')
        return
    files=[]
    for phase in ['phase3r','phase3r1','phase3r2']:
        for p in (PROJECT/'data'/phase).rglob('*'):
            if p.is_file() and not any(s in p.parts for s in ['raw','profiles','derived','warmup','history']):files.append(p)
    for name in ['fullmap','fullmap_scale','fullmap_flow']:
        files.extend(p for p in (Path(__file__).parent.parent/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.extend(PROJECT.glob('PHASE3R*.md'))
    write_json(ROOT/'preserved-before.json',{str(p.relative_to(PROJECT)):sha256(p) for p in sorted(set(files))})
    write_json(ROOT/'plan.json',PLAN)
