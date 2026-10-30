"""Suburb house price indices (kickoff 4.5). Built in step 1.2.

Instruction 01 D.1: 1 draw `rng.standard_normal((60, 128))`, rows suburbs in geography
order, columns months 2016-02 to 2026-09.

    e[s, 2016-01] = 0
    e[s, t] = noise_phi * e[s, t-1] + noise_sd * z[s, t-1]
    r[s, t] = beta_area * drift_city,t / 100 + e[s, t] - e[s, t-1]
    HPI[s, 2016-01] = base,  HPI[s, t] = HPI[s, t-1] * exp(r[s, t])

The recursion runs at full precision, then the whole matrix is rounded with
numpy.round(hpi, round_dp) (instruction 01b B.4). Everything downstream uses the rounded
values. `exp` differs in the last digit between platforms; 6 dp removes that.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmbsq.config import Config, load_hpi_drift
from rmbsq.synth.months import month_index, month_range, to_period


def drift_by_month(cfg: Config, cities: list[str], months: np.ndarray) -> np.ndarray:
    """City drift in percent, shape (len(cities), len(months)): the regime row with
    from <= t <= to."""
    regimes = load_hpi_drift(cfg.table_path("hpi_drift"))
    out = np.full((len(cities), len(months)), np.nan)
    for r in regimes.to_dict("records"):
        mask = (months >= month_index(r["from"])) & (months <= month_index(r["to"]))
        for i, c in enumerate(cities):
            out[i, mask] = r[c]
    if np.isnan(out).any():
        raise ValueError("a month has no HPI drift regime")
    return out


def hpi_unrounded(cfg: Config, geo: pd.DataFrame, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """(int months 2016-01..2026-09, full-precision HPI array of shape (60, 129))."""
    months = month_range(cfg.calendar.sim_start, cfg.calendar.window_end)
    n_s, n_t = len(geo), len(months)
    z = rng.standard_normal((n_s, n_t - 1))

    cities = list(dict.fromkeys(geo["city"]))
    drift = drift_by_month(cfg, cities, months)
    city_row = np.array([cities.index(c) for c in geo["city"]])
    beta = geo["beta"].to_numpy()

    phi, sd = cfg.hpi.noise_phi, cfg.hpi.noise_sd
    hpi = np.empty((n_s, n_t))
    hpi[:, 0] = cfg.hpi.base
    e_prev = np.zeros(n_s)
    for t in range(1, n_t):
        e = phi * e_prev + sd * z[:, t - 1]
        r = beta * drift[city_row, t] / 100 + e - e_prev  # drift is in percent (4.5)
        hpi[:, t] = hpi[:, t - 1] * np.exp(r)
        e_prev = e
    return months, hpi


def hpi_matrix(cfg: Config, geo: pd.DataFrame, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """(int months, HPI rounded to round_dp decimal places)."""
    months, hpi = hpi_unrounded(cfg, geo, rng)
    return months, np.round(hpi, cfg.hpi.round_dp)


def build_hpi(cfg: Config, geo: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """suburb, period, hpi for every suburb (geography order) and month."""
    months, hpi = hpi_matrix(cfg, geo, rng)
    n_s, n_t = hpi.shape
    return pd.DataFrame(
        {
            "suburb": np.repeat(geo["suburb"].to_numpy(), n_t),
            "period": np.tile(to_period(months), n_s),
            "hpi": hpi.reshape(-1),
        }
    )
