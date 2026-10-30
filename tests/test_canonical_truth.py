"""Step 2.6: the canonical layer equals the true panel (instruction 02 B, D 2.6).

fact_loan_month, built from the raw trustee files, is joined to the true panel from
`simulate` on loan_id and period and compared on every column they share. The comparison
lives in `rmbsq/canonical/truth_check.py` (instruction 06 C.1).
"""

import pytest

from rmbsq.canonical.truth_check import MONEY, FLOATS, EXACT, truth_check
from rmbsq.synth.generate import run_profile


def _assert_equal(db, panel):
    check = truth_check(db, panel)
    assert check.n_fact == check.n_truth
    assert check.unmatched == 0
    for col in [*MONEY, *FLOATS, *EXACT]:
        assert check.column_mismatches[col] == 0, col
    assert check.mismatched_rows == 0


def test_canonical_equals_truth_panel(small_db, small):
    _assert_equal(small_db, small["panel"])


@pytest.mark.full
def test_full_canonical_equals_truth_panel(full_db, cfg):
    _assert_equal(full_db, run_profile(cfg, "full")["panel"])
