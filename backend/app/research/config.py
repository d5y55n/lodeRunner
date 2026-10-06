from dataclasses import dataclass, field
from .interactions import ExitRule
from .zones import ORIGINAL_WIDTHS
from .detectors import make_detector


@dataclass(frozen=True)
class Periods:
    start: int
    research_end: int
    validation_end: int
    test_end: int

    def __post_init__(self):
        if not self.start < self.research_end < self.validation_end < self.test_end:
            raise ValueError("Periods must be strictly chronological")

    def bounds(self, phase):
        if phase == "research":
            return self.start, self.research_end
        if phase == "validation":
            return self.research_end, self.validation_end
        if phase == "test":
            raise ValueError("Final test remains untouched in Phase 2")
        raise ValueError("Unknown research phase")


@dataclass(frozen=True)
class Experiment:
    symbol: str
    timeframe: str
    dataset_id: str
    periods: Periods
    detector: str
    detector_parameters: dict
    width_model: str
    width_parameter: float
    exit_rule: ExitRule = field(default_factory=ExitRule)
    horizons: tuple[int, ...] = (4, 8)
    tp_grid: tuple[float, ...] = (0.003, 0.005)
    sl_grid: tuple[float, ...] = (0.003, 0.005)
    phase: str = "research"
    control_stride: int = 4
    volume_window_ms: int | None = None
    entry_rule: str = "first_interaction_close_then_future_candles"
    engine_version: str = "phase2-v1"

    def __post_init__(self):
        self.periods.bounds(self.phase)
        if not self.symbol or not self.timeframe or not self.dataset_id:
            raise ValueError("Instrument and dataset identity required")
        if self.detector != "D":
            make_detector(self.detector, self.detector_parameters)
        elif set(self.detector_parameters) != {"bin_size", "window_ms", "concentration_multiple"}:
            raise ValueError("D requires bin_size, window_ms, concentration_multiple")
        if self.width_model not in ("fixed_percentage", "original_timeframe"):
            raise ValueError("Adaptive formula has no selected default; use zones extension point")
        if not 0 < self.width_parameter < 1:
            raise ValueError("Invalid zone width")
        if self.width_model == "original_timeframe" and ORIGINAL_WIDTHS.get(self.timeframe) != self.width_parameter:
            raise ValueError("Original timeframe width mismatch")
        if (not self.horizons or any(type(h) is not int or h <= 0 for h in self.horizons)
                or self.control_stride < 1 or (self.volume_window_ms is not None and self.volume_window_ms <= 0)):
            raise ValueError("Invalid horizon, control stride or volume window")
        for grid in (self.tp_grid, self.sl_grid):
            if not grid or any(not 0 < p < 1 for p in grid):
                raise ValueError("Invalid TP/SL grid")
        if self.entry_rule != "first_interaction_close_then_future_candles" or self.engine_version != "phase2-v1":
            raise ValueError("Unsupported entry rule or engine version")
