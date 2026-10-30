"""Step 3.5: Oracle rendering (instruction 03 D.3, E 3.5)."""

import json
import logging
from pathlib import Path

import pytest
import sqlglot

from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.compiler import compile
from rmbsq.semantic.spec import QuerySpec

GOLD = json.loads((Path(__file__).parent / "fixtures" / "compiler_gold.json").read_text(encoding="utf-8"))
# DuckDB constructs that sqlglot passes into Oracle output (instruction 03 D.3, E 3.5)
BANNED = ["FILTER(", "FILTER (", "YEAR(", "QUARTER(", "STRFTIME", "CLOB", "LIMIT ", "::"]


@pytest.mark.parametrize("item", GOLD, ids=lambda g: g["id"])
def test_specs_render_to_oracle(item, caplog):
    with caplog.at_level(logging.WARNING, logger="sqlglot"):
        text = compile(QuerySpec.model_validate(item["spec"]), load_catalog()).sql_oracle
    assert [r.getMessage() for r in caplog.records] == []
    assert [b for b in BANNED if b.lower() in text.lower()] == []
    sqlglot.parse_one(text, read="oracle")
