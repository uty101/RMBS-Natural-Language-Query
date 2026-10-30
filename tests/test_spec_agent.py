"""Step 4.2: the spec agent (instruction 04 D)."""

import json
from pathlib import Path

import pytest

from rmbsq.llm.client import LLMClient
from rmbsq.llm.spec_agent import TOOL_CHOICE, question_to_spec, render_spec_prompt, spec_input_schema, spec_tool
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.spec import QuerySpec
from tests.llm_helpers import seed

GOLD = {g["id"]: g for g in json.loads(
    (Path(__file__).parent / "fixtures" / "compiler_gold.json").read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def catalog(small_db):
    return load_catalog(db=small_db)


def ask(cfg, catalog, tmp_path, question: str, fixture: str) -> tuple[QuerySpec, bool]:
    client = LLMClient(cfg, cache_dir=tmp_path)
    seed(client, render_spec_prompt(catalog, cfg), [{"role": "user", "content": question}],
         [spec_tool()], TOOL_CHOICE, fixture)
    return question_to_spec(question, client, catalog)


def test_prompt_has_every_name(cfg, catalog):
    prompt = render_spec_prompt(catalog, cfg)
    assert len(catalog.metrics) == 12 and len(catalog.dimensions) == 18
    for name in [*catalog.metrics, *catalog.dimensions]:
        assert f"| {name} |" in prompt
        assert f"- {name}: " in prompt or name in catalog.metrics
    assert "{{" not in prompt and "}}" not in prompt


def test_tool_schema_inlined():
    text = json.dumps(spec_input_schema())
    assert "$ref" not in text and "$defs" not in text

    def keys(node):
        if isinstance(node, dict):
            yield from node
            for v in node.values():
                yield from keys(v)
        elif isinstance(node, list):
            for v in node:
                yield from keys(v)

    assert "title" not in set(keys(spec_input_schema()))
    tool = spec_tool()
    assert tool["name"] == "submit_spec" and tool["description"] == "Submit the query spec for the question."


def test_parse_fixture_answer(cfg, catalog, tmp_path):
    spec, ok = ask(cfg, catalog, tmp_path, "What is the balance and loan count by originator?", "spec_answer")
    assert ok
    assert spec == QuerySpec.model_validate(GOLD["S02"]["spec"])


def test_parse_fixture_clarify(cfg, catalog, tmp_path):
    spec, ok = ask(cfg, catalog, tmp_path, "How are arrears trending?", "spec_clarify")
    assert ok and spec.intent == "clarify"
    assert spec.clarify.options == ["30+ days", "90+ days"]


def test_parse_fixture_unsupported(cfg, catalog, tmp_path):
    spec, ok = ask(cfg, catalog, tmp_path, "What is the average borrower income?", "spec_unsupported")
    assert ok and spec.intent == "unsupported"
    assert spec.unsupported_reason == "Borrower income is not in the data."


def test_parse_invalid_spec(cfg, catalog, tmp_path):
    spec, ok = ask(cfg, catalog, tmp_path, "Show cpr, cdr, smm and loan count.", "spec_four_metrics")
    assert not ok and spec.intent == "unsupported"
    assert spec.unsupported_reason.startswith("invalid spec from model: metrics: ")
    assert len(spec.unsupported_reason) <= len("invalid spec from model: ") + 200


def test_parse_missing_tool_block(cfg, catalog, tmp_path):
    spec, ok = ask(cfg, catalog, tmp_path, "Tell me something.", "spec_text_only")
    assert not ok and spec.intent == "unsupported"
    assert spec.unsupported_reason.startswith("invalid spec from model: ")
