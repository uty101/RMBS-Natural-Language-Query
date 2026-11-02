"""Step 8c.1: structured-output wire schemas and parsing (instruction 08c B, C.3)."""

import json
from pathlib import Path

import pytest

from rmbsq.db import connect_readonly
from rmbsq.eval.run import load_items, run_baseline
from rmbsq.llm.baseline import BaselineResponseError, baseline_message, baseline_sql, baseline_system
from rmbsq.llm.client import LLMClient
from rmbsq.llm.spec_agent import question_to_spec, render_spec_prompt
from rmbsq.llm.wire import BASELINE_WIRE_SCHEMA, output_config, spec_wire_schema, wire_to_spec
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.spec import QuerySpec
from tests.llm_helpers import response, seed

ROOT = Path(__file__).resolve().parents[1]
GOLD = {g["id"]: g for g in json.loads(
    (Path(__file__).parent / "fixtures" / "compiler_gold.json").read_text(encoding="utf-8"))}
BANNED = {"maxItems", "minLength", "maxLength", "minimum", "maximum", "$ref"}
QUESTION = "What is the balance by originator now?"
COLUMNS = ["originator", "period_label", "balance_total"]


@pytest.fixture(scope="module")
def catalog(small_db):
    return load_catalog(db=small_db)


def ask_spec(cfg, catalog, tmp_path, resp, question="What is the balance and loan count by originator?"):
    client = LLMClient(cfg, cache_dir=tmp_path)
    seed(client, render_spec_prompt(catalog, cfg), [{"role": "user", "content": question}],
         output_config(spec_wire_schema(catalog)), resp)
    return question_to_spec(question, client, catalog)


def seed_baseline(cfg, tmp_path, resp, question=QUESTION, columns=COLUMNS):
    client = LLMClient(cfg, cache_dir=tmp_path)
    seed(client, baseline_system(cfg), [{"role": "user", "content": baseline_message(question, columns)}],
         output_config(BASELINE_WIRE_SCHEMA), resp)
    return client


def json_response(obj: dict) -> dict:
    return {"id": "msg_wire", "type": "message", "role": "assistant", "model": "claude-sonnet-5-5",
            "content": [{"type": "text", "text": json.dumps(obj)}], "stop_reason": "end_turn",
            "stop_sequence": None, "usage": {"input_tokens": 3100, "output_tokens": 60}}


def walk(node, found: list):
    if isinstance(node, dict):
        if node.get("type") == "object":
            found.append(node)
        for key, value in node.items():
            assert key not in BANNED, key
            if key == "minItems":
                assert value <= 1
            walk(value, found)
    elif isinstance(node, list):
        for value in node:
            walk(value, found)


def test_wire_schema_supported(catalog):
    for schema in (spec_wire_schema(catalog), BASELINE_WIRE_SCHEMA):
        objects = []
        walk(schema, objects)
        assert objects
        for obj in objects:
            assert obj["additionalProperties"] is False
            assert set(obj["required"]) == set(obj["properties"])
    spec = spec_wire_schema(catalog)
    assert spec["properties"]["metrics"]["items"]["enum"] == list(catalog.metrics)
    assert spec["properties"]["group_by"]["items"]["enum"] == list(catalog.dimensions)
    assert len(catalog.metrics) == 12 and len(catalog.dimensions) == 18


def test_wire_to_spec(cfg, catalog, tmp_path):
    base = {"intent": "answer", "metrics": ["balance_total"], "group_by": [], "order": None,
            "clarify": None, "unsupported_reason": None}
    # a repeated dimension appends its values, deduplicated, in first-seen order
    got = wire_to_spec({**base, "time": None, "filters": [
        {"dimension": "state", "values": ["NSW", "VIC"]},
        {"dimension": "originator", "values": ["KOO"]},
        {"dimension": "state", "values": ["VIC", "QLD"]}]})
    assert got["filters"] == {"state": ["NSW", "VIC", "QLD"], "originator": ["KOO"]}
    assert list(got["filters"]) == ["state", "originator"]
    # time null drops the key, so QuerySpec applies its default
    assert "time" not in got
    assert "clarify" not in got and "unsupported_reason" not in got
    assert QuerySpec.model_validate(got).time is not None
    # a clarify object carrying stray empty lists
    clarify = wire_to_spec({"intent": "clarify", "metrics": [], "group_by": [], "filters": [], "time": None,
                            "order": None, "clarify": {"question": "Which threshold?", "options": ["30+", "90+"]},
                            "unsupported_reason": None})
    assert set(clarify) == {"intent", "clarify", "unsupported_reason"}
    assert QuerySpec.model_validate(clarify).intent == "clarify"
    # an answer object with 4 metrics comes back unsupported with flag False
    four = {**base, "metrics": ["cpr", "cdr", "smm_vol", "loan_count"], "filters": [], "time": None}
    spec, ok = ask_spec(cfg, catalog, tmp_path, json_response(four), "Show cpr, cdr, smm and loan count.")
    assert not ok and spec.intent == "unsupported"
    assert spec.unsupported_reason.startswith("invalid spec from model: metrics: ")


def test_parse_thinking_then_text(cfg, catalog, tmp_path):
    spec, ok = ask_spec(cfg, catalog, tmp_path, "spec_thinking")
    assert response("spec_thinking")["content"][0]["type"] == "thinking"
    assert ok
    assert spec == QuerySpec.model_validate(GOLD["S02"]["spec"])
    client = seed_baseline(cfg, tmp_path / "baseline", {
        **response("spec_thinking"),
        "content": [response("spec_thinking")["content"][0], {"type": "text", "text": '{"sql": "SELECT 1"}'}]})
    assert baseline_sql(QUESTION, COLUMNS, client, cfg) == "SELECT 1"


def _invalid_for_both(cfg, catalog, small_db, tmp_path, fixture, reason):
    spec, ok = ask_spec(cfg, catalog, tmp_path / "spec", fixture)
    assert not ok and spec.intent == "unsupported"
    assert spec.unsupported_reason == f"invalid spec from model: {reason}"
    client = seed_baseline(cfg, tmp_path / "baseline", fixture)
    with pytest.raises(BaselineResponseError, match=reason):
        baseline_sql(QUESTION, COLUMNS, client, cfg)
    # in the eval runner it is intent `error` with the reason as error text, not a decline
    item = next(i for i in load_items(ROOT / "eval" / "questions.yaml") if i.id == "Q02")
    client = seed_baseline(cfg, tmp_path / "run", fixture, item.question, list(item.output_columns))
    con = connect_readonly(small_db)
    try:
        row = run_baseline([item], client, con).iloc[0]
    finally:
        con.close()
    assert (row["intent"], row["sql"], row["ran"]) == ("error", "", False)
    assert reason in row["error"]


def test_parse_refusal(cfg, catalog, small_db, tmp_path):
    _invalid_for_both(cfg, catalog, small_db, tmp_path, "refusal", "stop_reason refusal")


def test_parse_truncated(cfg, catalog, small_db, tmp_path):
    _invalid_for_both(cfg, catalog, small_db, tmp_path, "truncated", "stop_reason max_tokens")
