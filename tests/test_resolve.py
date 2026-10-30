"""Step 4.3: entity resolution (instruction 04 E). Scores are rapidfuzz's
token_set_ratio as measured on the small profile; the review records them."""

import pytest

from rmbsq.llm.resolve import deal_aliases, resolve_entities
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.spec import QuerySpec


@pytest.fixture(scope="module")
def catalog(small_db):
    return load_catalog(db=small_db)


@pytest.fixture(scope="module")
def aliases(catalog):
    return deal_aliases(catalog)


def resolve(filters: dict, catalog, aliases) -> QuerySpec:
    spec = QuerySpec(intent="answer", metrics=["loan_count"], filters=filters)
    return resolve_entities(spec, catalog, aliases)


def test_exact_case_insensitive(catalog, aliases):
    assert resolve({"state": ["nsw"]}, catalog, aliases).filters == {"state": ["NSW"]}
    assert resolve({"originator": ["harb"], "dpd_bucket": ["90+"]}, catalog, aliases).filters == {
        "originator": ["HARB"], "dpd_bucket": ["90+"]}


def test_aliases(catalog, aliases):
    assert {k: v for k, v in aliases.items() if v == "HARB 2019-1"} == {
        "Harbour 19-1": "HARB 2019-1", "HARB 19-1": "HARB 2019-1", "HARB19-1": "HARB 2019-1"}
    for alias in ("Harbour 19-1", "HARB 19-1", "HARB19-1", "harbour 19-1", "harb19-1"):
        assert resolve({"deal_name": [alias]}, catalog, aliases).filters == {"deal_name": ["HARB 2019-1"]}
    assert resolve({"deal_id": ["d001"]}, catalog, aliases).filters == {"deal_id": ["D001"]}


def test_deal_id_to_deal_name(catalog, aliases):
    assert resolve({"deal_id": ["HARB 2019-1"]}, catalog, aliases).filters == {"deal_name": ["HARB 2019-1"]}
    assert resolve({"deal_id": ["D004", "KOO19-1"]}, catalog, aliases).filters == {
        "deal_id": ["D004"], "deal_name": ["KOO 2019-1"]}


def test_fuzzy_accept(catalog, aliases):
    # score 93.33 against Blacktown North, next best 80.0 (Blacktown South)
    assert resolve({"suburb": ["Blacktwon North"]}, catalog, aliases).filters == {"suburb": ["Blacktown North"]}


def test_fuzzy_clarify(catalog, aliases):
    # score 88.89 against Joondalup, then 52.63 Boroondara, 40.0 Onkaparinga
    spec = resolve({"area": ["Joondalop"]}, catalog, aliases)
    assert spec.intent == "clarify"
    assert spec.clarify.question == "Which area did you mean by 'Joondalop'?"
    assert spec.clarify.options == ["Joondalup", "Boroondara", "Onkaparinga"]


def test_fuzzy_tie_clarifies(catalog, aliases):
    # "Blacktown" is a token subset of 3 suburbs, so all 3 score 100
    spec = resolve({"suburb": ["Blacktown"]}, catalog, aliases)
    assert spec.intent == "clarify"
    assert spec.clarify.options == ["Blacktown Central", "Blacktown North", "Blacktown South"]


def test_unknown_unsupported(catalog, aliases):
    spec = resolve({"suburb": ["Narnia"]}, catalog, aliases)
    assert spec.intent == "unsupported"
    assert spec.unsupported_reason == "unknown suburb value 'Narnia'"


def test_flags_and_years(catalog, aliases):
    assert resolve({"io_flag": ["Y"], "lmi_flag": ["false"]}, catalog, aliases).filters == {
        "io_flag": ["yes"], "lmi_flag": ["no"]}
    assert resolve({"vintage_year": ["2019"]}, catalog, aliases).filters == {"vintage_year": [2019]}
    spec = resolve({"vintage_year": [2031]}, catalog, aliases)
    assert spec.intent == "unsupported" and spec.unsupported_reason == "unknown vintage_year value '2031'"
    spec = resolve({"dpd_bucket": ["90 plus"]}, catalog, aliases)
    assert spec.intent == "unsupported" and spec.unsupported_reason == "unknown dpd_bucket value '90 plus'"


def test_first_failure_decides(catalog, aliases):
    assert resolve({"suburb": ["Narnia"], "area": ["Joondalop"]}, catalog, aliases).intent == "unsupported"
    assert resolve({"area": ["Joondalop"], "suburb": ["Narnia"]}, catalog, aliases).intent == "clarify"
    assert resolve({"area": ["Narnia", "Joondalop"]}, catalog, aliases).intent == "unsupported"
    assert resolve({"area": ["Joondalop", "Narnia"]}, catalog, aliases).intent == "clarify"


def test_non_answer_unchanged(catalog, aliases):
    spec = QuerySpec(intent="unsupported", unsupported_reason="No data.")
    assert resolve_entities(spec, catalog, aliases) == spec
