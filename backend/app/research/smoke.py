"""Small, reproducible BTCUSDT experiment. No parameter selection or final test."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pandas as pd
from app.market.binance_client import BinanceFuturesClient
from app.market.data_service import HistoricalMarketDataService
from app.market.models import BinanceKlinesQuery, Candle as MarketCandle
from .config import Experiment, Periods
from .data import from_market
from .detectors import make_detector
from .interactions import ExitRule
from .models import canonical, identity
from .runner import run_grid
from .zones import FIXED_WIDTHS, ORIGINAL_WIDTHS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset",type=Path,help="Existing Phase 1 Parquet or CSV (no download)")
    parser.add_argument("--output",type=Path,default=Path("../data/research/phase2-smoke"))
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    if args.dataset:
        source = args.dataset
        frame = pd.read_parquet(source) if source.suffix == ".parquet" else pd.read_csv(source)
        market = [MarketCandle(**row) for row in frame.to_dict(orient="records")]
    else:
        # Fixed historical slice: downloading is independent from experiment execution.
        client = BinanceFuturesClient()
        try:
            result = HistoricalMarketDataService(client).download_klines(BinanceKlinesQuery(
                symbol="BTCUSDT",interval="1h",start_time=1704067200000,
                end_time=1704671999999,fail_on_gaps=True))
        finally:
            client.close()
        market = result.candles
        source = args.output / "BTCUSDT_1h_2024-01-01_2024-01-08.csv"
        pd.DataFrame([c.model_dump() for c in market]).to_csv(source,index=False)
    candles = from_market(market,"BTCUSDT","1h")
    if len(candles) < 20:
        raise ValueError("Smoke needs at least 20 closed hourly candles")
    if candles[-1].end > int(datetime.now(timezone.utc).timestamp()*1000):
        raise ValueError("Dataset contains unfinished/future candles")
    n = len(candles)
    periods = Periods(candles[0].start,candles[int(n*0.6)].start,
                      candles[int(n*0.8)].start,candles[-1].end)
    dataset_id = "BTCUSDT:1h:" + hashlib.sha256(source.read_bytes()).hexdigest()
    configs = []
    for name,params in [("A",{}),("B",{"width":1}),("B",{"width":2}),
                        ("C",{"reversal_fraction":0.003}),("C",{"reversal_fraction":0.005})]:
        widths = [("fixed_percentage",w) for w in FIXED_WIDTHS] if name == "A" else [("fixed_percentage",0.002)]
        if name == "A":
            widths.append(("original_timeframe",ORIGINAL_WIDTHS["1h"]))
        for model,width in widths:
            for rule in (ExitRule(),ExitRule("confirmed",0.001)):
                configs.append(Experiment("BTCUSDT","1h",dataset_id,periods,name,params,
                                          model,width,exit_rule=rule))
    results = run_grid(candles,configs)
    repeat = run_grid(candles,configs)
    assert canonical(results) == canonical(repeat), "Non-reproducible results"
    summary = []
    for config,result in zip(configs,results):
        selected = [c for c in candles if periods.start <= c.start and c.end <= periods.research_end]
        detector = make_detector(config.detector,config.detector_parameters)
        final = detector.detect(selected,"1h",periods.research_end)
        for i,c in enumerate(selected):
            assert detector.detect(selected[:i+1],"1h",c.end) == [e for e in final if e.known_at <= c.end]
        zones = {z["id"]:z for z in result["zones"]}
        for v in result["interactions"]:
            assert v["start"] >= zones[v["zone_id"]]["candidate"]["known_at"]
        for zone_id in zones:
            visits = [v for v in result["interactions"] if v["zone_id"] == zone_id]
            assert [v["number"] for v in visits] == list(range(1,len(visits)+1))
            assert all(a["end"] is not None and b["start"] >= a["end"] for a,b in zip(visits,visits[1:]))
        summary.append({"experiment_id":result["experiment_id"],"detector":config.detector,
                        "parameters":config.detector_parameters,"width_model":config.width_model,
                        "width":config.width_parameter,"exit_rule":asdict(config.exit_rule),
                        "candidates":len(result["candidates"]),"zones":len(result["zones"]),
                        "interactions":len(result["interactions"]),
                        "measurement_rows":len(result["measurements"])})
    payload = canonical(results)
    (args.output/"experiments.json").write_text(payload,encoding="utf-8")
    report = {"dataset":str(source.resolve()),"dataset_id":dataset_id,"candles":len(candles),
              "periods":asdict(periods),"reproducible":True,"prefix_causality_checked":True,
              "nonoverlapping_visits_checked":True,"final_test_used":False,
              "results_sha256":identity(results),"experiments":summary,
              "D_status":"Synthetic trade tests only; historical aggregate-trade acquisition pending"}
    (args.output/"summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
