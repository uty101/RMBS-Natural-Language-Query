"""Step 4.6: the pipeline and the CLI (instruction 04 H), all in replay mode."""

import json
from pathlib import Path

import pytest

from rmbsq import cli
from rmbsq.db import connect_readonly
from rmbsq.llm.answer import answer
from rmbsq.llm.client import LLMClient
from rmbsq.llm.narrate import narrate_message, narrate_system
from rmbsq.llm.spec_agent import TOOL_CHOICE, render_spec_prompt, spec_tool
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.format import format_table
from rmbsq.semantic.spec import QuerySpec
from tests.llm_helpers import response, seed
from tests.test_compiler import max_scaled_diff, run_gold

GOLD = {g["id"]: g for g in json.loads(
    (Path(__file__).parent / "fixtures" / "compiler_gold.json").read_text(encoding="utf-8"))}
QUESTION = "What is the balance and loan count by originator?"


@pytest.fixture(scope="module")
def catalog(small_db):
    return load_catalog(db=small_db)


def seed_spec(client, cfg, catalog, question, fixture):
    seed(client, render_spec_prompt(catalog, cfg), [{"role": "user", "content": question}],
         [spec_tool()], TOOL_CHOICE, fixture)


def run(cfg, catalog, small_db, client, question):
    con = connect_readonly(small_db)
    try:
        return answer(question, client, con, catalog, cfg)
    finally:
        con.close()


def test_answer_end_to_end_replay(cfg, catalog, small_db, tmp_path):
    client = LLMClient(cfg, cache_dir=tmp_path)
    seed_spec(client, cfg, catalog, QUESTION, "spec_answer")
    _, gold, _ = run_gold(small_db, GOLD["S02"])
    spec = QuerySpec.model_validate(GOLD["S02"]["spec"])
    seed(client, narrate_system(cfg),
         [{"role": "user", "content": narrate_message(QUESTION, spec, format_table(gold, catalog), cfg)}],
         [], None, "narrate_s02")

    result = run(cfg, catalog, small_db, client, QUESTION)
    assert result.spec_valid and result.spec == spec and result.route == "agg"
    assert max_scaled_diff(result.table, gold, spec.metrics) == 0.0
    assert result.text == response("narrate_s02")["content"][0]["text"]
    assert (result.guard_tripped, result.offending) == (False, [])
    assert [c["hit"] for c in result.calls] == [True, True]
    assert "TO_DATE" in result.sql_oracle


def test_answer_clarify(cfg, catalog, small_db, tmp_path):
    client = LLMClient(cfg, cache_dir=tmp_path)
    seed_spec(client, cfg, catalog, "How are arrears trending?", "spec_clarify")
    result = run(cfg, catalog, small_db, client, "How are arrears trending?")
    assert result.spec.intent == "clarify" and result.table is None and result.sql_duckdb is None
    assert result.text == "Which arrears threshold do you mean?\nOptions: 30+ days; 90+ days"
    assert len(result.calls) == 1


def test_answer_unsupported(cfg, catalog, small_db, tmp_path):
    client = LLMClient(cfg, cache_dir=tmp_path)
    seed_spec(client, cfg, catalog, "What is the average borrower income?", "spec_unsupported")
    result = run(cfg, catalog, small_db, client, "What is the average borrower income?")
    assert result.spec.intent == "unsupported" and result.display is None
    assert result.text == "Borrower income is not in the data."


def test_cli_cache_miss_exit_2(small_db, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)  # the relative data/llm_cache/ is then an empty temp folder
    assert cli.main(["ask", "What is the balance by originator?", "--db", str(small_db)]) == 2
    assert "not in the cache; run with --live" in capsys.readouterr().err
    assert not (tmp_path / "data").exists()
