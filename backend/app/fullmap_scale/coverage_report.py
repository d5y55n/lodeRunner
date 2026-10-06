"""Finalize availability evidence separately from strategy outcomes."""
import json
import pandas as pd
from app.market.aggregate_trades import write_json,sha256
from app.fullmap.contract import HOUR,LOOKBACK
from app.research.phase3_engine import load_coverage
from .history import ROOT,HISTORY,SOURCE,load_prices


def main():
    earlier=json.loads((ROOT/'availability.json').read_text());trade=json.loads((HISTORY/'trade-coverage.json').read_text())
    if not trade['ready']:raise ValueError('Trade coverage unresolved')
    cs=load_prices();old=load_coverage(SOURCE);bad=sorted(trade['quarantine_intervals']+old['quarantine_intervals'])
    first=earlier['earliest_archived_trade_day']+LOOKBACK
    complete=[t for t in range(first,1704067200000,HOUR) if not any(a<t and b>t-LOOKBACK for a,b in bad)]
    result=dict(earlier,status='COVERAGE_VERIFIED',trade_window_completeness_not_yet_verified=False,
        earliest_authoritative_price=cs[0].start,earliest_850_day_price=cs[0].start+LOOKBACK,
        additional_aggregate_rows=trade['aggregate_rows'],new_quarantines=trade['quarantine_intervals'],
        all_known_quarantines=bad,earliest_complete_850_day_trade_window_before_2024=complete[0] if complete else None,
        count_complete_850_day_trade_windows_before_2024=len(complete),trade_coverage_sha256=sha256(HISTORY/'trade-coverage.json'),
        development_evaluation_start=cs[0].start+LOOKBACK,development_end_exclusive=1672531200000,
        development_timestamps=(1672531200000-cs[0].start-LOOKBACK)//HOUR,replication_timestamps=8760,
        rest_checksum_note='Official REST has no published checksum. Exact responses and local SHA-256 retained; 2019-12-31 overlapping official ZIP is identical.',
        volume_history_status='Complete temporal publication coverage is distinct from complete observed trade coverage; all pre-2024 eligible D windows intersect quarantine')
    write_json(ROOT/'coverage-final.json',result)
    print('COVERAGE_FINAL',pd.Timestamp(result['development_evaluation_start'],unit='ms',tz='UTC'),len(complete),flush=True)


if __name__=='__main__':main()
