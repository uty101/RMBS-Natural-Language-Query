"""Step 4.4: narration, the number guard and the template answer (instruction 04 F)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from rmbsq.llm.client import LLMClient
from rmbsq.llm.guard import number_guard
from rmbsq.llm.narrate import narrate, narrate_system, template_answer
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.spec import QuerySpec
from tests.llm_helpers import response, seed

FIXTURES = Path(__file__).parent / "fixtures"
GUARD = json.loads((FIXTURES / "guard_cases.json").read_text(encoding="utf-8"))
GOLD = {g["id"]: g for g in json.loads((FIXTURES / "compiler_gold.json").read_text(encoding="utf-8"))}
S02 = QuerySpec.model_validate(GOLD["S02"]["spec"])
QUESTION = "What is the balance and loan count by originator?"


@pytest.fixture(scope="module")
def catalog(small_db):
    return load_catalog(db=small_db)


def table(name: str) -> pd.DataFrame:
    t = GUARD["tables"][name]
    return pd.DataFrame(t["rows"], columns=t["columns"])


@pytest.mark.parametrize("case", GUARD["cases"], ids=lambda c: c["id"])
def test_guard_cases(catalog, case):
    assert number_guard(case["text"], case["question"], table(case["table"]), catalog) == case["offending"]


def _narrate(cfg, catalog, tmp_path, display, fixture, spec=S02, question=QUESTION, message=None):
    client = LLMClient(cfg, cache_dir=tmp_path)
    message = message or json.dumps(
        {"question": question, "spec": spec.model_dump(mode="json"),
         "table": {"columns": list(display.columns), "rows": display.values.tolist()}, "truncated": False},
        ensure_ascii=False, sort_keys=True)
    seed(client, narrate_system(cfg), [{"role": "user", "content": message}], [], None, fixture)
    return narrate(question, spec, display, client, cfg, catalog)


def test_narrate_passes(cfg, catalog, tmp_path):
    text, tripped, offending = _narrate(cfg, catalog, tmp_path, table("T2"), "narrate_pass")
    assert text == response("narrate_pass")["content"][0]["text"]
    assert (tripped, offending) == (False, [])


def test_narrate_trips_to_template(cfg, catalog, tmp_path):
    display = table("T2")
    text, tripped, offending = _narrate(cfg, catalog, tmp_path, display, "narrate_trip")
    assert (tripped, offending) == (True, ["51%"])
    assert text == template_answer(S02, display)


def _state_spec():
    return QuerySpec(intent="answer", metrics=["arrears_30p_bal"], group_by=["state"],
                     time={"grain": "month", "start": "2024-01", "end": "2024-06", "shape": "series"})


def test_template_formats():
    spec = _state_spec()
    head = "Result computed from the data (narration withheld because it cited a number not in the table):"
    assert template_answer(spec, table("T1")) == "\n".join([
        head,
        "- NSW / 2024-06: arrears_30p_bal 1.23%",
        "- QLD / 2024-06: arrears_30p_bal 0.98%",
        "- VIC / 2024-06: arrears_30p_bal 1.05%",
    ])
    twelve = pd.DataFrame([[s, f"2024-0{m}", f"{m}.0{i}%"] for i, s in enumerate(["NSW", "QLD"]) for m in range(1, 7)],
                          columns=["state", "period_label", "arrears_30p_bal"])
    out = template_answer(spec, twelve).split("\n")
    assert len(out) == 12
    assert out[1] == "- NSW / 2024-01: arrears_30p_bal 1.00%"
    assert out[10] == "- QLD / 2024-04: arrears_30p_bal 4.01%"
    assert out[11] == "- … and 2 more rows."
    s02 = template_answer(S02, table("T2")).split("\n")
    assert s02[1] == "- HARB / 2026-09: balance_total A$412.3m; loan_count 12,345"
    empty = table("T1").iloc[0:0]
    assert template_answer(spec, empty) == head + "\nNo loans match the filters and dates in the query."


def test_truncation_flag(cfg, catalog, tmp_path):
    spec = _state_spec()
    display = pd.DataFrame([["NSW", f"2024-{i:02d}", "1.00%"] for i in range(60)],
                           columns=["state", "period_label", "arrears_30p_bal"])
    question = "What were 30+ arrears by state?"
    sent = {"question": question, "spec": spec.model_dump(mode="json"),
            "table": {"columns": list(display.columns), "rows": display.head(50).values.tolist()}, "truncated": True}
    assert cfg.llm.narration_max_rows == 50
    text, tripped, _ = _narrate(cfg, catalog, tmp_path, display, "narrate_truncated", spec, question,
                                json.dumps(sent, ensure_ascii=False, sort_keys=True))
    assert not tripped and text == "The first rows show arrears by state."
    assert len(sent["table"]["rows"]) == 50
