"""The question-to-answer pipeline (instruction 04 H). Step 4.6.

Spec call, then entity resolution for an answer spec, then compile, execute, format and
narrate if the spec is still an answer. A clarify spec answers with its question and
options; an unsupported spec with its reason.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import pandas as pd

from rmbsq.llm.narrate import narrate
from rmbsq.llm.resolve import deal_aliases, resolve_entities
from rmbsq.llm.spec_agent import question_to_spec
from rmbsq.semantic.compiler import compile, execute
from rmbsq.semantic.format import format_table
from rmbsq.semantic.spec import QuerySpec


@dataclass
class Answer:
    question: str
    spec_raw: QuerySpec
    spec_valid: bool
    spec: QuerySpec
    route: str | None
    sql_duckdb: str | None
    sql_oracle: str | None
    table: pd.DataFrame | None
    display: pd.DataFrame | None
    text: str
    guard_tripped: bool
    offending: list[str]
    calls: list[dict]


def answer(question: str, client, con: duckdb.DuckDBPyConnection, catalog, cfg) -> Answer:
    first_call = len(client.calls)
    spec_raw, spec_valid = question_to_spec(question, client, catalog)
    spec = spec_raw
    if spec.intent == "answer":
        spec = resolve_entities(spec_raw, catalog, deal_aliases(catalog))
    route = sql_duckdb = sql_oracle = table = display = None
    tripped, offending = False, []
    if spec.intent == "answer":
        compiled = compile(spec, catalog)
        route, sql_duckdb, sql_oracle = compiled.route, compiled.sql_duckdb, compiled.sql_oracle
        table = execute(compiled, con)
        display = format_table(table, catalog)
        text, tripped, offending = narrate(question, spec, display, client, cfg, catalog)
    elif spec.intent == "clarify":
        text = f"{spec.clarify.question}\nOptions: {'; '.join(spec.clarify.options)}"
    else:
        text = spec.unsupported_reason
    return Answer(question=question, spec_raw=spec_raw, spec_valid=spec_valid, spec=spec, route=route,
                  sql_duckdb=sql_duckdb, sql_oracle=sql_oracle, table=table, display=display, text=text,
                  guard_tripped=tripped, offending=offending, calls=client.calls[first_call:])
