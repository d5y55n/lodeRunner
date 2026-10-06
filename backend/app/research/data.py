"""Bridge Phase 1 candles to research's exclusive-end clock."""
from .models import Candle, validate_candles
from app.market.data_service import validate_candle_sequence


def from_market(candles, symbol, timeframe):
    gaps = validate_candle_sequence(candles, timeframe)
    if gaps:
        raise ValueError("Research cannot bridge missing candles")
    result = [Candle(f"{symbol}:{timeframe}:{c.open_time}", c.open_time, c.close_time+1,
                     c.open, c.high, c.low, c.close) for c in candles]
    validate_candles(result)
    return result
