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

# kickoff 6.2 / instruction 02 C.4: bucket upper edges, a value on an edge goes to the lower bucket
LTV_EDGES = [0.6, 0.7, 0.8, 0.9]
LTV_LABELS = ["<=60", "60-70", "70-80", "80-90", ">90"]
SEASONING_EDGES = [12, 24, 36, 60]
SEASONING_LABELS = ["0-12", "13-24", "25-36", "37-60", ">60"]


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


def ltv_bucket(ltv) -> np.ndarray:
    """Kickoff 6.2 ltv buckets, labels `<=60, 60-70, 70-80, 80-90, >90`."""
    return np.array(LTV_LABELS, dtype=object)[np.searchsorted(LTV_EDGES, np.asarray(ltv, dtype=float), side="left")]


def seasoning_bucket(months) -> np.ndarray:
    """Kickoff 6.2 seasoning buckets, inclusive integer ranges `0-12, 13-24, 25-36, 37-60, >60`."""
    idx = np.searchsorted(SEASONING_EDGES, np.asarray(months, dtype=np.int64), side="left")
    return np.array(SEASONING_LABELS, dtype=object)[idx]


def _hpi_at(hpi: pd.DataFrame, suburb: np.ndarray, month: np.ndarray) -> np.ndarray:
    """hpi(suburb, month) for every row; a missing pair raises."""
    index = pd.MultiIndex.from_arrays([hpi["suburb"].to_numpy(object), from_period(hpi["period"])])
    pos = index.get_indexer(pd.MultiIndex.from_arrays([suburb, month]))
    if (pos < 0).any():
        raise KeyError("hpi has no value for some (suburb, month) pairs")
    return hpi["hpi"].to_numpy(dtype=float)[pos]


def enrich(df: pd.DataFrame, hpi: pd.DataFrame, cfg) -> pd.DataFrame:
    """Instruction 02 C.4: indexed_value, indexed_ltv, ltv_bucket_orig, ltv_bucket_indexed,
    seasoning_months, seasoning_bucket, current rate_type and io_flag, vintage_year.
    hpi has columns suburb, period (first-of-month datetimes or 'YYYY-MM'), hpi."""
    if not pd.api.types.is_datetime64_any_dtype(hpi["period"]):
        hpi = hpi.assign(period=pd.to_datetime(hpi["period"], format="%Y-%m"))
    out = df.copy()
    suburb = df["suburb"].to_numpy(object)
    period = from_period(df["period"])
    orig = from_period(df["orig_month"])
    orig_valuation = df["orig_valuation_c"].to_numpy(dtype=float) / 100
    indexed_value = orig_valuation * _hpi_at(hpi, suburb, period) / _hpi_at(hpi, suburb, orig)
    exiting = df["exit_reason"].notna().to_numpy()
    balance = np.where(exiting, df["opening_balance_c"].to_numpy(dtype=float), df["closing_balance_c"].to_numpy(dtype=float)) / 100
    out["indexed_value"] = indexed_value
    out["indexed_ltv"] = balance / indexed_value
    out["ltv_bucket_orig"] = pd.array(ltv_bucket(df["orig_ltv"].to_numpy()), dtype="string")
    out["ltv_bucket_indexed"] = pd.array(ltv_bucket(out["indexed_ltv"].to_numpy()), dtype="string")
    seasoning = period - orig
    out["seasoning_months"] = seasoning.astype(np.int64)
    out["seasoning_bucket"] = pd.array(seasoning_bucket(seasoning), dtype="string")
    fixed = (df["rate_type_orig"] == "fixed").fillna(False).to_numpy(dtype=bool) & (df["period"] < df["fixed_end_month"]).to_numpy()
    out["rate_type"] = pd.array(np.where(fixed, "fixed", "variable"), dtype="string")
    out["io_flag"] = df["io_flag_orig"].to_numpy() & (df["period"] < df["io_end_month"]).to_numpy()
    out["vintage_year"] = df["orig_month"].dt.year.astype(np.int64)
    return out


def canonical_rows(raw_dir: Path, cfg) -> pd.DataFrame:
    """Ingest, dedupe, detect calls and enrich every trustee file under raw_dir."""
    raw_dir = Path(raw_dir)
    hpi = pd.read_parquet(raw_dir / "hpi.parquet")
    return enrich(detect_calls(dedupe_resubmissions(ingest_raw(raw_dir))), hpi, cfg)
