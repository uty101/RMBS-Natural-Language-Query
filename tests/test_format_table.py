"""Step 3.6: display formatting (kickoff 5.2, 5.3; instruction 03 E 3.6)."""

import numpy as np
import pandas as pd

from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.format import format_table


def test_display_rules():
    df = pd.DataFrame({
        "issue_year": pd.array([2019, 2023, 2021], dtype="int64"),
        "deal_name": ["HARB 2019-1", "RED 2023-2", "KOO 2021-1"],
        "period_label": ["2026-09", "2025-Q2", "range"],
        "arrears_90p_bal": [0.0412, np.nan, 0.000125],
        "balance_total": [412_345_678.9, 999_950.0, np.nan],
        "loan_count": pd.array([12345, None, 7], dtype="Int64"),
    })
    out = format_table(df, load_catalog())
    assert out.to_dict("list") == {
        "issue_year": ["2019", "2023", "2021"],
        "deal_name": ["HARB 2019-1", "RED 2023-2", "KOO 2021-1"],
        "period_label": ["2026-09", "2025-Q2", "range"],
        # 0.000125: Python's format gives 0.01% (recorded, not changed; instruction 03 E 3.6)
        "arrears_90p_bal": ["4.12%", "n/a", "0.01%"],
        "balance_total": ["A$412.3m", "A$1.0m", "n/a"],
        "loan_count": ["12,345", "n/a", "7"],
    }
    assert all(isinstance(v, str) for col in out.columns for v in out[col])
