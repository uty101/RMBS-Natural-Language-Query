"""Step 5.0: the 40 eval items (instruction 05 B, F 5.0)."""

from collections import Counter
from pathlib import Path

import yaml

from rmbsq.eval.run import load_items
from rmbsq.semantic.spec import QuerySpec

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "eval" / "questions.yaml"
CATEGORIES = {"simple": 10, "grouped": 10, "time": 6, "trap": 8, "ambiguous": 4, "unsupported": 2}
TRAPS = {"arrears_units", "call_as_prepay", "exit_rows", "weighting"}  # instruction 05 B.1


def test_questions_file():
    raw = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))["items"]
    assert len(raw) == 40
    assert len({r["id"] for r in raw}) == 40
    assert Counter(r["category"] for r in raw) == CATEGORIES
    assert Counter(r["trap"] for r in raw if r["category"] == "trap") == {t: 2 for t in TRAPS}
    assert all("trap" not in r for r in raw if r["category"] != "trap")
    answers = [r for r in raw if r["expected_intent"] == "answer"]
    assert len(answers) == 34
    for r in answers:
        assert r["gold_spec"] and r["output_columns"] and r["gold_sql"], r["id"]
        assert QuerySpec.model_validate(r["gold_spec"]).intent == "answer", r["id"]
    assert all("gold_spec" not in r for r in raw if r["expected_intent"] != "answer")

    items = load_items(QUESTIONS)
    assert [i.id for i in items] == [r["id"] for r in raw]
    assert sum(i.gold_spec is not None for i in items) == 34
