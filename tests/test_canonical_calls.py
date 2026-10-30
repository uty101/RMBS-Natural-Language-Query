"""Step 2.3: call detection (kickoff 4.8 trap 3, 6.2; instruction 02 C.3, D 2.3)."""

from pathlib import Path

import pandas as pd
import pytest

from rmbsq.canonical.build import dedupe_resubmissions, detect_calls, ingest_raw

ROOT = Path(__file__).resolve().parents[1]

# instruction 02 D 2.3: the 7 called format B deals of the full profile
FULL_B_CALLS = {
    ("D004", "2025-11"): 146,
    ("D005", "2025-04"): 150,
    ("D009", "2026-03"): 154,
    ("D010", "2025-12"): 151,
    ("D014", "2026-02"): 147,
    ("D015", "2026-06"): 148,
    ("D020", "2026-04"): 158,
}


def _frame(n_loans: int, n_prepaid: int) -> pd.DataFrame:
    """1 deal, n_loans active at the end of 2024-01; n_prepaid of them prepay in 2024-02,
    the rest stay active."""
    rows = []
    for i in range(n_loans):
        loan = f"X001-{i + 1:04d}"
        rows.append({"loan_id": loan, "deal_id": "X001", "period": pd.Timestamp("2024-01-01"),
                     "closing_balance_c": 100_000_00, "exit_reason": None})
        exit_ = i < n_prepaid
        rows.append({"loan_id": loan, "deal_id": "X001", "period": pd.Timestamp("2024-02-01"),
                     "closing_balance_c": 0 if exit_ else 99_000_00, "exit_reason": "prepaid" if exit_ else None})
    df = pd.DataFrame(rows)
    return df.astype({"loan_id": "string", "deal_id": "string", "closing_balance_c": "Int64", "exit_reason": "string"})


def _canonical_rows(raw_dir):
    return detect_calls(dedupe_resubmissions(ingest_raw(raw_dir)))


def _called(df):
    c = df[df["exit_reason"] == "called"]
    return set(zip(c["deal_id"], c["period"].dt.strftime("%Y-%m"), c["loan_id"]))


def test_detect_calls_constructed():
    all_ten = detect_calls(_frame(10, 10))
    assert (all_ten["exit_reason"] == "called").sum() == 10
    assert (all_ten["exit_reason"] == "prepaid").sum() == 0
    nine = detect_calls(_frame(10, 9))
    assert (nine["exit_reason"] == "called").sum() == 0
    assert (nine["exit_reason"] == "prepaid").sum() == 9


def test_format_b_calls_recovered(small_raw, small):
    rows = _canonical_rows(small_raw)
    canonical = _called(rows[rows["trustee_format"] == "B"])
    deals = small["deals"]
    b_deals = set(deals.loc[deals["trustee_format"] == "B", "deal_id"])
    truth = small["panel"]
    truth = _called(truth[truth["deal_id"].isin(b_deals)])
    assert canonical == truth


def test_format_a_calls_unchanged(small_raw):
    before = dedupe_resubmissions(ingest_raw(small_raw))
    after = detect_calls(before)
    a = (before["trustee_format"] == "A").to_numpy()
    read_as_call = _called(before[a])
    assert len(read_as_call) > 0
    assert _called(after[a]) == read_as_call
    pd.testing.assert_frame_equal(after[a], before[a])


@pytest.mark.full
def test_full_format_b_calls_recovered():
    rows = _canonical_rows(ROOT / "data" / "raw")
    c = rows[(rows["exit_reason"] == "called") & (rows["trustee_format"] == "B")]
    got = c.groupby(["deal_id", c["period"].dt.strftime("%Y-%m")]).size()
    assert {k: int(v) for k, v in got.items()} == FULL_B_CALLS
