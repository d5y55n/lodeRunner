from pathlib import Path
from app.research.models import identity

HOUR=3600000
DAY=24*HOUR
WIDTHS={'1d':.022,'4h':.007,'1h':.004,'15m':.002}
CANDLE_COUNTS={'1d':850,'4h':5100,'1h':20400,'15m':81600}
LOOKBACK=850*DAY
ROOT=Path(__file__).resolve().parents[3]/'data/phase3r'
SOURCE=ROOT.parent/'phase3'
FINAL_START=1704067200000


def permitted(start,end):
    if not 0<=start<end<=FINAL_START:raise ValueError('No 2024 data access')


def configuration(detector,parameters,timeframe='1h',lookback=LOOKBACK):
    if timeframe not in WIDTHS:raise ValueError('Unsupported timeframe')
    value=dict(symbol='BTCUSDT',timeframe=timeframe,detector=detector,parameters=parameters,
        lookback_ms=lookback,proximity_half_width=WIDTHS[timeframe],schema='full-map-v1',
        candle_window='start>=T-lookback; end<=T; complete dependency span inside window',
        decision_price='last closed candle close',trade_window='[T-lookback,T)',
        C_initialization='reset trackers at rolling left boundary; replay existing C rules',
        clusters='closed +/-width intervals; touching intervals are connected',
        directional_volume_window_ms=HOUR,volume_overlap='union within type; joint union separately',
        D_native_direction='NEUTRAL',price_window_required=True)
    return {**value,'configuration_id':identity(value)}


def state_identity(config,t,price):
    event_id=identity(['full-map-market-event-v1',config['symbol'],config['timeframe'],t])
    return event_id,identity(['full-map-snapshot-v1',config['configuration_id'],t,price])
