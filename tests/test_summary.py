"""Step 6.1: summary outputs on the full database (instruction 06 C, J 6.1)."""

import json
from pathlib import Path

import pytest

from rmbsq.canonical.build import pool_monthly, write_pool_monthly
from rmbsq.db import connect_readonly
from rmbsq.eval.run import load_items
from rmbsq.eval.summary import compiler_check, data_summary
from rmbsq.eval.traps import trap_effects
from rmbsq.semantic.catalog import load_catalog
from rmbsq.synth.generate import run_profile

ROOT = Path(__file__).resolve().parents[1]
GOLD = json.loads((ROOT / "tests" / "fixtures" / "compiler_gold.json").read_text(encoding="utf-8"))

# instruction 06 C.3: chat Claude's values on the full database, to 1e-4
TRAP_VALUES = {
    "Q27": (0.006631, 0.005857),
    "Q29": (0.2156, 1.0000),
    "Q30": (0.1832, 0.4898),
    "Q32": (9975, 10572),
    "Q33": (0.519643, 0.509175),
    "Q2_2025": (0.180644, 0.180632),
}


@pytest.mark.full
def test_data_summary_values(full_db, cfg, tmp_path):
    # pool_monthly.csv rebuilt from the database under test, not read from outputs/
    con = connect_readonly(full_db)
    try:
        write_pool_monthly(pool_monthly(con), tmp_path / "pool_monthly.csv")
    finally:
        con.close()
    summary = data_summary(full_db, ROOT / "data" / "raw", tmp_path / "pool_monthly.csv",
                           run_profile(cfg, "full")["panel"], cfg)
    print(summary.to_string(index=False))
    stats = dict(zip(summary["stat"], summary["value"]))
    assert stats["n_loan_months"] == 773336
    assert stats["n_raw_rows"] == 774057
    assert stats["n_resubmission_duplicates"] == 721
    assert stats["n_called_deals"] == 17
    assert stats["n_called_deals_b"] == 7
    assert stats["canonical_truth_mismatches"] == 0


@pytest.mark.full
def test_compiler_check(full_db):
    check = compiler_check(full_db, GOLD, load_items(ROOT / "eval" / "questions.yaml"), load_catalog())
    print(check.to_string(index=False))
    assert len(check) == 49
    assert list(check["source"]) == ["compiler_gold"] * 15 + ["eval"] * 34
    assert (check["max_scaled_diff"].astype(float) <= 1e-9).all()
    assert check["oracle_ok"].all()


@pytest.mark.full
def test_trap_effects(full_db):
    con = connect_readonly(full_db)
    try:
        traps = trap_effects(con, load_catalog())
    finally:
        con.close()
    print(traps.to_string(index=False))
    assert list(traps["item_id"]) == list(TRAP_VALUES)
    for _, r in traps.iterrows():
        gold, naive = TRAP_VALUES[r["item_id"]]
        assert abs(r["gold"] - gold) <= 1e-4, r["item_id"]
        assert abs(r["naive"] - naive) <= 1e-4, r["item_id"]
