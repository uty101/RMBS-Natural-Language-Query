"""Step 5.2: scoring on constructed frames (instruction 05 C, F 5.2)."""

import pandas as pd
import pytest

from rmbsq.eval.run import EvalItem
from rmbsq.eval.score import compare_result, norm_key, score, wilson
from rmbsq.semantic.spec import QuerySpec

TIME = {"grain": "month", "start": "2026-09", "end": "2026-09", "shape": "point"}


def spec(metrics, group_by=(), order=None):
    return QuerySpec(intent="answer", metrics=list(metrics), group_by=list(group_by), time=TIME, order=order)


def by_state(values, states=("NSW", "QLD", "VIC")):
    return pd.DataFrame({"state": list(states), "period_label": "2026-09", "arrears_90p_bal": values})


GOLD = by_state([0.01, 0.02, 0.03])
STATE_SPEC = spec(["arrears_90p_bal"], ["state"])
ORDERED_SPEC = spec(["arrears_90p_bal"], ["state"], {"metric": "arrears_90p_bal", "direction": "asc", "limit": 3})
COLS = ("state", "period_label", "arrears_90p_bal")


def check(result, gold=GOLD, s=STATE_SPEC, cols=COLS):
    return compare_result(result, gold, s, cols)


def test_key_order_without_order_is_a_multiset():
    shuffled = GOLD.iloc[[2, 0, 1]].reset_index(drop=True)
    c = check(shuffled)
    assert c.correct and c.n_values_checked == 3 and c.max_abs_err == 0.0
    assert not check(GOLD.iloc[[0, 1]]).correct                                  # a key row missing
    assert not check(pd.concat([GOLD, GOLD.iloc[[0]]], ignore_index=True)).correct  # a key row repeated


def test_key_order_with_order_must_match():
    assert check(GOLD, s=ORDERED_SPEC).correct
    c = check(GOLD.iloc[[2, 0, 1]].reset_index(drop=True), s=ORDERED_SPEC)
    assert not c.correct and c.n_values_checked == 0 and c.max_abs_err is None


@pytest.mark.parametrize("delta, ok", [(0.9e-6, True), (-0.9e-6, True), (1.1e-6, False), (-1.1e-6, False)])
def test_pct_absolute_tolerance(delta, ok):
    c = check(by_state([0.01, 0.02 + delta, 0.03]))
    assert c.correct is ok
    assert c.max_abs_err == pytest.approx(abs(delta), rel=1e-6)


@pytest.mark.parametrize("delta, ok", [(900.0, True), (-900.0, True), (1100.0, False), (-1100.0, False)])
def test_aud_m_relative_tolerance(delta, ok):
    s = spec(["balance_total"])
    gold = pd.DataFrame({"period_label": ["2026-09"], "balance_total": [1e9]})
    got = pd.DataFrame({"period_label": ["2026-09"], "balance_total": [1e9 + delta]})
    c = compare_result(got, gold, s, ("period_label", "balance_total"))
    assert c.correct is ok and c.max_abs_err == pytest.approx(abs(delta))


@pytest.mark.parametrize("value, ok", [(1234, True), (1234.0, True), (1234 + 5e-10, True), (1234 - 5e-10, True),
                                       (1234 + 2e-9, False), (1234.4, False), (1235, False)])
def test_count_exact(value, ok):
    s = spec(["loan_count"])
    gold = pd.DataFrame({"period_label": ["2026-09"], "loan_count": [1234]})
    got = pd.DataFrame({"period_label": ["2026-09"], "loan_count": [value]})
    assert compare_result(got, gold, s, ("period_label", "loan_count")).correct is ok


def test_extra_columns_ignored():
    assert check(GOLD.assign(note="x", loan_count=7)).correct


def test_missing_column_is_wrong():
    c = check(GOLD.drop(columns="arrears_90p_bal"))
    assert not c.correct and c.n_values_checked == 0 and c.max_abs_err is None
    assert not check(GOLD.drop(columns="period_label")).correct


@pytest.mark.parametrize("null", [None, float("nan"), pd.NA])
def test_null_is_wrong(null):
    got = GOLD.astype({"arrears_90p_bal": object})
    got.loc[1, "arrears_90p_bal"] = null
    c = check(got)
    assert not c.correct and c.n_values_checked == 3


def test_non_numeric_value_is_wrong():
    got = GOLD.astype({"arrears_90p_bal": object})
    got.loc[0, "arrears_90p_bal"] = "1.00%"
    assert not check(got).correct


