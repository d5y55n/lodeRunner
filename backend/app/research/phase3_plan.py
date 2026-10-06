from datetime import datetime,timezone
from .models import identity


def utc(value):
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp()*1000)


DEVELOPMENT_START = utc("2021-01-01")
DEVELOPMENT_END = utc("2023-01-01")
VALIDATION_END = utc("2024-01-01")
FINAL_TEST_START = VALIDATION_END


def permitted(start,end):
    if not DEVELOPMENT_START <= start < end <= FINAL_TEST_START:
        raise ValueError("Only 2021-2023 data permitted; all 2024 data is reserved")


def manifest():
    value = {"schema":"phase3-v1","symbol":"BTCUSDT","development_start":DEVELOPMENT_START,
             "development_end":DEVELOPMENT_END,"validation_end":VALIDATION_END,
             "final_test_start":FINAL_TEST_START,"timeframe":"1h",
             "fixed_half_widths":[0.0005,0.001,0.002,0.003,0.005],"original_half_width":0.004,
             "B_widths":[1,2],"C_reversals":[0.003,0.005],"D_bin_widths":[50,100],
             "D_concentration":1.5,"D_window_ms":3600000,"horizons":[4,8,24],
             "tp":[0.003,0.005],"sl":[0.003,0.005],"volume_window_ms":3600000,
             "context_lookback":24,"schedule_stride":4,"quantile_groups":4,
             "validation_policy":"freeze_development_subset_then_single_evaluation"}
    return {**value,"plan_id":identity(value)}
