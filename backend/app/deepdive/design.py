from pathlib import Path
from app.research.models import identity
from app.research.phase3_plan import DEVELOPMENT_START, DEVELOPMENT_END, VALIDATION_END

ROOT = Path(__file__).resolve().parents[3] / 'data/phase35'
SOURCE = ROOT.parent / 'phase3'


def guard(start, end):
    if not DEVELOPMENT_START <= start < end <= VALIDATION_END:
        raise ValueError('Phase 3.5 permits only 2021-2023; no 2024 access')


def design():
    value = dict(schema='phase35-v1', symbol='BTCUSDT', timeframe='1h', detector='A',
        development=[DEVELOPMENT_START, DEVELOPMENT_END], replication=[DEVELOPMENT_END, VALIDATION_END],
        replication_label='previously inspected replication period',
        percentile='strictly earlier decision times, midrank, event-balanced ECDF per width',
        percentile_sensitivity='row-weighted expanding ECDF and frozen legacy Phase 3 quartiles',
        replication_percentile='fixed complete-development ECDF; no 2023 update',
        minimum_history_rows=100, ventile_minimum_unique_events=100,
        normalized_delta='(buy-sell)/quantity; null for zero quantity', near_zero_abs_ratio=.05,
        sign_sensitivity_abs_ratio=[0., .01, .05, .10], normalized_edges=[-1+i*.2 for i in range(11)],
        rolling_windows=[[i/100, (i+20)/100] for i in range(0,81,5)],
        temporal_blocks='calendar UTC quarters', context_fit_end=1612137600000,
        context='January 2021 volatility Q1/Q3; return neutral = January absolute-return Q25',
        calibration_context='unavailable before fit end; price context itself remains causal',
        controls='nearest earlier A event, same width/kind/facet and causal regime cell; full horizon elapsed',
        dependence='collapse same-time geometry within subgroup; compare row-weighted and event-balanced',
        uncertainty='no naive confidence intervals or significance claims',
        rule_selection=False, live_trading=False, final_test=False)
    return {**value, 'design_id': identity(value)}


def code_hash():
    return identity({p.name:p.read_text(encoding='utf-8') for p in sorted(Path(__file__).parent.glob('*.py'))})
