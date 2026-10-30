"""Step 2.5: the canonical database (kickoff 6.1; instruction 02 C.5, C.6, D 2.5)."""

import csv
from decimal import Decimal
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest

from rmbsq.canonical.build import build_dim_loan, pool_monthly
from rmbsq.synth.truth import pool_monthly as truth_pool_monthly

ROOT = Path(__file__).resolve().parents[1]

# instruction 02 C.5, column for column
C5 = {
    "dim_deal": [
        ("deal_id", "VARCHAR"), ("deal_name", "VARCHAR"), ("originator", "VARCHAR"),
        ("originator_name", "VARCHAR"), ("trustee_format", "VARCHAR"), ("issue_month", "DATE"),
        ("issue_year", "INTEGER"), ("issue_balance", "DECIMAL(18,2)"),
    ],
    "dim_loan": [
        ("loan_id", "VARCHAR"), ("deal_id", "VARCHAR"), ("orig_month", "DATE"), ("vintage_year", "INTEGER"),
        ("orig_balance", "DECIMAL(18,2)"), ("orig_valuation", "DECIMAL(18,2)"), ("orig_ltv", "DOUBLE"),
        ("ltv_bucket_orig", "VARCHAR"), ("rate_type_orig", "VARCHAR"), ("fixed_end_month", "DATE"),
        ("io_flag_orig", "BOOLEAN"), ("io_end_month", "DATE"), ("occupancy", "VARCHAR"),
        ("lmi_flag", "BOOLEAN"), ("city", "VARCHAR"), ("state", "VARCHAR"), ("area", "VARCHAR"),
        ("suburb", "VARCHAR"),
    ],
    "fact_loan_month": [
        ("loan_id", "VARCHAR"), ("deal_id", "VARCHAR"), ("period", "DATE"),
        ("opening_balance", "DECIMAL(18,2)"), ("scheduled_principal", "DECIMAL(18,2)"),
        ("curtailment", "DECIMAL(18,2)"), ("closing_balance", "DECIMAL(18,2)"), ("interest_rate", "DOUBLE"),
        ("dpd_bucket", "TINYINT"), ("hardship_flag", "BOOLEAN"), ("exit_reason", "VARCHAR"),
        ("exit_balance", "DECIMAL(18,2)"), ("loss", "DECIMAL(18,2)"), ("indexed_value", "DOUBLE"),
        ("indexed_ltv", "DOUBLE"), ("ltv_bucket_indexed", "VARCHAR"), ("seasoning_months", "INTEGER"),
        ("seasoning_bucket", "VARCHAR"), ("rate_type", "VARCHAR"), ("io_flag", "BOOLEAN"),
    ],
    "hpi": [("suburb", "VARCHAR"), ("period", "DATE"), ("hpi", "DOUBLE")],
    "cash_rate": [("period", "DATE"), ("rate", "DOUBLE")],
}
# agg_deal_month: C.5 gives each column's kind (a count, a DECIMAL sum or a DOUBLE sum)
AGG = [
    ("deal_id", "VARCHAR"), ("period", "DATE"), ("loan_count", "count"), ("bal", "DECIMAL"),
    ("a30_bal", "DECIMAL"), ("a90_bal", "DECIMAL"), ("a90_cnt", "count"), ("hard_bal", "DECIMAL"),
    ("orig_ltv_x_bal", "DOUBLE"), ("idx_ltv_x_bal", "DOUBLE"), ("rate_x_bal", "DOUBLE"),
    ("smm_num", "DECIMAL"), ("smm_den", "DECIMAL"), ("mdr_num", "DECIMAL"), ("mdr_den", "DECIMAL"),
]
# the same quantities summed straight over fact_loan_month, with no grouping
DIRECT = {
    "loan_count": "count(*) FILTER (WHERE f.closing_balance > 0)",
    "bal": "sum(f.closing_balance) FILTER (WHERE f.closing_balance > 0)",
    "a30_bal": "sum(f.closing_balance) FILTER (WHERE f.closing_balance > 0 AND f.dpd_bucket >= 2 AND NOT f.hardship_flag)",
    "a90_bal": "sum(f.closing_balance) FILTER (WHERE f.closing_balance > 0 AND f.dpd_bucket = 4 AND NOT f.hardship_flag)",
    "a90_cnt": "count(*) FILTER (WHERE f.closing_balance > 0 AND f.dpd_bucket = 4 AND NOT f.hardship_flag)",
    "hard_bal": "sum(f.closing_balance) FILTER (WHERE f.closing_balance > 0 AND f.hardship_flag)",
    "orig_ltv_x_bal": "sum(CAST(f.closing_balance AS DOUBLE) * l.orig_ltv) FILTER (WHERE f.closing_balance > 0)",
    "idx_ltv_x_bal": "sum(CAST(f.closing_balance AS DOUBLE) * f.indexed_ltv) FILTER (WHERE f.closing_balance > 0)",
    "rate_x_bal": "sum(CAST(f.closing_balance AS DOUBLE) * f.interest_rate) FILTER (WHERE f.closing_balance > 0)",
    "smm_num": "sum(f.curtailment) FILTER (WHERE f.opening_balance > 0)"
               " + sum(f.exit_balance) FILTER (WHERE f.opening_balance > 0 AND f.exit_reason = 'prepaid')",
    "smm_den": "sum(f.opening_balance - f.scheduled_principal) FILTER (WHERE f.opening_balance > 0"
               " AND (f.exit_reason IS NULL OR f.exit_reason = 'prepaid'))",
    "mdr_num": "sum(f.exit_balance) FILTER (WHERE f.opening_balance > 0 AND f.exit_reason = 'defaulted')",
    "mdr_den": "sum(f.opening_balance) FILTER (WHERE f.opening_balance > 0)",
}
RATIOS = ["arrears_30p_bal", "arrears_90p_bal", "hardship_share_bal", "cpr", "cdr", "wa_indexed_ltv"]


