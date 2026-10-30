"""Steps 5.3 and 5.6: the eval runner in replay against fixture caches (instruction 05 D,
F 5.3, F 5.6).

The cache for Q02, Q35 and Q39 is written into a temp dir with the client's own key
function (tests/llm_helpers.py), and the outputs go to a temp dir. No test reads
`data/llm_cache/`.
"""

import csv
import io
import json
import re
from pathlib import Path

import pytest

from rmbsq.db import connect_readonly
from rmbsq.eval.report import RESULT_COLUMNS, SUMMARY_COLUMNS, TRAP_COLUMNS
from rmbsq.eval.run import load_items, run_eval
from rmbsq.llm.baseline import TOOL as SQL_TOOL
from rmbsq.llm.baseline import TOOL_CHOICE as SQL_CHOICE
from rmbsq.llm.baseline import baseline_message, baseline_system
from rmbsq.llm.client import LLMClient
from rmbsq.llm.narrate import narrate_message, narrate_system
from rmbsq.llm.spec_agent import TOOL_CHOICE, render_spec_prompt, spec_tool
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.compiler import compile, execute
from rmbsq.semantic.format import format_table
from tests.llm_helpers import seed

ROOT = Path(__file__).resolve().parents[1]
ITEMS = {i.id: i for i in load_items(ROOT / "eval" / "questions.yaml")}
THREE = [ITEMS["Q02"], ITEMS["Q35"], ITEMS["Q39"]]
BAD_SQL = "SELECT * FROM no_such_table"
FLOAT = re.compile(r"^-?\d+\.\d{10}$")


def tool_response(name: str, tool_input: dict, input_tokens: int, output_tokens: int) -> dict:
    return {"id": f"msg_{name}", "type": "message", "role": "assistant", "model": "claude-sonnet-5-5",
            "content": [{"type": "tool_use", "id": f"toolu_{name}", "name": name, "input": tool_input}],
            "stop_reason": "tool_use", "stop_sequence": None,
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}}


def text_response(text: str, input_tokens: int, output_tokens: int) -> dict:
    return {"id": "msg_text", "type": "message", "role": "assistant", "model": "claude-sonnet-5-5",
            "content": [{"type": "text", "text": text}], "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}}


@pytest.fixture(scope="module")
def catalog(small_db):
    return load_catalog(db=small_db)


@pytest.fixture(scope="module")
def q02_display(small_db, catalog):
    con = connect_readonly(small_db)
    try:
        table = execute(compile(ITEMS["Q02"].gold_spec, catalog), con)
    finally:
        con.close()
    return format_table(table, catalog)


@pytest.fixture
def cache(cfg, catalog, q02_display, tmp_path):
    """The 6 spec and baseline responses and the 1 narration for Q02, Q35 and Q39."""
    client = LLMClient(cfg, cache_dir=tmp_path / "cache")
    spec_prompt = render_spec_prompt(catalog, cfg)
    q02, q35, q39 = THREE

    def spec_call(item, tool_input, latency):
        seed(client, spec_prompt, [{"role": "user", "content": item.question}], [spec_tool()], TOOL_CHOICE,
             tool_response("submit_spec", tool_input, 3000, 100), latency)

    def sql_call(item, sql, latency):
        cols = list(item.output_columns) if item.output_columns else ["period_label"]
        seed(client, baseline_system(cfg), [{"role": "user", "content": baseline_message(item.question, cols)}],
             [SQL_TOOL], SQL_CHOICE, tool_response("submit_sql", {"sql": sql}, 2000, 50), latency)

    spec_call(q02, q02.gold_spec.model_dump(mode="json"), 1.5)
    balance = q02_display["balance_total"].iloc[0]
    seed(client, narrate_system(cfg),
         [{"role": "user", "content": narrate_message(q02.question, q02.gold_spec, q02_display, cfg)}], [], None,
         text_response(f"The pool's outstanding balance at 2026-09 was {balance}.", 800, 30), 0.25)
    spec_call(q35, {"intent": "clarify", "clarify": {"question": "Which arrears threshold do you mean?",
                                                      "options": ["30+ days", "90+ days"]}}, 1.25)
    spec_call(q39, {"intent": "unsupported", "unsupported_reason": "Borrower income is not in the data."}, 1.0)
    sql_call(q02, q02.gold_sql, 2.0)
    sql_call(q35, BAD_SQL, 2.5)
    sql_call(q39, "", 0.5)
    return client.cache_dir


def read_csv(path: Path) -> list[dict]:
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))


