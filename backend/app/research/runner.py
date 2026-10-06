from collections import Counter
from dataclasses import asdict
from itertools import product
from pathlib import Path
from .models import canonical, identity, validate_candles
from .detectors import make_detector
from .zones import construct
from .interactions import track
from .outcomes import measure
from .volume import VolumeConcentration, zone_features, validate_trades


def code_digest():
    return identity({p.name: p.read_text(encoding="utf-8") for p in sorted(Path(__file__).parent.glob("*.py"))})


def compare(rows):
    """Descriptive comparison only. No ranking, confidence claim or optimization."""
    groups = {}
    for row in rows:
        o = row["outcome"]
        key = (o["direction"], o["tp"], o["sl"], o["horizon"])
        group = groups.setdefault(key, {"event": [], "control": []})
        group[row["group"]].append(o)
    results = []
    for key, groups_for_key in sorted(groups.items()):
        item = dict(zip(("direction", "tp", "sl", "horizon"), key))
        for group, outcomes in groups_for_key.items():
            complete = [o for o in outcomes if not o["censored"]]
            counts = dict(sorted(Counter(o["label"] for o in complete).items()))
            item[group] = {"total": len(outcomes), "complete": len(complete),
                           "censored": len(outcomes)-len(complete), "labels": counts,
                           "tp_first_fraction": counts.get("TP_FIRST", 0)/len(complete) if complete else None}
        a, b = item["event"]["tp_first_fraction"], item["control"]["tp_first_fraction"]
        item["descriptive_tp_fraction_difference"] = a-b if a is not None and b is not None else None
        results.append(item)
    return results


def run(candles, config, trades=None, trade_coverage=None):
    validate_candles(candles)
    start, end = config.periods.bounds(config.phase)
    # Independent split reset: even candidate confirmation and outcomes stay inside the split.
    selected = [c for c in candles if c.start >= start and c.end <= end]
    if not selected:
        raise ValueError("No closed candles in selected period")
    if selected[0].start != start or selected[-1].end != end:
        raise ValueError("Dataset must cover the complete selected period")
    if trades is not None:
        validate_trades(trades)
        if trade_coverage is None:
            raise ValueError("Trade acquisition coverage is required")
        if any(not trade_coverage[0] <= t.timestamp < trade_coverage[1] for t in trades):
            raise ValueError("Trades outside declared coverage")
    if config.detector == "D":
        if trades is None or trade_coverage[0] > start or trade_coverage[1] < end:
            raise ValueError("D needs complete trade-level coverage of the selected period")
        detector = VolumeConcentration(trades, start=start, **config.detector_parameters)
    else:
        detector = make_detector(config.detector, config.detector_parameters)
    candidates = detector.detect(selected, config.timeframe, end)
    zones = [construct(c, config.width_model, config.width_parameter) for c in candidates]
    interactions, rows = [], []
    for z in zones:
        visits = track(z, selected, config.exit_rule)
        interactions.extend(asdict(v) for v in visits)
        for v in visits:
            features = {"status": "NOT_REQUESTED"}
            if config.volume_window_ms is not None:
                features = ({"status": "MISSING_TRADE_DATA"} if trades is None else
                            zone_features(z, trades, v.observed_at, config.volume_window_ms,
                                          max(start, trade_coverage[0]), min(end, trade_coverage[1])))
            rows.extend(label_rows(v.entry_price, v.observed_at, selected, config, "event",
                                   {"zone_id": z.id, "interaction_number": v.number,
                                    "volume_features": features}))
    # Fixed clock schedule is determined independently of S/R and subsequent price moves.
    for c in selected[::config.control_stride]:
        rows.extend(label_rows(c.close, c.end, selected, config, "control",
                               {"candle_id": c.id}))
    manifest = {"config": asdict(config), "code_sha256": code_digest(),
                "candle_sha256": identity([asdict(c) for c in selected]),
                "trade_sha256": identity([asdict(t) for t in trades]) if trades is not None else None,
                "trade_coverage": trade_coverage,
                "selected_start": start, "selected_end": end,
                "control": "fixed_stride_same_market_split_and_close_entry",
                "split_policy": "reset_and_truncate_no_cross_boundary_outcomes"}
    return {"experiment_id": identity(manifest), "manifest": manifest,
            "candidates": [{"id": c.id, **asdict(c)} for c in candidates],
            "zones": [{"id": z.id, **asdict(z)} for z in zones],
            "interactions": interactions, "measurements": rows,
            "comparison": compare(rows),
            "limitations": ["Descriptive only; controls are not regime-matched.",
                            "Zones and overlapping horizons are correlated, not independent samples.",
                            "Interaction completion facts are not entry-time features.",
                            "No intrabar fill model, transaction costs, optimization or edge claim."]}


def label_rows(price, timestamp, candles, config, group, context):
    for direction, tp, sl, horizon in product(("LONG", "SHORT"), config.tp_grid,
                                             config.sl_grid, config.horizons):
        yield {"group": group, "observed_at": timestamp, "entry_price": price, **context,
               "outcome": asdict(measure(price, timestamp, candles, direction, tp, sl, horizon))}


def run_grid(candles, configurations, **kwargs):
    # Enumeration only. Intentionally no objective function or best-parameter selection.
    return [run(candles, config, **kwargs) for config in configurations]
