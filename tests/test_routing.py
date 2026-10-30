"""Step 3.4: routing (instruction 03 D.2, E 3.4)."""

import json
from pathlib import Path

import pytest

from rmbsq.db import connect_readonly
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.compiler import compile, execute
from rmbsq.semantic.spec import QuerySpec
from tests.test_compiler import TOL, max_scaled_diff

GOLD = json.loads((Path(__file__).parent / "fixtures" / "compiler_gold.json").read_text(encoding="utf-8"))
AGG_SPECS = ["S01", "S02", "S05", "S10", "S11", "S12"]  # instruction 03 E 3.4


@pytest.mark.parametrize("item", GOLD, ids=lambda g: g["id"])
def test_route_auto_choice(item):
    assert compile(QuerySpec.model_validate(item["spec"]), load_catalog()).route == item["route_auto"]


@pytest.mark.parametrize("item", [g for g in GOLD if g["id"] in AGG_SPECS], ids=lambda g: g["id"])
def test_fact_and_agg_routes_equal(small_db, item):
    spec, cat = QuerySpec.model_validate(item["spec"]), load_catalog()
    con = connect_readonly(small_db)
    try:
        fact = execute(compile(spec, cat, route="fact"), con)
        agg = execute(compile(spec, cat, route="agg"), con)
    finally:
        con.close()
    assert max_scaled_diff(agg, fact, spec.metrics) <= TOL
