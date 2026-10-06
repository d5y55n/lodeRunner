# Phase 5: derived confluence research

This package reads frozen native Detector A maps, memberships and existing 15m
outcomes. It never modifies prior packages or datasets and does not fetch data.

From `backend`, use `.venv/Scripts/python.exe -m app.confluence.pipeline`.
Use `--development-only` to stop before review/freeze and any replication reads.
Set `OPENBLAS_NUM_THREADS=1` for reproducible bounded matrix-work concurrency.
Do not run duplicate pipelines. Status and logs live under `data/phase5`.

Definitions are in `contract.py` and `PHASE5_CONFLUENCE_CONTRACT.md`.
After all development analysis and the full test suite, the pipeline freezes
the code, complete development artifacts, buckets and contract report. Any
change makes the replication gate fail. The source reader allows only the
requested phase directories and refuses 2024 paths.

Per-phase artifacts:

- `native`: normalized native snapshots with exact candidate intervals/indexes.
- `states`: common closed-15m decisions with four source IDs/ages and unions.
- `overlaps`: all subset/component price intersections and participant counts.
- `analysis`: all planned categories including empty ones, all outcome grids,
  UTC quarters, paired block-bootstrap contrasts and native magnitude vectors.
- `source-hashes.json`: read-only input provenance.
- `outcome-reuse.json`: existing labels joined by exact event and timestamp.

No score summation, Delta-based direction, optimizer, live rule, leverage,
2024 analysis, B/C confluence or automatic winner selection exists here.
