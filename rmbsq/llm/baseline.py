"""Free text-to-SQL baseline (kickoff 6.10; instruction 04 G). Step 4.5.

The model writes 1 DuckDB query through the forced tool `submit_sql`. The query runs on
the locked read-only connection of `rmbsq.db`, and a `threading.Timer` interrupts it
after `baseline_timeout_s`. An empty SQL string is a decline.
"""

from __future__ import annotations

import threading

import duckdb
import pandas as pd

from rmbsq.llm.spec_agent import fill
from rmbsq.semantic.catalog import ROOT

PROMPT = ROOT / "prompts" / "baseline_system.md"
TOOL_NAME = "submit_sql"
TOOL = {"name": TOOL_NAME,
        "input_schema": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}}
TOOL_CHOICE = {"type": "tool", "name": TOOL_NAME}


class BaselineError(Exception):
    pass


def baseline_system(cfg) -> str:
    cal = cfg.calendar
    return fill(PROMPT.read_text(encoding="utf-8"),
                {"window_start": cal.window_start, "window_end": cal.window_end, "latest": cal.latest})


def baseline_message(question: str, output_columns: list[str]) -> str:
    return question + "\n\nOutput columns, in order: " + ", ".join(output_columns)


def baseline_sql(question: str, output_columns: list[str], client, cfg) -> str:
    response = client.call(baseline_system(cfg),
                           [{"role": "user", "content": baseline_message(question, output_columns)}],
                           [TOOL], TOOL_CHOICE)
    block = next((b for b in response.get("content", [])
                  if b.get("type") == "tool_use" and b.get("name") == TOOL_NAME), None)
    if block is None:
        return ""
    return block["input"].get("sql", "")


def run_baseline_sql(sql: str, con: duckdb.DuckDBPyConnection, cfg) -> pd.DataFrame | None:
    if sql == "":
        return None
    timer = threading.Timer(cfg.llm.baseline_timeout_s, con.interrupt)
    timer.start()
    try:
        return con.execute(sql).df()
    except duckdb.Error as err:
        raise BaselineError(str(err)) from err
    finally:
        timer.cancel()
