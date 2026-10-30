"""Canonical layer: dedupe, call detection, enrichment and the DuckDB build (Section 2).

Rules are kickoff 6.2 and instruction 02 part C.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from rmbsq.canonical.ingest import ingest_format_a, ingest_format_b
from rmbsq.config import load_config
from rmbsq.synth.months import from_period, month_index, month_labels, to_period

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


# dim_loan columns that must be the same on every row of a loan (instruction 02 C.5)
STATIC = [
    "deal_id", "orig_month", "orig_balance_c", "orig_valuation_c", "orig_ltv", "rate_type_orig",
    "fixed_end_month", "io_flag_orig", "io_end_month", "occupancy", "lmi_flag", "city", "state",
    "area", "suburb",
]


def build_dim_loan(rows: pd.DataFrame) -> pd.DataFrame:
    """1 row per loan, from that loan's first canonical row (earliest period), loan_id
    order. Raises ValueError if any static field differs between a loan's rows."""
    changed = rows.groupby("loan_id", sort=True)[STATIC].nunique(dropna=False) > 1
    if changed.to_numpy().any():
        bad = changed[changed.any(axis=1)]
        detail = "; ".join(f"{loan}: {', '.join(bad.columns[bad.loc[loan].to_numpy()])}" for loan in bad.index[:10])
        raise ValueError(f"static fields differ between rows of {len(bad)} loans: {detail}")
    first = rows.sort_values(["loan_id", "period"], kind="stable").drop_duplicates("loan_id")
    return first[["loan_id", *STATIC, "vintage_year", "ltv_bucket_orig"]].reset_index(drop=True)


def _money(col: str) -> str:
    """Integer cents to DECIMAL(18,2) dollars, exactly (O-27); the `_c` suffix goes."""
    return f"CAST(CAST({col} AS DECIMAL(18,0)) * 0.01 AS DECIMAL(18,2)) AS {col.removesuffix('_c')}"


DIM_DEAL_SQL = """
CREATE TABLE dim_deal AS
SELECT CAST(deal_id AS VARCHAR) AS deal_id, CAST(deal_name AS VARCHAR) AS deal_name,
       CAST(originator AS VARCHAR) AS originator, CAST(originator_name AS VARCHAR) AS originator_name,
       CAST(trustee_format AS VARCHAR) AS trustee_format, CAST(issue_month AS DATE) AS issue_month,
       CAST(year(issue_month) AS INTEGER) AS issue_year, {issue_balance}
FROM deals_df ORDER BY deal_id
"""

DIM_LOAN_SQL = """
CREATE TABLE dim_loan AS
SELECT CAST(loan_id AS VARCHAR) AS loan_id, CAST(deal_id AS VARCHAR) AS deal_id,
       CAST(orig_month AS DATE) AS orig_month, CAST(vintage_year AS INTEGER) AS vintage_year,
       {orig_balance}, {orig_valuation}, CAST(orig_ltv AS DOUBLE) AS orig_ltv,
       CAST(ltv_bucket_orig AS VARCHAR) AS ltv_bucket_orig, CAST(rate_type_orig AS VARCHAR) AS rate_type_orig,
       CAST(fixed_end_month AS DATE) AS fixed_end_month, CAST(io_flag_orig AS BOOLEAN) AS io_flag_orig,
       CAST(io_end_month AS DATE) AS io_end_month, CAST(occupancy AS VARCHAR) AS occupancy,
       CAST(lmi_flag AS BOOLEAN) AS lmi_flag, CAST(city AS VARCHAR) AS city, CAST(state AS VARCHAR) AS state,
       CAST(area AS VARCHAR) AS area, CAST(suburb AS VARCHAR) AS suburb
FROM dim_loan_df ORDER BY loan_id
"""

FACT_SQL = """
CREATE TABLE fact_loan_month AS
SELECT CAST(loan_id AS VARCHAR) AS loan_id, CAST(deal_id AS VARCHAR) AS deal_id, CAST(period AS DATE) AS period,
       {opening_balance}, {scheduled_principal}, {curtailment}, {closing_balance},
       CAST(interest_rate AS DOUBLE) AS interest_rate, CAST(dpd_bucket AS TINYINT) AS dpd_bucket,
       CAST(hardship_flag AS BOOLEAN) AS hardship_flag, CAST(exit_reason AS VARCHAR) AS exit_reason,
       {exit_balance}, {loss}, CAST(indexed_value AS DOUBLE) AS indexed_value,
       CAST(indexed_ltv AS DOUBLE) AS indexed_ltv, CAST(ltv_bucket_indexed AS VARCHAR) AS ltv_bucket_indexed,
       CAST(seasoning_months AS INTEGER) AS seasoning_months, CAST(seasoning_bucket AS VARCHAR) AS seasoning_bucket,
       CAST(rate_type AS VARCHAR) AS rate_type, CAST(io_flag AS BOOLEAN) AS io_flag
FROM rows_df ORDER BY period, loan_id
"""

