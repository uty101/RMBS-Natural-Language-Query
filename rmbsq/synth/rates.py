"""Cash rate path (kickoff 4.4). Built in step 1.2."""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmbsq.config import Config, load_cash_steps
from rmbsq.synth.months import month_index, month_range, to_period


def cash_rate_by_month(cfg: Config) -> tuple[np.ndarray, np.ndarray]:
    """(int months sim_start..window_end, rate), each step held until the next change."""
    steps = load_cash_steps(cfg.table_path("cash_rate"))
    starts = np.array([month_index(p) for p in steps["period"]])
    months = month_range(cfg.calendar.sim_start, cfg.calendar.window_end)
    idx = np.searchsorted(starts, months, side="right") - 1
    if (idx < 0).any():
        raise ValueError("cash rate table starts after sim_start")
    return months, steps["rate"].to_numpy()[idx]


def build_cash_rate(cfg: Config) -> pd.DataFrame:
    """Monthly period (first of month) and rate, 2016-01 to 2026-09."""
    months, rate = cash_rate_by_month(cfg)
    return pd.DataFrame({"period": to_period(months), "rate": rate})
