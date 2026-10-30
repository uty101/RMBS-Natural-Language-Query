"""Eval outputs: summary with Wilson intervals, trap failures and the detail file
(kickoff 6.11; instruction 05 D.2). Steps 5.3, 5.6.

Every file is UTF-8 with LF line endings. The CSVs write floats as `%.10f`, a null as an
empty cell, and quote a cell only when it holds a comma, quote or line break. The detail
file holds 1 JSON object per (system, item) with sorted keys.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from rmbsq.eval.score import wilson
from rmbsq.semantic.format import format_table

RESULT_COLUMNS = ["system", "item_id", "category", "intent", "correct", "n_values_checked", "max_abs_err",
                  "latency_s", "input_tokens", "output_tokens", "guard_tripped", "error"]
SUMMARY_COLUMNS = ["system", "category", "n", "k", "accuracy", "wilson_lo", "wilson_hi"]
TRAP_COLUMNS = ["system", "item_id", "trap", "expected", "got"]
SYSTEMS = ["system", "baseline"]
DETAIL_ROWS = 20  # instruction 05 D.2: at most 20 result rows per detail line


def _cell(v) -> str:
    if v is None or v is pd.NA or (isinstance(v, (float, np.floating)) and math.isnan(v)):
        return ""
    if isinstance(v, (bool, np.bool_)):
        return str(bool(v))
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return "%.10f" % v
    return str(v)


def write_table(df: pd.DataFrame, path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(df.columns)
        for row in df.itertuples(index=False):
            w.writerow([_cell(v) for v in row])


def summarise(scored: pd.DataFrame, cfg) -> pd.DataFrame:
    """D.2: system x (each category, in item order, then total)."""
    categories = list(dict.fromkeys(scored["category"]))
    rows = []
    for system in SYSTEMS:
        mine = scored[scored["system"] == system]
        for category in [*categories, "total"]:
            part = mine if category == "total" else mine[mine["category"] == category]
            n, k = len(part), int(part["correct"].sum())
            lo, hi = wilson(k, n, cfg.eval.wilson_z)
            rows.append([system, category, n, k, k / n, lo, hi])
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def first_value(df: pd.DataFrame | None, metric: str, catalog) -> str | None:
    """The first value of `metric` as `format_table` shows it; None when there is no value."""
    if df is None or metric not in df.columns or df.empty:
        return None
    try:
        return str(format_table(df[[metric]].head(1), catalog)[metric].iloc[0])
    except (TypeError, ValueError):
        return str(df[metric].iloc[0])


def build_trap_failures(scored: pd.DataFrame, items, catalog) -> pd.DataFrame:
    """Step 5.6: 1 row per wrong trap answer."""
    by_id = {i.id: i for i in items}
    rows = []
    for _, r in scored.iterrows():
        item = by_id[r["item_id"]]
        if item.trap is None or r["correct"]:
            continue
        metric = item.gold_spec.metrics[0]
        got = first_value(r["result"], metric, catalog)
        if got is None:
            got = r["error"] or r["intent"]
        rows.append([r["system"], item.id, item.trap, first_value(r["gold"], metric, catalog), got])
    return pd.DataFrame(rows, columns=TRAP_COLUMNS)


def _display_rows(df: pd.DataFrame | None, catalog) -> tuple[list[str], list[list[str]]]:
    if df is None:
        return [], []
    head = df.head(DETAIL_ROWS)
    try:
        shown = format_table(head, catalog)
    except (TypeError, ValueError):
        # a baseline result whose metric column is not numeric: every cell as str
        shown = head.astype(str)
    return [str(c) for c in shown.columns], [[str(v) for v in row] for row in shown.itertuples(index=False)]


def detail_lines(scored: pd.DataFrame, items, catalog) -> list[str]:
    by_id = {i.id: i for i in items}
    lines = []
    for _, r in scored.iterrows():
        columns, rows = _display_rows(r["result"], catalog)
        obj = {"system": r["system"], "item_id": r["item_id"], "question": by_id[r["item_id"]].question,
               "intent": r["intent"], "columns": columns, "rows": rows, "correct": bool(r["correct"]),
               "error": r["error"]}
        if r["system"] == "system":
            obj.update(spec=r["spec"], sql_duckdb=r["sql"], text=r["text"], offending=list(r["offending"]))
        else:
            obj["sql"] = r["sql"]
        lines.append(json.dumps(obj, sort_keys=True, ensure_ascii=False))
    return lines


def write_outputs(scored: pd.DataFrame, items, catalog, cfg, out_dir: Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_table(scored[RESULT_COLUMNS], out_dir / "eval_results.csv")
    write_table(summarise(scored, cfg), out_dir / "eval_summary.csv")
    write_table(build_trap_failures(scored, items, catalog), out_dir / "trap_failures.csv")
    text = "".join(line + "\n" for line in detail_lines(scored, items, catalog))
    (out_dir / "eval_detail.jsonl").write_bytes(text.encode("utf-8"))
