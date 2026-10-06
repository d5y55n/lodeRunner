"""Write a factual progress snapshot, never a completion or performance claim."""
from datetime import datetime,timezone
import json
import xml.etree.ElementTree as ET
from .phase3_engine import ROOT
from app.market.aggregate_trades import write_json


def snapshot(root=ROOT):
    reports=[]
    for path in sorted((root/"integrity").glob("*.json")):
        if path.name.endswith(("-klines.json","-aggTrades.json")):
            reports.append(json.loads(path.read_text()))
    passed=[r for r in reports if r.get("passed")]
    failed=[r for r in reports if not r.get("passed")]
    aggregates=[r for r in passed if r["kind"]=="aggTrades"]
    coverage_path=root/"coverage-manifest.json"
    coverage=json.loads(coverage_path.read_text()) if coverage_path.exists() else {}
    development=(root/"development/development-completion.json").exists()
    validation=(root/"validation/validation-completion.json").exists()
    frozen=(root/"frozen-validation.json").exists()
    test_path=root/"test-results.xml"
    test=ET.parse(test_path).getroot().find("testsuite").attrib if test_path.exists() else {}
    value=dict(as_of_utc=datetime.now(timezone.utc).isoformat(),phase3_complete=development and validation,
               expected_source_files=72,source_reports=len(reports),passed_source_files=len(passed),
               failed_source_files=len(failed),verified_aggregate_rows=sum(r["rows"] for r in aggregates),
               verified_trade_months=[r["month"] for r in aggregates],
               failed_sources=[dict(month=r["month"],kind=r["kind"],error=r.get("error")) for r in failed],
               development="2021-01-01 <= UTC < 2023-01-01",validation="2023-01-01 <= UTC < 2024-01-01",
               final_test_used=False,full_development_evaluated=development,frozen_validation_evaluated=validation,
               validation_configuration_frozen=frozen,coverage_ready=coverage.get("ready",False),
               coverage_id=coverage.get("coverage_id"),quarantined_minutes=sum((b-a)//60000 for a,b in coverage.get("quarantine_intervals",[])),
               tests=test)
    write_json(root/"research-progress.json",value)
    lines=["# Phase 3 Status","",f"Snapshot UTC: {value['as_of_utc']}","",
           "Development: [2021-01-01, 2023-01-01) UTC. Validation: [2023-01-01, 2024-01-01) UTC.",
           "All 2024 data remains reserved. No live signals or trading execution.","",
           f"Official source groups checked: {len(reports)}/72; passed {len(passed)}, failed {len(failed)}.",
           f"Aggregate rows in passed sources: {value['verified_aggregate_rows']:,}.",
           "Passed trade months: "+", ".join(value["verified_trade_months"]),"",
           "## Coverage Decisions","",
           f"Outcome-blind coverage ready: {value['coverage_ready']}. Trade-volume quarantine: {value['quarantined_minutes']} minutes.",
           "Numerical ID gaps alone do not exclude periods. The active coverage policy and its versions",
           "are documented in PHASE3_COVERAGE_POLICY.md. Consistent ID/boundary warnings are retained.",
           "Invalid monthly publications are preserved and explicitly replaced by verified official daily sources.",
           "Verified candle-based price history remains included through volume-only quarantine.",
           "No trade reconstruction, interpolation or candle-volume substitution.","",
           "## Implemented and Tested","",
           "Monthly archive capture, official checksums, ZIP CRC, integrity checks, raw/derived separation;",
           "trade-derived hourly price profiles; A/B/C volume attachment; D real-volume execution;",
           "stable identities, unique-event counts, causal control index, development-only bucket fitting;",
           "hash-locked validation configuration; separate decision features and future outcomes/lifecycles.","",
           f"Latest test report: {test.get('tests','unavailable')} tests; failures={test.get('failures','unavailable')}, errors={test.get('errors','unavailable')}.","",
           "## Research State","",
           f"Development completion report exists: {development}. Validation configuration frozen: {frozen}.",
           f"Validation completion report exists: {validation}. Final test used: false.",
           "Long-range scope is 1h; other original timeframe mappings are not evaluated in this run.",
           "No edge claim, parameter ranking, live signal or trading execution.","",
           "## Files Added or Updated","",
           "- PROJECT_SPEC.md; docs/research/PHASE3_DESIGN.md; this status report.",
           "- backend/app/market/phase3_archives.py; phase3_gap_audit.py.",
           "- backend/app/market/phase3_coverage.py; phase3_daily_fallback.py; phase3_publication_audit.py.",
           "- backend/app/research/phase3_plan.py; phase3_identity.py; phase3_context.py; phase3_fast.py.",
           "- backend/app/research/phase3_profiles.py; phase3_statistics.py; phase3_engine.py; phase3_status.py.",
           "- backend/app/research/phase3_storage.py; phase3_disk_summary.py; phase3_reports.py.",
           "- backend/tests/test_phase3_foundations.py; test_phase3_acquisition.py; test_phase3_fast.py;",
           "  test_phase3_statistics.py; test_phase3_pipeline.py.","",
           "- backend/tests/test_phase3_coverage.py; test_phase3_publications.py; test_phase3_disk.py.",
           "- backend/pyproject.toml; backend/uv.lock.","",
           "See PHASE3_DESIGN.md and data/phase3/integrity for details."]
    path=root.parents[1]/"docs/research/PHASE3_STATUS.md"
    path.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(value,indent=2))


if __name__=="__main__":snapshot()
