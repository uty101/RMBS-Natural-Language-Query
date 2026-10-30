"""The canonical layer against the true panel (instruction 02 B, D 2.6; instruction 06 C.1).

fact_loan_month, built from the raw trustee files, is joined to the true panel from
`simulate` on loan_id and period and compared on every column they share: money in whole
cents, the float columns within 1e-9, and the bucket, flag and exit reason exactly.
Moved here from `tests/test_canonical_truth.py` so the test and `scripts/build_summary.py`
use the same comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from rmbsq.db import connect_readonly

MONEY = ["opening_balance", "scheduled_principal", "curtailment", "closing_balance", "exit_balance", "loss"]
FLOATS = ["interest_rate", "indexed_value", "indexed_ltv"]
EXACT = ["dpd_bucket", "hardship_flag", "exit_reason"]
FLOAT_TOL = 1e-9  # the step 2.6 rule (instruction 02 D 2.6)

FACT_SQL = (
    "SELECT loan_id, period, "
    + ", ".join(f"CAST(round({c} * 100) AS BIGINT) AS {c}" for c in MONEY)
    + ", " + ", ".join(FLOATS + EXACT)
    + " FROM fact_loan_month"
)


@dataclass(frozen=True)
class TruthCheck:
    n_fact: int
    n_truth: int
    unmatched: int                                   # rows of the outer join not in both
    column_mismatches: dict[str, int] = field(default_factory=dict)  # per column, over matched rows
    mismatched_rows: int = 0                         # unmatched rows plus matched rows with any mismatch


def _column_masks(both: pd.DataFrame) -> dict[str, np.ndarray]:
    masks = {}
    for col in MONEY:
        expected = np.round(both[f"{col}_t"].to_numpy() * 100).astype(np.int64)
        masks[col] = both[f"{col}_c"].to_numpy(dtype=np.int64) != expected
    for col in FLOATS:
        diff = np.abs(both[f"{col}_c"].to_numpy(dtype=float) - both[f"{col}_t"].to_numpy(dtype=float))
        masks[col] = ~(diff <= FLOAT_TOL)
    masks["dpd_bucket"] = both["dpd_bucket_c"].to_numpy(dtype=np.int64) != both["dpd_bucket_t"].to_numpy(dtype=np.int64)
    masks["hardship_flag"] = both["hardship_flag_c"].to_numpy(dtype=bool) != both["hardship_flag_t"].to_numpy(dtype=bool)
    reason_c = both["exit_reason_c"].astype(object).where(both["exit_reason_c"].notna(), None)
    reason_t = both["exit_reason_t"].astype(object).where(both["exit_reason_t"].notna(), None)
    masks["exit_reason"] = reason_c.to_numpy() != reason_t.to_numpy()
    return masks


def truth_check(db, panel: pd.DataFrame) -> TruthCheck:
    con = connect_readonly(db)
    try:
        fact = con.execute(FACT_SQL).df()
    finally:
        con.close()
    fact["loan_id"] = fact["loan_id"].astype(str)
    fact["period"] = pd.to_datetime(fact["period"]).astype("datetime64[ns]")
    truth = panel.assign(loan_id=panel["loan_id"].astype(str))
    joined = fact.merge(truth, on=["loan_id", "period"], how="outer", suffixes=("_c", "_t"), indicator=True)
    matched = (joined["_merge"] == "both").to_numpy()
    masks = _column_masks(joined[matched])
    any_bad = np.zeros(int(matched.sum()), dtype=bool)
    for mask in masks.values():
        any_bad |= mask
    return TruthCheck(n_fact=len(fact), n_truth=len(truth), unmatched=int((~matched).sum()),
                      column_mismatches={c: int(m.sum()) for c, m in masks.items()},
                      mismatched_rows=int((~matched).sum() + any_bad.sum()))