HPI_SQL = """
CREATE TABLE hpi AS
SELECT CAST(suburb AS VARCHAR) AS suburb, CAST(period AS DATE) AS period, CAST(hpi AS DOUBLE) AS hpi
FROM hpi_df
"""

# instruction 03 D.4: period labels by join, so compiled SQL needs no date functions
DIM_PERIOD_SQL = """
CREATE TABLE dim_period AS
SELECT CAST(period AS DATE) AS period, CAST(month_label AS VARCHAR) AS month_label,
       CAST(quarter_label AS VARCHAR) AS quarter_label, CAST(year_label AS VARCHAR) AS year_label
FROM period_df ORDER BY period
"""

CASH_SQL = """
CREATE TABLE cash_rate AS
SELECT CAST(period AS DATE) AS period, CAST(rate AS DOUBLE) AS rate FROM cash_df ORDER BY period
"""

DUPLICATE_KEYS_SQL = """
SELECT count(*) FROM (SELECT loan_id, period FROM fact_loan_month GROUP BY loan_id, period HAVING count(*) > 1)
"""

# instruction 02 C.5: 1 statement over fact_loan_month (joined to dim_loan for orig_ltv)
AGG_SQL = """
CREATE TABLE agg_deal_month AS
SELECT f.deal_id, f.period,
       count(*) FILTER (WHERE f.closing_balance > 0) AS loan_count,
       COALESCE(sum(f.closing_balance) FILTER (WHERE f.closing_balance > 0), 0) AS bal,
       COALESCE(sum(f.closing_balance) FILTER (
           WHERE f.closing_balance > 0 AND f.dpd_bucket >= 2 AND NOT f.hardship_flag), 0) AS a30_bal,
       COALESCE(sum(f.closing_balance) FILTER (
           WHERE f.closing_balance > 0 AND f.dpd_bucket = 4 AND NOT f.hardship_flag), 0) AS a90_bal,
       count(*) FILTER (WHERE f.closing_balance > 0 AND f.dpd_bucket = 4 AND NOT f.hardship_flag) AS a90_cnt,
       COALESCE(sum(f.closing_balance) FILTER (WHERE f.closing_balance > 0 AND f.hardship_flag), 0) AS hard_bal,
       COALESCE(sum(CAST(f.closing_balance AS DOUBLE) * l.orig_ltv) FILTER (WHERE f.closing_balance > 0), 0.0)
           AS orig_ltv_x_bal,
       COALESCE(sum(CAST(f.closing_balance AS DOUBLE) * f.indexed_ltv) FILTER (WHERE f.closing_balance > 0), 0.0)
           AS idx_ltv_x_bal,
       COALESCE(sum(CAST(f.closing_balance AS DOUBLE) * f.interest_rate) FILTER (WHERE f.closing_balance > 0), 0.0)
           AS rate_x_bal,
       COALESCE(sum(f.curtailment) FILTER (WHERE f.opening_balance > 0), 0)
           + COALESCE(sum(f.exit_balance) FILTER (WHERE f.opening_balance > 0 AND f.exit_reason = 'prepaid'), 0)
           AS smm_num,
       COALESCE(sum(f.opening_balance - f.scheduled_principal) FILTER (
           WHERE f.opening_balance > 0 AND (f.exit_reason IS NULL OR f.exit_reason = 'prepaid')), 0) AS smm_den,
       COALESCE(sum(f.exit_balance) FILTER (WHERE f.opening_balance > 0 AND f.exit_reason = 'defaulted'), 0)
           AS mdr_num,
       COALESCE(sum(f.opening_balance) FILTER (WHERE f.opening_balance > 0), 0) AS mdr_den
FROM fact_loan_month f JOIN dim_loan l ON f.loan_id = l.loan_id
GROUP BY f.deal_id, f.period
ORDER BY f.deal_id, f.period
"""

# instruction 02 C.6: pool metrics, columns summed over deals per period, then ratios (kickoff 6.3)
POOL_SQL = """
WITH p AS (
    SELECT period, sum(bal) AS bal, sum(a30_bal) AS a30_bal, sum(a90_bal) AS a90_bal,
           sum(hard_bal) AS hard_bal, sum(idx_ltv_x_bal) AS idx_ltv_x_bal, sum(smm_num) AS smm_num,
           sum(smm_den) AS smm_den, sum(mdr_num) AS mdr_num, sum(mdr_den) AS mdr_den
    FROM agg_deal_month GROUP BY period
)
SELECT strftime(period, '%Y-%m') AS period,
       CAST(a30_bal AS DOUBLE) / CAST(bal AS DOUBLE) AS arrears_30p_bal,
       CAST(a90_bal AS DOUBLE) / CAST(bal AS DOUBLE) AS arrears_90p_bal,
       CAST(hard_bal AS DOUBLE) / CAST(bal AS DOUBLE) AS hardship_share_bal,
       1 - pow(1 - CAST(smm_num AS DOUBLE) / CAST(smm_den AS DOUBLE), 12) AS cpr,
       1 - pow(1 - CAST(mdr_num AS DOUBLE) / CAST(mdr_den AS DOUBLE), 12) AS cdr,
       idx_ltv_x_bal / CAST(bal AS DOUBLE) AS wa_indexed_ltv,
       bal AS balance_total
FROM p ORDER BY period
"""