def _describe(con, table):
    return [(r[0], r[1]) for r in con.execute(f"DESCRIBE {table}").fetchall()]


def test_tables_and_types(small_db):
    con = duckdb.connect(str(small_db), read_only=True)
    for table, expected in C5.items():
        assert _describe(con, table) == expected, table
    agg = _describe(con, "agg_deal_month")
    assert [n for n, _ in agg] == [n for n, _ in AGG]
    for (name, typ), (_, kind) in zip(agg, AGG):
        if kind == "count":
            assert typ == "BIGINT", name
        elif kind == "DECIMAL":
            assert typ.startswith("DECIMAL("), name
        else:
            assert typ == kind, name
    n, distinct = con.execute("SELECT count(*), count(DISTINCT (deal_id, period)) FROM agg_deal_month").fetchone()
    assert n == distinct
    n, distinct = con.execute("SELECT count(*), count(DISTINCT (loan_id, period)) FROM fact_loan_month").fetchone()
    assert n == distinct
    con.close()


def test_agg_sums_equal_fact_sums(small_db):
    con = duckdb.connect(str(small_db), read_only=True)
    agg = con.execute("SELECT " + ", ".join(f"sum({c})" for c in DIRECT) + " FROM agg_deal_month").fetchone()
    direct = con.execute(
        "SELECT " + ", ".join(DIRECT.values()) + " FROM fact_loan_month f JOIN dim_loan l ON f.loan_id = l.loan_id"
    ).fetchone()
    con.close()
    kinds = dict(AGG)
    for name, a, d in zip(DIRECT, agg, direct):
        if kinds[name] == "DOUBLE":
            assert abs(a - d) <= 1e-9 * abs(d), name
        else:
            assert isinstance(a, (Decimal, int)) and a == d, name


def test_dim_loan_static_check(small_rows):
    loan_id = small_rows["loan_id"].iloc[0]
    pair = small_rows[small_rows["loan_id"] == loan_id].head(2).copy()
    assert len(pair) == 2
    assert len(build_dim_loan(pair)) == 1
    pair.iloc[1, pair.columns.get_loc("suburb")] = "Somewhere Else"
    with pytest.raises(ValueError, match="suburb"):
        build_dim_loan(pair)


def _compare(canonical: pd.DataFrame, truth: pd.DataFrame):
    assert list(canonical.columns) == list(truth.columns)
    assert list(canonical["period"]) == list(truth["period"])
    for col in RATIOS:
        diff = np.abs(canonical[col].astype(float).to_numpy() - truth[col].astype(float).to_numpy())
        assert diff.max() <= 1e-9, (col, diff.max())
    bal = np.abs(canonical["balance_total"].astype(float).to_numpy() - truth["balance_total"].astype(float).to_numpy())
    assert bal.max() <= 0.01, bal.max()


def test_pool_monthly_matches_truth(small_db, small):
    con = duckdb.connect(str(small_db), read_only=True)
    canonical = pool_monthly(con)
    con.close()
    _compare(canonical, truth_pool_monthly(small["panel"]))


@pytest.mark.full
def test_full_pool_monthly_matches_truth(full_db):
    con = duckdb.connect(str(full_db), read_only=True)
    canonical = pool_monthly(con)
    con.close()
    with open(ROOT / "outputs" / "pool_monthly_truth.csv", encoding="utf-8", newline="") as f:
        truth = pd.DataFrame(list(csv.DictReader(f)))
    _compare(canonical, truth)


def test_dim_period(small_db):
    """Instruction 03 D.4: 60 months, window_start to window_end, with 3 spot checks."""
    con = duckdb.connect(str(small_db), read_only=True)
    try:
        cols = con.execute("SELECT column_name, data_type FROM information_schema.columns "
                           "WHERE table_name = 'dim_period' ORDER BY ordinal_position").fetchall()
        rows = con.execute("SELECT strftime(period, '%Y-%m-%d'), month_label, quarter_label, year_label "
                           "FROM dim_period ORDER BY period").fetchall()
    finally:
        con.close()
    assert cols == [("period", "DATE"), ("month_label", "VARCHAR"), ("quarter_label", "VARCHAR"),
                    ("year_label", "VARCHAR")]
    assert len(rows) == 60
    assert rows[0] == ("2021-10-01", "2021-10", "2021-Q4", "2021")
    assert ("2024-12-01", "2024-12", "2024-Q4", "2024") in rows
    assert rows[-1] == ("2026-09-01", "2026-09", "2026-Q3", "2026")
