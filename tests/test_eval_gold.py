"""Step 5.1: every answer item's gold spec, compiled, equals its gold SQL (instruction 05 F 5.1)."""

from pathlib import Path

import pytest

from rmbsq.db import connect_readonly
from rmbsq.eval.run import load_items
from rmbsq.eval.score import compare_result
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.compiler import compile, execute

ROOT = Path(__file__).resolve().parents[1]
ANSWERS = [i for i in load_items(ROOT / "eval" / "questions.yaml") if i.gold_spec is not None]


@pytest.mark.full
@pytest.mark.parametrize("item", ANSWERS, ids=[i.id for i in ANSWERS])
def test_gold_spec_equals_gold_sql(full_db, cfg, item):
    con = connect_readonly(full_db)
    try:
        got = execute(compile(item.gold_spec, load_catalog()), con)
        gold = con.execute(item.gold_sql).df()
    finally:
        con.close()
    check = compare_result(got, gold, item.gold_spec, item.output_columns)
    print(item.id, len(gold), check)
    assert len(gold) >= 1
    assert check.correct, check.reason
    assert check.n_values_checked == len(gold) * len(item.gold_spec.metrics)
    # kickoff 6.11: the gold check holds to gold_tol_abs as well
    assert check.max_abs_err <= cfg.eval.gold_tol_abs