def test_bool_and_float_keys_normalise():
    assert [norm_key(v) for v in (True, False, 2021, 2021.0, " NSW ", 2021.5, "2021")] == \
        ["yes", "no", "2021", "2021", "NSW", "2021.5", "2021"]
    s = spec(["arrears_90p_bal"], ["io_flag", "vintage_year"])
    gold = pd.DataFrame({"io_flag": ["yes", "no"], "vintage_year": [2021, 2021], "period_label": "2026-09",
                         "arrears_90p_bal": [0.01, 0.02]})
    got = pd.DataFrame({"io_flag": [False, True], "vintage_year": [2021.0, 2021.0], "period_label": "2026-09",
                        "arrears_90p_bal": [0.02, 0.01]})
    assert compare_result(got, gold, s, ("io_flag", "vintage_year", "period_label", "arrears_90p_bal")).correct
    got["vintage_year"] = [2021.5, 2021.5]
    assert not compare_result(got, gold, s, ("io_flag", "vintage_year", "period_label", "arrears_90p_bal")).correct


ANSWER = EvalItem(id="A1", category="grouped", question="q", expected_intent="answer", gold_spec=STATE_SPEC,
                  output_columns=COLS, gold_sql="SELECT 1")
CLARIFY = EvalItem(id="C1", category="ambiguous", question="q", expected_intent="clarify")
UNSUPPORTED = EvalItem(id="U1", category="unsupported", question="q", expected_intent="unsupported")


def row(system, item, intent, sql="", spec_valid=True, ran=False, result=None, gold=None):
    return {"system": system, "item_id": item.id, "intent": intent, "sql": sql,
            "spec_valid": spec_valid if system == "system" else None, "ran": ran, "result": result, "gold": gold}


def scored(rows):
    return score(pd.DataFrame(rows), [ANSWER, CLARIFY, UNSUPPORTED])


def test_answer_rules_both_systems():
    good = dict(ran=True, result=GOLD, gold=GOLD)
    out = scored([
        row("system", ANSWER, "answer", **good),
        row("system", ANSWER, "answer", spec_valid=False, **good),
        row("system", ANSWER, "clarify", **good),
        row("system", ANSWER, "answer", ran=False, gold=GOLD),
        row("baseline", ANSWER, "sql", "SELECT 1", **good),
        row("baseline", ANSWER, "error", "SELECT nope", gold=GOLD),
        row("baseline", ANSWER, "decline", "", gold=GOLD),
        row("baseline", ANSWER, "sql", "SELECT 1", ran=True, result=by_state([0.01, 0.02, 0.04]), gold=GOLD),
    ])
    assert out["correct"].tolist() == [True, False, False, False, True, False, False, False]
    assert out["n_values_checked"].tolist() == [3, 0, 0, 0, 3, 0, 0, 3]
    assert out["max_abs_err"].iloc[7] == pytest.approx(0.01)
    assert (out["category"] == "grouped").all()


def test_clarify_and_unsupported_rules_both_systems():
    out = scored([
        row("system", CLARIFY, "clarify"),
        row("system", CLARIFY, "answer"),
        row("system", CLARIFY, "unsupported"),
        row("baseline", CLARIFY, "decline", ""),
        row("baseline", CLARIFY, "sql", "SELECT 1", ran=True),
        row("system", UNSUPPORTED, "unsupported"),
        row("system", UNSUPPORTED, "clarify"),
        row("baseline", UNSUPPORTED, "decline", ""),
        row("baseline", UNSUPPORTED, "sql", "SELECT 1", ran=True),
        row("baseline", UNSUPPORTED, "error", "SELECT nope"),
    ])
    assert out["correct"].tolist() == [True, False, False, False, False, True, False, True, False, False]
    assert out["category"].tolist() == ["ambiguous"] * 5 + ["unsupported"] * 5


def test_wilson_hand_values():
    # hand values, z = 1.96, z^2 = 3.8416 (working in review/section_5.md):
    # (7, 10): centre 8.9208 / 13.8416, half 1.96 * sqrt(3.0604) / 13.8416
    lo, hi = wilson(7, 10, 1.96)
    assert round(lo, 6) == 0.396773 and round(hi, 6) == 0.892211
    # (40, 40): centre 41.9208 / 43.8416, half 1.96 * 0.98 / 43.8416
    lo, hi = wilson(40, 40, 1.96)
    assert round(lo, 6) == 0.912375 and round(hi, 6) == 1.000000
