"""Step 2.6: the canonical layer equals the true panel (instruction 02 B, D 2.6).

fact_loan_month, built from the raw trustee files, is joined to the true panel from
`simulate` on loan_id and period and compared on every column they share.
"""

import duckdb
import numpy as np
import pandas as pd
import pytest

from rmbsq.synth.generate import run_profile

MONEY = ["opening_balance", "scheduled_principal", "curtailment", "closing_balance", "exit_balance", "loss"]
FLOATS = ["interest_rate", "indexed_value", "indexed_ltv"]
EXACT = ["dpd_bucket", "hardship_flag", "exit_reason"]

FACT_SQL = (
    "SELECT loan_id, period, "
    + ", ".join(f"CAST(round({c} * 100) AS BIGINT) AS {c}" for c in MONEY)
    + ", " + ", ".join(FLOATS + EXACT)
    + " FROM fact_loan_month"
)


def _assert_equal(db, panel: pd.DataFrame):
    con = duckdb.connect(str(db), read_only=True)
    fact = con.execute(FACT_SQL).df()
    con.close()
    fact["loan_id"] = fact["loan_id"].astype(str)
    fact["period"] = pd.to_datetime(fact["period"]).astype("datetime64[ns]")
    truth = panel.assign(loan_id=panel["loan_id"].astype(str))
    joined = fact.merge(truth, on=["loan_id", "period"], how="outer", suffixes=("_c", "_t"), indicator=True)

    assert len(fact) == len(truth)
    assert (joined["_merge"] == "both").all(), joined["_merge"].value_counts()

    for col in MONEY:
        expected = np.round(joined[f"{col}_t"].to_numpy() * 100).astype(np.int64)
        assert (joined[f"{col}_c"].to_numpy(dtype=np.int64) == expected).all(), col
    for col in FLOATS:
        diff = np.abs(joined[f"{col}_c"].to_numpy(dtype=float) - joined[f"{col}_t"].to_numpy(dtype=float))
        assert diff.max() <= 1e-9, (col, diff.max())
    assert (joined["dpd_bucket_c"].to_numpy(dtype=np.int64) == joined["dpd_bucket_t"].to_numpy(dtype=np.int64)).all()
    assert (joined["hardship_flag_c"].to_numpy(dtype=bool) == joined["hardship_flag_t"].to_numpy(dtype=bool)).all()
    reason_c = joined["exit_reason_c"].astype(object).where(joined["exit_reason_c"].notna(), None)
    reason_t = joined["exit_reason_t"].astype(object).where(joined["exit_reason_t"].notna(), None)
    assert (reason_c.to_numpy() == reason_t.to_numpy()).all()


def test_canonical_equals_truth_panel(small_db, small):
    _assert_equal(small_db, small["panel"])


@pytest.mark.full
def test_full_canonical_equals_truth_panel(full_db, cfg):
    _assert_equal(full_db, run_profile(cfg, "full")["panel"])
