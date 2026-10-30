"""Step 3.3: compiler and time aggregation (instruction 03 B, D, E 3.3).

Each gold spec's compiled result is compared with its hand SQL's result: identical
columns and row order, dimension values equal as strings, metric values within 1e-9
after scaling by max(1, |value|), and the gold row count.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rmbsq.db import connect_readonly
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.compiler import compile, execute
from rmbsq.semantic.spec import QuerySpec
from rmbsq.semantic.timeagg import aggregate

GOLD = json.loads((Path(__file__).parent / "fixtures" / "compiler_gold.json").read_text(encoding="utf-8"))
TOL = 1e-9  # instruction 03 E 3.3


def max_scaled_diff(got: pd.DataFrame, want: pd.DataFrame, metrics: list[str]) -> float:
    """Asserts the 3.3 rule except the tolerance, and returns the max scaled difference."""
    assert list(got.columns) == list(want.columns)
    assert len(got) == len(want)
    worst = 0.0
    for c in got.columns:
        if c in metrics:
            a = got[c].astype("float64").to_numpy()
            b = want[c].astype("float64").to_numpy()
            assert (np.isnan(a) == np.isnan(b)).all(), c
            ok = ~np.isnan(b)
            if ok.any():
                worst = max(worst, float(np.max(np.abs(a[ok] - b[ok]) / np.maximum(1.0, np.abs(b[ok])))))
        else:
            assert [str(v) for v in got[c]] == [str(v) for v in want[c]], c
    return worst


def run_gold(db: Path, item: dict, route: str = "auto") -> tuple[pd.DataFrame, pd.DataFrame, str]:
    spec = QuerySpec.model_validate(item["spec"])
    compiled = compile(spec, load_catalog(), route=route)
    con = connect_readonly(db)
    try:
        got = execute(compiled, con)
        want = con.execute(item["hand_sql"]).df()
    finally:
        con.close()
    return got, want, compiled.route


@pytest.mark.parametrize("item", GOLD, ids=lambda g: g["id"])
def test_fifteen_specs_match_hand_sql(small_db, item):
    got, want, _ = run_gold(small_db, item)
    assert max_scaled_diff(got, want, item["spec"]["metrics"]) <= TOL
    assert len(got) == item["rows_small"]


@pytest.mark.full
@pytest.mark.parametrize("item", GOLD, ids=lambda g: g["id"])
def test_full_fifteen_specs_match_hand_sql(full_db, item):
    got, want, _ = run_gold(full_db, item)
    assert max_scaled_diff(got, want, item["spec"]["metrics"]) <= TOL
    assert len(got) == item["rows_full"]


def _quarter(smm: list[float], dens: list[float]) -> pd.DataFrame:
    """A constructed 1-group monthly parts frame for 2025-Q1 (instruction 03 B.8)."""
    parts = pd.DataFrame({
        "period": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
        "period_label": "2025-Q1",
        "smm_den": dens,
    })
    parts["smm_num"] = [m * d for m, d in zip(smm, dens)]
    for p in ("loan_count", "bal", "a30_bal", "a90_bal", "a90_cnt", "hard_bal", "orig_ltv_x_bal",
              "idx_ltv_x_bal", "rate_x_bal", "mdr_num", "mdr_den"):
        parts[p] = 0
    return parts


def test_quarter_compounding_hand_example():
    cat = load_catalog()
    metrics = [cat.metrics["cpr"], cat.metrics["smm_vol"]]
    full = aggregate(_quarter([0.01, 0.02, 0.015], [1e6, 1e6, 1e6]), [], metrics)
    survival = 0.99 * 0.98 * 0.985
    assert survival == pytest.approx(0.955647, abs=1e-10)
    assert 1 - survival == pytest.approx(0.044353, abs=1e-10)
    assert full["cpr"].iloc[0] == pytest.approx(0.16595400138, abs=1e-10)
    assert full["smm_vol"].iloc[0] == pytest.approx(0.01500846031, abs=1e-10)

    missing = aggregate(_quarter([0.01, 0.02, 0.0], [1e6, 1e6, 0.0]), [], metrics)
    assert 0.99 * 0.98 == pytest.approx(0.9702, abs=1e-10)
    assert missing["cpr"].iloc[0] == pytest.approx(0.16599698292, abs=1e-10)