TABLES = ["dim_deal", "dim_loan", "fact_loan_month", "hpi", "cash_rate", "agg_deal_month", "dim_period"]
FACT_MONEY = ["opening_balance_c", "scheduled_principal_c", "curtailment_c", "closing_balance_c", "exit_balance_c", "loss_c"]


def _with_months(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df.assign(**{col: pd.to_datetime(df[col], format="%Y-%m")})


def build_dim_period(cfg) -> pd.DataFrame:
    """Instruction 03 D.4: 1 row per month from window_start to window_end, for example
    2025-04-01, 2025-04, 2025-Q2, 2025."""
    months = np.arange(month_index(cfg.calendar.window_start), month_index(cfg.calendar.window_end) + 1)
    labels = month_labels(months)
    year = (months // 12 + 1970).astype(str)
    quarter = (months % 12 // 3 + 1).astype(str)
    return pd.DataFrame({
        "period": to_period(months),
        "month_label": labels,
        "quarter_label": np.char.add(np.char.add(year, "-Q"), quarter),
        "year_label": year,
    })


def build_canonical(raw_dir: Path, db_path: Path, cfg) -> None:
    """Instruction 02 C.5: the canonical DuckDB file from the raw files, rebuilt from
    scratch. DuckDB runs on 1 thread, so DOUBLE sums add in the same order every run
    (rule 9)."""
    raw_dir, db_path = Path(raw_dir), Path(db_path)
    rows_df = canonical_rows(raw_dir, cfg)
    dim_loan_df = build_dim_loan(rows_df)
    deals = _with_months(pd.read_parquet(raw_dir / "deals.parquet"), "issue_month")
    deals_df = deals.assign(issue_balance_c=np.round(deals["issue_balance"].to_numpy() * 100).astype(np.int64))
    hpi_df = _with_months(pd.read_parquet(raw_dir / "hpi.parquet"), "period")
    cash_df = _with_months(pd.read_parquet(raw_dir / "cash_rate.parquet"), "period")
    period_df = build_dim_period(cfg)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    try:
        con.execute("SET threads = 1")
        for name, df in [("deals_df", deals_df), ("dim_loan_df", dim_loan_df), ("rows_df", rows_df),
                         ("hpi_df", hpi_df), ("cash_df", cash_df), ("period_df", period_df)]:
            con.register(name, df)
        con.execute(DIM_DEAL_SQL.format(issue_balance=_money("issue_balance_c")))
        con.execute(DIM_LOAN_SQL.format(orig_balance=_money("orig_balance_c"), orig_valuation=_money("orig_valuation_c")))
        con.execute(FACT_SQL.format(**{c.removesuffix("_c"): _money(c) for c in FACT_MONEY}))
        con.execute(HPI_SQL)
        con.execute(CASH_SQL)
        dupes = con.execute(DUPLICATE_KEYS_SQL).fetchone()[0]
        if dupes:
            raise ValueError(f"fact_loan_month has {dupes} duplicate (loan_id, period) keys")
        con.execute(AGG_SQL)
        con.execute(DIM_PERIOD_SQL)
    finally:
        con.close()


def pool_monthly(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Instruction 02 C.6: the pool_monthly_truth.csv columns, from agg_deal_month.
    balance_total holds exact Decimals."""
    cur = con.execute(POOL_SQL)
    names = [d[0] for d in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=names)


def write_pool_monthly(df: pd.DataFrame, path: Path) -> None:
    """Instruction 02 C.6: ratios as %.10f, balance_total with exactly 2 decimals, LF."""
    lines = [",".join(df.columns)]
    for r in df.itertuples(index=False):
        ratios = ["%.10f" % v for v in r[1:-1]]
        lines.append(",".join([r[0], *ratios, f"{r[-1]:.2f}"]))
    Path(path).write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def row_counts(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Instruction 02 C.6: table, trustee_format, rows. 1 row per table with trustee_format
    `all`, plus dim_loan and fact_loan_month split into A and B."""
    out = []
    for table in TABLES:
        out.append((table, "all", con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]))
        if table in ("dim_loan", "fact_loan_month"):
            split = con.execute(
                f"SELECT d.trustee_format, count(*) FROM {table} t JOIN dim_deal d ON t.deal_id = d.deal_id "
                "GROUP BY d.trustee_format ORDER BY d.trustee_format"
            ).fetchall()
            out.extend((table, fmt, n) for fmt, n in split)
    return pd.DataFrame(out, columns=["table", "trustee_format", "rows"])
