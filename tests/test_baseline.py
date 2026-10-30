"""Step 4.5: the free text-to-SQL baseline (instruction 04 G)."""

import dataclasses
import time

import pytest

from rmbsq.db import connect_readonly
from rmbsq.llm.baseline import (TOOL, TOOL_CHOICE, BaselineError, baseline_message, baseline_sql, baseline_system,
                                run_baseline_sql)
from rmbsq.llm.client import LLMClient
from tests.llm_helpers import response, seed

QUESTION = "What is the balance by originator now?"
COLUMNS = ["originator", "period_label", "balance_total"]


def ask(cfg, tmp_path, fixture: str) -> str:
    client = LLMClient(cfg, cache_dir=tmp_path)
    seed(client, baseline_system(cfg), [{"role": "user", "content": baseline_message(QUESTION, COLUMNS)}],
         [TOOL], TOOL_CHOICE, fixture)
    return baseline_sql(QUESTION, COLUMNS, client, cfg)


def test_baseline_parse(cfg, tmp_path):
    assert baseline_message(QUESTION, COLUMNS) == (
        "What is the balance by originator now?\n\nOutput columns, in order: originator, period_label, balance_total")
    assert ask(cfg, tmp_path, "baseline_sql") == response("baseline_sql")["content"][0]["input"]["sql"]
    assert ask(cfg, tmp_path / "empty", "baseline_empty") == ""
    assert "{{" not in baseline_system(cfg)


def test_baseline_timeout(cfg, small_db):
    short = dataclasses.replace(cfg, llm=dataclasses.replace(cfg.llm, baseline_timeout_s=1))
    con = connect_readonly(small_db)
    try:
        t0 = time.perf_counter()
        with pytest.raises(BaselineError):
            run_baseline_sql("SELECT SUM(range) FROM range(100000000000)", con, short)
        elapsed = time.perf_counter() - t0
        assert elapsed < 3
        assert con.execute("SELECT 1").fetchone() == (1,)
    finally:
        con.close()


def test_baseline_cannot_write(cfg, small_db, tmp_path):
    target = tmp_path / "out.csv"
    con = connect_readonly(small_db)
    try:
        with pytest.raises(BaselineError):
            run_baseline_sql(f"COPY (SELECT 1 AS a) TO '{target.as_posix()}'", con, cfg)
    finally:
        con.close()
    assert not target.exists()


def test_baseline_runs_select(cfg, small_db):
    con = connect_readonly(small_db)
    try:
        df = run_baseline_sql(response("baseline_sql")["content"][0]["input"]["sql"], con, cfg)
        assert run_baseline_sql("", con, cfg) is None
    finally:
        con.close()
    assert list(df.columns) == COLUMNS
    assert len(df) == 4 and df["balance_total"].notna().all()
