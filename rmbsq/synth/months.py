"""Calendar months as integers.

A month is held as an int: months since 1970-01, which is numpy's `datetime64[M]`
encoding. Month arithmetic is then plain integer arithmetic (CONVENTIONS T4), and
frames get a first-of-month `datetime64` only at the edges.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def month_index(label: str) -> int:
    """'YYYY-MM' -> int month."""
    return int(np.datetime64(label, "M").astype(np.int64))


def month_label(m) -> str:
    """int month -> 'YYYY-MM'."""
    return str(np.datetime64(int(m), "M"))


def month_labels(months: np.ndarray) -> np.ndarray:
    """int months -> array of 'YYYY-MM' strings."""
    return np.datetime_as_string(np.asarray(months, dtype=np.int64).astype("datetime64[M]"), unit="M")


def to_period(months: np.ndarray) -> np.ndarray:
    """int months -> first-of-month datetime64[ns]."""
    return np.asarray(months, dtype=np.int64).astype("datetime64[M]").astype("datetime64[ns]")


def from_period(values) -> np.ndarray:
    """first-of-month datetimes (NaT allowed) -> int months, NaT as -1."""
    arr = pd.to_datetime(pd.Series(values)).to_numpy().astype("datetime64[M]")
    out = arr.astype(np.int64)
    out[np.isnat(arr)] = -1
    return out


def month_range(start: str, end: str) -> np.ndarray:
    """Inclusive int months from start to end."""
    return np.arange(month_index(start), month_index(end) + 1, dtype=np.int64)
