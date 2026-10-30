"""Step 2.4: enrichment (kickoff 6.2; instruction 02 C.4, D 2.4)."""

import pandas as pd
import pyarrow.parquet as pq

from rmbsq.canonical.build import ltv_bucket, seasoning_bucket


def _o29_rows(small_rows, small):
    """O-29: the first loan_id of each originator, at the latest period where that loan
    has a row with closing_balance > 0. The first loan_id is taken among loans that have
    such a row: D005-0001, RED's first loan, exits before the window and has no row."""
    live = small_rows[small_rows["closing_balance_c"] > 0]
    originator = small["loans"].set_index("loan_id")["originator"]
    live = live.assign(originator=originator.loc[live["loan_id"]].to_numpy())
    first = live.groupby("originator", sort=True)["loan_id"].min()
    out = [live[live["loan_id"] == loan_id].sort_values("period").iloc[-1] for loan_id in first]
    return pd.DataFrame(out)


def test_indexed_ltv_by_hand_five_rows(small_rows, small, small_raw):
    rows = _o29_rows(small_rows, small)
    assert len(rows) == 5
    hpi = pq.read_table(small_raw / "hpi.parquet").to_pandas()
    lookup = {(s, p): h for s, p, h in zip(hpi["suburb"], hpi["period"], hpi["hpi"])}
    for _, r in rows.iterrows():
        orig_valuation = int(r["orig_valuation_c"]) / 100
        h_period = lookup[(r["suburb"], r["period"].strftime("%Y-%m"))]
        h_orig = lookup[(r["suburb"], r["orig_month"].strftime("%Y-%m"))]
        value = orig_valuation * h_period / h_orig
        ltv = (int(r["closing_balance_c"]) / 100) / value
        assert abs(r["indexed_value"] - value) <= 1e-12
        assert abs(r["indexed_ltv"] - ltv) <= 1e-12


def test_buckets_edges():
    assert ltv_bucket([0.6, 0.7, 0.8, 0.9]).tolist() == ["<=60", "60-70", "70-80", "80-90"]
    assert ltv_bucket([0.6000001, 0.9000001]).tolist() == ["60-70", ">90"]
    months = [12, 13, 24, 25, 36, 37, 60, 61]
    assert seasoning_bucket(months).tolist() == ["0-12", "13-24", "13-24", "25-36", "25-36", "37-60", "37-60", ">60"]


def _switch_loan(small_rows, end_col):
    """The first loan (loan_id order) with rows in both the month before end_col and the
    month of end_col."""
    r = small_rows[small_rows[end_col].notna()]
    before = r[r["period"] == r[end_col] - pd.DateOffset(months=1)]["loan_id"]
    at = r[r["period"] == r[end_col]]["loan_id"]
    loan_id = sorted(set(before) & set(at))[0]
    return small_rows[small_rows["loan_id"] == loan_id].sort_values("period")


def test_current_rate_type_and_io(small_rows):
    fixed = _switch_loan(small_rows, "fixed_end_month")
    assert (fixed["rate_type_orig"] == "fixed").all()
    end = fixed["fixed_end_month"].iloc[0]
    assert (fixed.loc[fixed["period"] < end, "rate_type"] == "fixed").all()
    assert (fixed.loc[fixed["period"] >= end, "rate_type"] == "variable").all()
    assert fixed.loc[fixed["period"] == end - pd.DateOffset(months=1), "rate_type"].item() == "fixed"
    assert fixed.loc[fixed["period"] == end, "rate_type"].item() == "variable"

    io = _switch_loan(small_rows, "io_end_month")
    assert io["io_flag_orig"].all()
    end = io["io_end_month"].iloc[0]
    assert io.loc[io["period"] < end, "io_flag"].all()
    assert not io.loc[io["period"] >= end, "io_flag"].any()
    assert io.loc[io["period"] == end - pd.DateOffset(months=1), "io_flag"].item() is True
    assert io.loc[io["period"] == end, "io_flag"].item() is False
