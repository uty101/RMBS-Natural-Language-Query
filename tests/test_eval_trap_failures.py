"""Step 5.6: 1 trap_failures.csv row per wrong trap answer (instruction 05 D.2, F 5.6)."""

import pandas as pd

from rmbsq.eval.report import TRAP_COLUMNS, write_outputs
from rmbsq.eval.score import score
from rmbsq.semantic.catalog import load_catalog
from tests.test_eval_run import ITEMS, read_csv


def frame(metric, value, label="2025-11"):
    return pd.DataFrame({"period_label": [label], metric: [value]})


def trap_row(system, item, intent, value=None, error="", sql="SELECT 1"):
    """A run row for a trap item: gold is a 1-row frame; value None means no result."""
    metric = item.gold_spec.metrics[0]
    gold_value = 1000 if metric == "loan_count" else 0.2
    return {"system": system, "item_id": item.id, "intent": intent, "sql": sql,
            "spec_valid": True if system == "system" else None, "ran": value is not None,
            "result": None if value is None else frame(metric, value), "gold": frame(metric, gold_value),
            "error": error, "spec": None, "text": "", "offending": [], "guard_tripped": None,
            "latency_s": 0.0, "input_tokens": 0, "output_tokens": 0}


def test_trap_failures_row_count(cfg, tmp_path):
    traps = [ITEMS[f"Q{n}"] for n in range(27, 35)]
    rows = []
    for item in traps:
        rows.append(trap_row("system", item, "answer", 1000 if item.trap == "exit_rows" else 0.2))
        rows.append(trap_row("baseline", item, "sql", 1000 if item.trap == "exit_rows" else 0.2))
    # 4 wrong: a clarify, a wrong value, an error and a wrong count
    rows[2] = trap_row("system", ITEMS["Q28"], "clarify")
    rows[5] = trap_row("baseline", ITEMS["Q29"], "sql", 1.0)
    rows[7] = trap_row("baseline", ITEMS["Q30"], "error", error="Binder Error: no column x", sql="SELECT x")
    rows[9] = trap_row("baseline", ITEMS["Q31"], "sql", 1036)
    scored = score(pd.DataFrame(rows), traps)
    write_outputs(scored, traps, load_catalog(), cfg, tmp_path)

    results = read_csv(tmp_path / "eval_results.csv")
    wrong = [(r["system"], r["item_id"]) for r in results if r["category"] == "trap" and r["correct"] == "False"]
    failures = read_csv(tmp_path / "trap_failures.csv")
    assert len(failures) == len(wrong) == 4
    assert [(r["system"], r["item_id"]) for r in failures] == wrong
    assert [[r[c] for c in TRAP_COLUMNS] for r in failures] == [
        ["system", "Q28", "arrears_units", "20.00%", "clarify"],
        ["baseline", "Q29", "call_as_prepay", "20.00%", "100.00%"],
        ["baseline", "Q30", "call_as_prepay", "20.00%", "Binder Error: no column x"],
        ["baseline", "Q31", "exit_rows", "1,000", "1,036"]]
