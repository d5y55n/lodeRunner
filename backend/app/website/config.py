import json
import os
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, model_validator

STEPS = {"15m": 900000, "1h": 3600000, "4h": 14400000, "1d": 86400000}
DAY = 86400000
PROJECT = Path(__file__).resolve().parents[3]


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    scoring_version: str
    converging_version: str
    history_days: int = Field(gt=0, le=3000)
    half_life_days: float = Field(gt=0)
    recency_floor: float = Field(ge=0, le=1)
    outer_multiplier: float = Field(ge=1)
    widths: dict[str, float]
    tf_weights: dict[str, float]
    balanced_band: float = Field(ge=0, lt=1)
    swing_ns: dict[str, int]
    converging_history_days: int = Field(gt=0, le=3000)
    percentile_bands: list[float]
    diagnostic_horizons: list[int]
    min_distribution_samples: int = Field(ge=1)
    chart_candles: int = Field(ge=20, le=2000)
    replay_default: str

    @model_validator(mode="after")
    def validate_maps(self):
        if set(self.widths) != set(STEPS) or set(self.tf_weights) != set(STEPS):
            raise ValueError("All four native timeframes required")
        if not all(0 < v < 1 for v in self.widths.values()):
            raise ValueError("Invalid widths")
        if not all(v > 0 for v in self.tf_weights.values()):
            raise ValueError("Weights must be positive")
        if set(self.swing_ns) != {"short", "medium", "long"} or not all(1 <= n <= 100 for n in self.swing_ns.values()):
            raise ValueError("Three named swing scales required")
        if len(self.percentile_bands) != 3 or not 0 < self.percentile_bands[0] < self.percentile_bands[1] < self.percentile_bands[2] < 100:
            raise ValueError("Three increasing display bands required")
        if not self.diagnostic_horizons or not all(0 < h <= 1000 for h in self.diagnostic_horizons):
            raise ValueError("Positive diagnostic horizons required")
        return self


def settings():
    path = Path(os.environ.get("ANALYSIS_CONFIG", Path(__file__).with_name("config.json")))
    return Settings(**json.loads(path.read_text(encoding="utf-8")))
