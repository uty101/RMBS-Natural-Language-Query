"""Canonical layer: dedupe, call detection, enrichment and the DuckDB build (Section 2).

Rules are kickoff 6.2 and instruction 02 part C.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from rmbsq.canonical.ingest import ingest_format_a, ingest_format_b
from rmbsq.config import load_config
from rmbsq.synth.months import from_period

ROOT = Path(__file__).resolve().parents[2]


def ingest_raw(raw_dir: Path) -> pd.DataFrame:
    """Every trustee file under raw_dir as canonical rows, format A files then format B,
    each in file name order."""
    raw_dir = Path(raw_dir)
    frames = [ingest_format_a(p) for p in sorted((raw_dir / "trustee_a").glob("*.parquet"))]
    frames += [ingest_format_b(p) for p in sorted((raw_dir / "trustee_b").glob("*.parquet"))]
    return pd.concat(frames, ignore_index=True)


def dedupe_resubmissions(df: pd.DataFrame) -> pd.DataFrame:
    """Kickoff 6.2: keep the max submission_seq per (loan_id, period)."""
    keep = df.groupby(["loan_id", "period"], sort=False)["submission_seq"].transform("max") == df["submission_seq"]
    return df[keep.to_numpy()].reset_index(drop=True)


def detect_calls(df: pd.DataFrame) -> pd.DataFrame:
    """Instruction 02 C.3, both formats, after dedupe. For deal d and month t, with
    active(d, t - 1) the rows of d in t - 1 with closing_balance_c > 0: if active > 0 and
    the prepaid exits in (d, t) number at least call_detect_share x active, every prepaid
    exit in (d, t) becomes called."""
    share = load_config(ROOT / "config.toml").deals.call_detect_share
    month = from_period(df["period"])
    live = (df["closing_balance_c"] > 0).fillna(False).to_numpy(dtype=bool)
    active = pd.DataFrame({"deal_id": df["deal_id"].to_numpy()[live], "month": month[live] + 1}).value_counts()
    prepaid = (df["exit_reason"] == "prepaid").fillna(False).to_numpy(dtype=bool)
    exits = pd.DataFrame({"deal_id": df["deal_id"].to_numpy()[prepaid], "month": month[prepaid]}).value_counts()
    both = pd.concat({"active": active, "prepaid": exits}, axis=1).fillna(0)
    hit = both[(both["active"] > 0) & (both["prepaid"] >= share * both["active"])].index
    key = pd.MultiIndex.from_arrays([df["deal_id"].to_numpy(), month], names=["deal_id", "month"])
    called = prepaid & key.isin(hit)
    out = df.copy()
    out.loc[called, "exit_reason"] = "called"
    return out
