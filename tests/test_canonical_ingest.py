"""Step 2.1: ingestion of formats A and B (instruction 02 C.1, C.2, D 2.1)."""

import numpy as np
import pandas as pd

from rmbsq.canonical.ingest import arrears_days_to_bucket, ingest_format_a, ingest_format_b

# instruction 02 C.1, column for column
C1 = [
    ("loan_id", "string"), ("deal_id", "string"), ("period", "datetime64[ns]"),
    ("submission_seq", "int64"), ("opening_balance_c", "Int64"),
    ("scheduled_principal_c", "Int64"), ("curtailment_c", "Int64"),
    ("closing_balance_c", "Int64"), ("exit_balance_c", "Int64"), ("loss_c", "Int64"),
    ("interest_rate", "float64"), ("dpd_bucket", "int8"), ("hardship_flag", "bool"),
    ("exit_reason", "string"), ("orig_month", "datetime64[ns]"),
    ("fixed_end_month", "datetime64[ns]"), ("io_end_month", "datetime64[ns]"),
    ("orig_balance_c", "Int64"), ("orig_valuation_c", "Int64"), ("orig_ltv", "float64"),
    ("rate_type_orig", "string"), ("io_flag_orig", "bool"), ("lmi_flag", "bool"),
    ("occupancy", "string"), ("city", "string"), ("state", "string"), ("area", "string"),
    ("suburb", "string"), ("trustee_format", "string"),
]


def _all(small_raw):
    a = [ingest_format_a(p) for p in sorted((small_raw / "trustee_a").glob("*.parquet"))]
    b = [ingest_format_b(p) for p in sorted((small_raw / "trustee_b").glob("*.parquet"))]
    return pd.concat(a, ignore_index=True), pd.concat(b, ignore_index=True)


def test_formats_same_columns_and_dtypes(small_raw):
    a = ingest_format_a(small_raw / "trustee_a" / "D001.parquet")
    b = ingest_format_b(small_raw / "trustee_b" / "D004.parquet")
    for df in (a, b):
        assert [(c, str(t)) for c, t in df.dtypes.items()] == [(c, str(pd.api.types.pandas_dtype(t))) for c, t in C1]
    assert set(a["trustee_format"]) == {"A"}
    assert set(b["trustee_format"]) == {"B"}


def test_arrears_days_map():
    days = [0, 1, 29, 30, 59, 60, 89, 90, 400]
    assert arrears_days_to_bucket(np.array(days)).tolist() == [0, 1, 1, 2, 2, 3, 3, 4, 4]


def test_hardship_rows_bucket_zero(small_raw):
    a, b = _all(small_raw)
    for df in (a, b):
        hard = df[df["hardship_flag"]]
        assert len(hard) > 0
        assert (hard["dpd_bucket"] == 0).all()


def test_cents_exact(small_raw, small):
    a = ingest_format_a(small_raw / "trustee_a" / "D001.parquet")
    truth = small["panel"]
    truth = truth[truth["deal_id"] == "D001"].sort_values(["period", "loan_id"]).reset_index(drop=True)
    a = a.sort_values(["period", "loan_id"]).reset_index(drop=True)
    assert len(a) == len(truth)
    assert (a["loan_id"].to_numpy() == truth["loan_id"].to_numpy()).all()
    assert (a["period"].to_numpy() == truth["period"].to_numpy()).all()
    pairs = {
        "opening_balance_c": "opening_balance", "scheduled_principal_c": "scheduled_principal",
        "curtailment_c": "curtailment", "closing_balance_c": "closing_balance",
        "exit_balance_c": "exit_balance", "loss_c": "loss",
    }
    for cents, dollars in pairs.items():
        expected = np.round(truth[dollars].to_numpy() * 100).astype(np.int64)
        assert (a[cents].to_numpy(dtype=np.int64) == expected).all(), cents
