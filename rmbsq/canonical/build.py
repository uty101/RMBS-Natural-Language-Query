"""Canonical layer: dedupe, call detection, enrichment and the DuckDB build (Section 2).

Rules are kickoff 6.2 and instruction 02 part C.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rmbsq.canonical.ingest import ingest_format_a, ingest_format_b


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
