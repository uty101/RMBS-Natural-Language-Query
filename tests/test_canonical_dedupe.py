"""Step 2.2: resubmissions (kickoff 4.8 trap 4, 6.2; instruction 02 D 2.2)."""

import numpy as np
import pandas as pd

from rmbsq.canonical.build import dedupe_resubmissions, ingest_raw


def test_resubmission_months_one_row_true_values(small_raw, small):
    raw = ingest_raw(small_raw)
    month = pd.Timestamp("2023-06-01")
    before = raw[(raw["deal_id"] == "D004") & (raw["period"] == month)]
    assert set(before["submission_seq"]) == {1, 2}
    after = dedupe_resubmissions(raw)
    rows = after[(after["deal_id"] == "D004") & (after["period"] == month)].set_index("loan_id").sort_index()
    assert rows.index.is_unique
    assert len(rows) == len(before) // 2
    truth = small["panel"]
    truth = truth[(truth["deal_id"] == "D004") & (truth["period"] == month)].set_index("loan_id").sort_index()
    assert list(rows.index) == list(truth.index)
    for cents, dollars in [("closing_balance_c", "closing_balance"), ("curtailment_c", "curtailment")]:
        expected = np.round(truth[dollars].to_numpy() * 100).astype(np.int64)
        assert (rows[cents].to_numpy(dtype=np.int64) == expected).all(), cents


def test_no_duplicates_after_dedupe(small_raw):
    raw = ingest_raw(small_raw)
    assert raw.duplicated(["loan_id", "period"]).any()
    after = dedupe_resubmissions(raw)
    assert not after.duplicated(["loan_id", "period"]).any()