def test_runner_three_items(cfg, small_db, cache, tmp_path):
    out = tmp_path / "out"
    run_eval(THREE, small_db, cache, out, cfg, mode="replay")
    rows = {(r["system"], r["item_id"]): r for r in read_csv(out / "eval_results.csv")}
    assert list(rows) == [("system", "Q02"), ("system", "Q35"), ("system", "Q39"),
                          ("baseline", "Q02"), ("baseline", "Q35"), ("baseline", "Q39")]
    keep = ["category", "intent", "correct", "n_values_checked", "max_abs_err", "latency_s", "input_tokens",
            "output_tokens", "guard_tripped"]
    got = {k: [r[c] for c in keep] for k, r in rows.items()}
    assert got[("system", "Q02")] == ["simple", "answer", "True", "1", "0.0000000000", "1.7500000000", "3800",
                                      "130", "False"]
    assert got[("system", "Q35")] == ["ambiguous", "clarify", "True", "0", "", "1.2500000000", "3000", "100",
                                      "False"]
    assert got[("system", "Q39")] == ["unsupported", "unsupported", "True", "0", "", "1.0000000000", "3000",
                                      "100", "False"]
    assert got[("baseline", "Q02")] == ["simple", "sql", "True", "1", "0.0000000000", "2.0000000000", "2000",
                                        "50", ""]
    assert got[("baseline", "Q35")] == ["ambiguous", "error", "False", "0", "", "2.5000000000", "2000", "50", ""]
    assert got[("baseline", "Q39")] == ["unsupported", "decline", "True", "0", "", "0.5000000000", "2000", "50",
                                        ""]
    assert rows[("baseline", "Q35")]["error"].startswith("Catalog Error")
    assert all(r["error"] == "" for k, r in rows.items() if k != ("baseline", "Q35"))


def test_runner_formats(cfg, small_db, cache, tmp_path):
    out = tmp_path / "out"
    run_eval(THREE, small_db, cache, out, cfg, mode="replay")
    for name in ["eval_results.csv", "eval_summary.csv", "trap_failures.csv", "eval_detail.jsonl"]:
        data = (out / name).read_bytes()
        assert b"\r" not in data and data.endswith(b"\n"), name

    results = (out / "eval_results.csv").read_text(encoding="utf-8").split("\n")
    assert results[0] == ",".join(RESULT_COLUMNS)
    for r in read_csv(out / "eval_results.csv"):
        for c in ["max_abs_err", "latency_s"]:
            assert r[c] == "" or FLOAT.match(r[c]), (c, r[c])

    summary = read_csv(out / "eval_summary.csv")
    assert (out / "eval_summary.csv").read_text(encoding="utf-8").split("\n")[0] == ",".join(SUMMARY_COLUMNS)
    assert [(r["system"], r["category"], r["n"], r["k"]) for r in summary] == [
        ("system", "simple", "1", "1"), ("system", "ambiguous", "1", "1"), ("system", "unsupported", "1", "1"),
        ("system", "total", "3", "3"),
        ("baseline", "simple", "1", "1"), ("baseline", "ambiguous", "1", "0"), ("baseline", "unsupported", "1", "1"),
        ("baseline", "total", "3", "2")]
    for r in summary:
        assert all(FLOAT.match(r[c]) for c in ["accuracy", "wilson_lo", "wilson_hi"])
    assert summary[7]["accuracy"] == "0.6666666667"

    assert (out / "trap_failures.csv").read_text(encoding="utf-8") == ",".join(TRAP_COLUMNS) + "\n"

    lines = (out / "eval_detail.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 6
    for line in lines:
        assert json.dumps(json.loads(line), sort_keys=True, ensure_ascii=False) == line
    detail = [json.loads(line) for line in lines]
    assert set(detail[0]) == {"system", "item_id", "question", "intent", "spec", "sql_duckdb", "columns", "rows",
                              "text", "offending", "correct", "error"}
    assert set(detail[3]) == {"system", "item_id", "question", "intent", "sql", "columns", "rows", "correct",
                              "error"}
    assert detail[0]["columns"] == ["period_label", "balance_total"]
    assert detail[0]["rows"][0][0] == "2026-09" and detail[0]["rows"][0][1].startswith("A$")
    assert detail[0]["text"].startswith("The pool's outstanding balance at 2026-09 was A$")
    assert detail[1]["text"] == "Which arrears threshold do you mean?\nOptions: 30+ days; 90+ days"
    assert detail[1]["spec"]["intent"] == "clarify" and detail[1]["rows"] == []
    assert detail[3]["rows"] == detail[0]["rows"]
    assert detail[5]["sql"] == "" and detail[5]["intent"] == "decline"


def test_record_with_full_cache_matches_replay(cfg, small_db, cache, tmp_path):
    """Record mode on a full cache makes no call (sockets are disabled) and writes the same files."""
    run_eval(THREE, small_db, cache, tmp_path / "replay", cfg, mode="replay")
    run_eval(THREE, small_db, cache, tmp_path / "record", cfg, mode="record")
    for name in ["eval_results.csv", "eval_summary.csv", "trap_failures.csv", "eval_detail.jsonl"]:
        assert (tmp_path / "replay" / name).read_bytes() == (tmp_path / "record" / name).read_bytes()
