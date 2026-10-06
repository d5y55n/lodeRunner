# SR Probability Trading Platform

## Scoring + Converging Website v1

Run `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8011`
from `backend`, then open http://127.0.0.1:8011. Default: real BTC 2023 replay,
not live prices. Independent WHERE / HOW FAST axes, inspectable formulas and
responsive candlestick UI. See [website documentation](docs/WEBSITE_V1.md) and
[implementation summary](IMPLEMENTATION_SUMMARY.md). Reserved 2024 requests are
blocked; do not use older historical research commands below for this website.

Phase 1 implements the historical Binance USD-M Futures market data pipeline for BTCUSDT and other public symbols/intervals. It includes a FastAPI app, normalized candle validation, pagination, local dataset saving, and deterministic tests.

Phase 2 adds the independent A/B/C/D S/R candidate research engine under
`backend/app/research/`. It has no signals, scores, ML or execution. Exact
algorithms, data requirements and measurement conventions are documented in
[`docs/research/PHASE2.md`](docs/research/PHASE2.md).

## Phase 2.5 real aggregate trades and offline inspection

```powershell
cd backend
uv run python -m app.market.aggregate_trades --start 2024-01-01 --end 2024-01-02
uv run python -m app.research.phase25 --replay
uv run pytest
```

Dates are UTC and end is exclusive. The fixed sanity run uses only the first
research day. Without `--replay`, phase25 also acquires/verifies the source archive.
Raw ZIP/checksum/integrity reports live in `data/raw/binance/aggTrades/`;
normalized Parquet and range integrity in `data/processed/aggTrades/`.
Derived files live in `data/research/phase25/`. Open `sanity.html` locally; it needs
no server, internet, CDN or production frontend. Read `docs/research/PHASE25.md`
for the exact sampling/volume rules, files and unresolved integrity warnings.

`decision_features.*` contains past-only features; `outcomes_future.*` contains
future labels; `interactions_retrospective.*` contains completed-visit facts.
Never join future labels back into creation-time features. `run-report.json`
records counts, provenance, reproducibility and hourly quantity reconciliation.

## Phase 2 smoke experiment (existing)

```powershell
cd backend
uv run python -m app.research.smoke
uv run pytest
```

The smoke downloads 168 closed BTCUSDT hourly candles from 2024-01-01 through
2024-01-07 UTC. It evaluates 20 small research configurations, checks every
candidate prefix for causality, checks non-overlapping visits per zone, and runs
twice to verify identical outputs. Validation and final-test slices are reserved;
only the first 100 candles are analyzed. No parameter is selected.

Replay the saved dataset without a network request:

```powershell
uv run python -m app.research.smoke --dataset ../data/research/phase2-smoke/BTCUSDT_1h_2024-01-01_2024-01-08.csv
```

Outputs: `data/research/phase2-smoke/summary.json`, `experiments.json`, and CSV.
To use the existing Windows environment directly, replace `uv run python` with
`.venv\Scripts\python.exe`, and run `.venv\Scripts\python.exe -m pytest`.

The Python `run_grid` API accepts explicit `Experiment` configurations for other
detector widths/reversals, TP/SL grids, horizons and split dates. Detector D and
zone-volume features accept normalized `Trade` objects plus coverage metadata;
the smoke never substitutes candle volume for missing historical trades.

## Phase 1 scope

- Python backend with `uv`
- FastAPI app with `/health`
- Binance public Futures kline client
- Candle normalization and integrity validation
- Pagination with duplicate handling
- Missing-candle detection
- Local dataset saving to Parquet or CSV
- Tests for the data layer and API

## Requirements

- Python 3.12+
- `uv`

## Setup

```bash
cd backend
uv sync
```

## Run the API

```bash
cd backend
uv run fastapi dev app/main.py
```

The API will expose:

- `GET /health`
- `GET /market/binance/klines`

## Run tests

```bash
cd backend
uv run pytest
```

## Verify a small BTCUSDT historical download

```bash
cd backend
uv run python -m app.market.data_service --symbol BTCUSDT --interval 1h --start-time 1704067200000 --end-time 1704153600000 --save-format parquet
```

The command downloads a small closed-candle historical slice, validates it, reports any gaps, and saves the dataset under `../data/raw/binance/`.

## API example

```bash
curl "http://127.0.0.1:8000/market/binance/klines?symbol=BTCUSDT&interval=1h&start_time=1704067200000&end_time=1704153600000&save=true"
```

## Notes

- Internally, timestamps are stored as UTC millisecond integers.
- Prices and volumes are normalized to `float64`-compatible Python floats.
- Missing candles are reported and never silently ignored.
- Duplicate candle timestamps are removed deterministically by keeping the last occurrence after chronological sorting.
