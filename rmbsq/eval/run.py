"""Runs the governed system and the baseline over the eval items (kickoff 6.11; instruction
05 D). Step 5.0 (items), step 5.3 (runs).

`eval/questions.yaml` is copied byte for byte from instruction 05. Each item has `id`,
`category`, `question` and `expected_intent`, plus `trap` on trap items; the answer
items also carry `gold_spec`, `output_columns` and `gold_sql`.

`run_system` and `run_baseline` return 1 row per item holding the intent, the SQL, the
result frame, the gold frame and the usage summed from the cache; `score` then adds
correct, n_values_checked and max_abs_err. A system item whose compile or execute fails
records intent `error` and the error text. A cache miss in replay mode, a missing API key
and an API error all propagate: they stop the run rather than score as wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd
import yaml
from sqlglot.errors import SqlglotError

from rmbsq.db import connect_readonly
from rmbsq.eval.report import write_outputs
from rmbsq.eval.score import score
from rmbsq.llm.answer import answer
from rmbsq.llm.baseline import BaselineError, baseline_sql, run_baseline_sql
from rmbsq.llm.client import LLMClient
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.spec import QuerySpec


@dataclass(frozen=True)
class EvalItem:
    id: str
    category: str
    question: str
    expected_intent: str
    trap: str | None = None
    gold_spec: QuerySpec | None = None
    output_columns: tuple[str, ...] | None = None
    gold_sql: str | None = None


def load_items(path: Path) -> list[EvalItem]:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)["items"]
    items = []
    for r in raw:
        spec = r.get("gold_spec")
        cols = r.get("output_columns")
        items.append(EvalItem(id=r["id"], category=r["category"], question=r["question"],
                              expected_intent=r["expected_intent"], trap=r.get("trap"),
                              gold_spec=None if spec is None else QuerySpec.model_validate(spec),
                              output_columns=None if cols is None else tuple(cols), gold_sql=r.get("gold_sql")))
    return items


# instruction 05 D.1: the baseline gets no gold columns on non-answer items
NON_ANSWER_COLUMNS = ["period_label"]
# what a failed system item raises once its spec call is made: a compile or execute failure
ITEM_ERRORS = (duckdb.Error, ValueError, SqlglotError)


def _usage(calls: list[dict]) -> dict:
    """D.2: latency and tokens summed over the item's calls, as the cache holds them."""
    return {"latency_s": sum(c["latency_s"] for c in calls),
            "input_tokens": sum(c["input_tokens"] or 0 for c in calls),
            "output_tokens": sum(c["output_tokens"] or 0 for c in calls)}


def gold_result(item: EvalItem, con: duckdb.DuckDBPyConnection) -> pd.DataFrame | None:
    """C.3: `gold_sql` run on the same connection; None for a non-answer item."""
    return None if item.gold_sql is None else con.execute(item.gold_sql).df()


def run_system(items, client, con, catalog) -> pd.DataFrame:
    rows = []
    for item in items:
        first = len(client.calls)
        ans, error = None, ""
        try:
            ans = answer(item.question, client, con, catalog, client.cfg)
        except ITEM_ERRORS as err:
            error = f"{type(err).__name__}: {err}"
        rows.append({
            "system": "system", "item_id": item.id,
            "intent": "error" if ans is None else ans.spec.intent,
            "spec_valid": None if ans is None else ans.spec_valid,
            "spec": None if ans is None else ans.spec.model_dump(mode="json"),
            "sql": "" if ans is None or ans.sql_duckdb is None else ans.sql_duckdb,
            "ran": ans is not None and ans.table is not None,
            "result": None if ans is None else ans.table,
            "text": "" if ans is None else ans.text,
            "guard_tripped": None if ans is None else ans.guard_tripped,
            "offending": [] if ans is None else ans.offending,
            "error": error, "gold": gold_result(item, con), **_usage(client.calls[first:]),
        })
    return pd.DataFrame(rows)


def run_baseline(items, client, con) -> pd.DataFrame:
    rows = []
    for item in items:
        first = len(client.calls)
        cols = list(item.output_columns) if item.output_columns else NON_ANSWER_COLUMNS
        sql = baseline_sql(item.question, cols, client, client.cfg)
        result, error = None, ""
        if sql == "":
            intent = "decline"
        else:
            try:
                result, intent = run_baseline_sql(sql, con, client.cfg), "sql"
            except BaselineError as err:
                intent, error = "error", str(err)
        rows.append({
            "system": "baseline", "item_id": item.id, "intent": intent, "spec_valid": None, "spec": None,
            "sql": sql, "ran": result is not None, "result": result, "text": None, "guard_tripped": None,
            "offending": None, "error": error, "gold": gold_result(item, con), **_usage(client.calls[first:]),
        })
    return pd.DataFrame(rows)


def _run(items, client, db: Path, catalog) -> pd.DataFrame:
    con = connect_readonly(db)
    try:
        results = pd.concat([run_system(items, client, con, catalog), run_baseline(items, client, con)],
                            ignore_index=True)
    finally:
        con.close()
    return score(results, items)


def run_eval(items, db: Path, cache_dir: Path, out_dir: Path, cfg, mode: str = "replay") -> pd.DataFrame:
    """D.2: record mode fills the cache first; the outputs always come from the replay pass."""
    if mode not in ("replay", "record"):
        raise ValueError(f"mode must be replay or record, got {mode}")
    catalog = load_catalog(db=db)
    if mode == "record":
        _run(items, LLMClient(cfg, mode="record", cache_dir=cache_dir), db, catalog)
    scored = _run(items, LLMClient(cfg, mode="replay", cache_dir=cache_dir), db, catalog)
    write_outputs(scored, items, catalog, cfg, out_dir)
    return scored
