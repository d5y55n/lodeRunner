"""Fixed first research-day real-trade sanity run; no ranking or test evaluation."""
import argparse
from dataclasses import asdict
from pathlib import Path
import json
import math
import pandas as pd
from app.market.aggregate_trades import acquire_days,sha256,write_json
from app.market.models import Candle as MarketCandle
from .data import from_market
from .models import canonical
from .runner import code_digest
from .volume import Trade,TradeIndex
from .sanity_export import build_exports,write_exports


ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"data/research/phase25")
    parser.add_argument("--replay",action="store_true",help="Reuse verified local source and normalized data")
    args = parser.parse_args()
    normalized = ROOT/"data/processed/aggTrades"
    if not args.replay:
        manifest = acquire_days("2024-01-01","2024-01-02",ROOT/"data/raw/binance/aggTrades",normalized)
    else:
        manifest = json.loads((normalized/"range-integrity.json").read_text())
    start,end = 1704067200000,1704153600000
    if (manifest["start"],manifest["end"],manifest["passed"]) != (start,end,True):
        raise ValueError("Unexpected source range or failed integrity")
    for source in manifest["days"]:
        if sha256(ROOT/"data/raw/binance/aggTrades"/source["archive"]) != source["sha256"]:
            raise ValueError("Raw source changed since integrity inspection")
    trades = []
    for file in manifest["normalized"]:
        path = normalized/file["file"]
        if sha256(path) != file["sha256"]:
            raise ValueError("Normalized dataset checksum changed")
        frame = pd.read_parquet(path)
        trades.extend(Trade(**record) for record in frame.to_dict(orient="records"))
    del frame
    indexed = TradeIndex(trades)
    source = ROOT/"data/research/phase2-smoke/BTCUSDT_1h_2024-01-01_2024-01-08.csv"
    # Filter at ingestion: no validation/test candle enters a detector or label engine.
    frame = pd.read_csv(source)
    frame = frame[(frame.open_time >= start)&(frame.close_time < end)]
    market = [MarketCandle(**r) for r in frame.to_dict(orient="records")]
    candles = from_market(market,"BTCUSDT","1h")
    reconciliation = []
    for c in market:
        quantity = math.fsum(t.quantity for t in indexed.window(c.open_time,c.close_time+1))
        reconciliation.append({"open_time":c.open_time,"aggregate_quantity":quantity,
                               "kline_quantity":c.volume,"difference":quantity-c.volume})
    plan = {"schema":"phase25-v1","symbol":"BTCUSDT","timeframe":"1h","start":start,"end":end,
            "original_research_end":1704427200000,"reserved_final_test_start":1704549600000,
            "sampling_period":"first UTC day of approved Phase 2 research period; fixed before execution",
            "detectors":[{"detector":"A","parameters":{}},{"detector":"B","parameters":{"width":1}},
                         {"detector":"C","parameters":{"reversal_fraction":0.003}},
                         *[{"detector":"D","parameters":{"bin_size":b,"window_ms":3600000,
                             "concentration_multiple":1.5}} for b in (50,100)]],
            "zone_half_width":0.002,"exit_rule":{"model":"boundary","separation_fraction":0.0},
            "volume_window_ms":3600000,"bin_sizes":[50,100],"tp_grid":[0.003],"sl_grid":[0.003],"horizons":[4],
            "source_archives":[{"file":d["archive"],"sha256":d["sha256"]} for d in manifest["days"]],
            "code_sha256":code_digest(),"candle_source_sha256":sha256(source),
            "html_template_sha256":sha256(Path(__file__).with_name("sanity_template.html")),
            "availability_model":"Historical event-time replay; trades with timestamp strictly before decision time; no receipt-latency reconstruction"}
    print("Building real-trade features and inspection exports...",flush=True)
    bundle = build_exports(candles,indexed,plan)
    hashes = write_exports(bundle,args.output)
    repeat = build_exports(candles,indexed,plan)
    if canonical(bundle) != canonical(repeat):
        raise AssertionError("Export contents are not reproducible")
    if hashes != write_exports(repeat,args.output):
        raise AssertionError("Export file bytes are not reproducible")
    report = {**bundle["summary"],"sample":bundle["sample"],"trade_count":len(indexed),
              "integrity":manifest,"export_reproducible":True,"export_hashes":hashes,
              "quantity_reconciliation":reconciliation,
              "max_abs_hourly_quantity_difference":max(abs(r["difference"]) for r in reconciliation)}
    write_json(args.output/"run-report.json",report)
    print(json.dumps({k:v for k,v in report.items() if k not in ("integrity","export_hashes","sample","quantity_reconciliation")},indent=2))


if __name__ == "__main__":
    main()
