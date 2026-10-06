# Phase 4 native-clock research

Run commands from `backend` with `.venv/Scripts/python.exe -m`.

1. `app.multimap.data development <15m|4h|1d>` verifies authoritative candles.
2. `app.multimap.gates <timeframe>` verifies parity; 15m also benchmarks 1,000 native timestamps.
3. `app.multimap.profiles gate` checks a deterministic real aggregate-trade sample.
4. `app.multimap.profiles development` streams the required 2022 quarter-hour trade profiles. It can run alongside price-map research, and verifies completed monthly partitions when restarted.
5. `app.multimap.run <timeframe> development` generates one snapshot per native close, compact daily memberships, candidate catalogs, normalized raw geometry and separate outcomes. It refuses to rewrite a completed run. Do not launch a duplicate process against the same output directory.
6. `app.multimap.flow <timeframe> development` requires completed prices and trade profiles, then attaches all predeclared native flow windows.
7. `app.multimap.analyze <timeframe> development` requires complete real flow attachments and exports development-only quartile descriptive tables and deterministic seven-day-block confidence intervals.
8. `app.multimap.audit` verifies frozen prior artifacts without regenerating them.

Replication must not be launched merely because the price stage finished. The development analysis, feature review and verified configuration freeze still need completion. This package intentionally does not auto-create that freeze or auto-start 2023.

Price output: `data/phase4/<timeframe>/<phase>/`.
Trade output: `data/phase4/trade-profiles-15m/`.
Plans, benchmark, parity, coverage, integrity and progress are JSON artifacts.

No function sums scores across timeframes. `contract.latest_closed` only returns a fully closed native state; it does not build a forward-filled research dataset or evaluate confluence.
