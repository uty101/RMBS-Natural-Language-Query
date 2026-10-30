"""Data summary and compiler check for the write-up (instruction 06 C.1, C.2). Step 6.1.

`data_summary` counts the canonical tables and raw files, compares the canonical table
with the true panel (`truth_check`), and reads the pool's 90+ arrears from
`pool_monthly.csv`. `compiler_check` runs every compiler gold spec and every eval answer
item's gold spec on 1 connection and compares each with its hand or gold SQL by the step
3.3 rule, and checks its Oracle text by the step 3.5 rule.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import sqlglot

from rmbsq.canonical.truth_check import truth_check
from rmbsq.db import connect_readonly
from rmbsq.semantic.compiler import compile, execute
from rmbsq.semantic.spec import QuerySpec

SUMMARY_COLUMNS = ["stat", "value"]
CHECK_COLUMNS = ["id", "source", "rows", "max_scaled_diff", "route", "oracle_ok"]
TRUSTEE_DIRS = ["trustee_a", "trustee_b"]
# DuckDB constructs that sqlglot passes into Oracle output (instruction 03 D.3, E 3.5)
BANNED = ["FILTER(", "FILTER (", "YEAR(", "QUARTER(", "STRFTIME", "CLOB", "LIMIT ", "::"]


def raw_rows(raw_dir: Path) -> int:
    return sum(pq.ParquetFile(p).metadata.num_rows
               for d in TRUSTEE_DIRS for p in sorted((Path(raw_dir) / d).glob("*.parquet")))


def data_summary(db: Path, raw_dir: Path, pool_monthly_csv: Path, panel: pd.DataFrame, cfg) -> pd.DataFrame:
    con = connect_readonly(db)
    try:
        one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
        n_deals = one("SELECT count(*) FROM dim_deal")
        n_loans = one("SELECT count(*) FROM dim_loan")
        n_loan_months = one("SELECT count(*) FROM fact_loan_month")
        n_called = one("SELECT count(DISTINCT deal_id) FROM fact_loan_month WHERE exit_reason = 'called'")
        n_called_b = one("SELECT count(DISTINCT f.deal_id) FROM fact_loan_month f JOIN dim_deal d"
                         " ON d.deal_id = f.deal_id WHERE f.exit_reason = 'called' AND d.trustee_format = 'B'")
    finally:
        con.close()
    n_raw = raw_rows(raw_dir)
    pool = pd.read_csv(pool_monthly_csv, dtype={"period": str})
    a90 = pool.set_index("period")["arrears_90p_bal"]
    peak = a90.idxmax()  # the first period on ties
    rows = [
        ("n_deals", int(n_deals)), ("n_loans", int(n_loans)), ("n_loan_months", int(n_loan_months)),
        ("n_raw_rows", n_raw), ("n_resubmission_duplicates", n_raw - int(n_loan_months)),
        ("n_called_deals", int(n_called)), ("n_called_deals_b", int(n_called_b)),
        ("canonical_truth_mismatches", truth_check(db, panel).mismatched_rows),
        ("arrears_90p_first", float(a90[cfg.calendar.window_start])),
        ("arrears_90p_peak", float(a90[peak])),
        ("arrears_90p_latest", float(a90[cfg.calendar.latest])),
        ("arrears_90p_peak_month", str(peak)),
    ]
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def max_scaled_diff(got: pd.DataFrame, want: pd.DataFrame, metrics: list[str]) -> float:
    """The step 3.3 rule: identical columns and row order, dimension values equal as
    strings, and the max over metric values of |got - want| / max(1, |want|). A
    structural difference raises ValueError."""
    if list(got.columns) != list(want.columns):
        raise ValueError(f"columns differ: {list(got.columns)} against {list(want.columns)}")
    if len(got) != len(want):
        raise ValueError(f"row counts differ: {len(got)} against {len(want)}")
    worst = 0.0
    for c in got.columns:
        if c in metrics:
            a = got[c].astype("float64").to_numpy()
            b = want[c].astype("float64").to_numpy()
            if (np.isnan(a) != np.isnan(b)).any():
                raise ValueError(f"{c}: nulls differ")
            ok = ~np.isnan(b)
            if ok.any():
                worst = max(worst, float(np.max(np.abs(a[ok] - b[ok]) / np.maximum(1.0, np.abs(b[ok])))))
        elif [str(v) for v in got[c]] != [str(v) for v in want[c]]:
            raise ValueError(f"{c}: values differ")
    return worst


def oracle_ok(sql_oracle: str) -> bool:
    """Step 3.5: no banned substring, and the text parses back as Oracle."""
    if any(b.lower() in sql_oracle.lower() for b in BANNED):
        return False
    try:
        sqlglot.parse_one(sql_oracle, read="oracle")
    except sqlglot.errors.SqlglotError:
        return False
    return True


def compiler_check(db: Path, gold: list[dict], items, catalog) -> pd.DataFrame:
    """1 row per compiler gold spec (source compiler_gold), then per eval answer item
    (source eval); `max_scaled_diff` is written %.3e."""
    cases = [(g["id"], "compiler_gold", QuerySpec.model_validate(g["spec"]), g["hand_sql"]) for g in gold]
    cases += [(i.id, "eval", i.gold_spec, i.gold_sql) for i in items if i.gold_spec is not None]
    con = connect_readonly(db)
    rows = []
    try:
        for id_, source, spec, sql in cases:
            compiled = compile(spec, catalog)
            got = execute(compiled, con)
            diff = max_scaled_diff(got, con.execute(sql).df(), spec.metrics)
            rows.append([id_, source, len(got), "%.3e" % diff, compiled.route, oracle_ok(compiled.sql_oracle)])
    finally:
        con.close()
    return pd.DataFrame(rows, columns=CHECK_COLUMNS)
