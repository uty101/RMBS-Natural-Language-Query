"""Step 5.7: the tiled database on the small profile with copies = 3 (instruction 05 E, F 5.7)."""

import json
from pathlib import Path

import duckdb
import pytest

from rmbsq.db import connect_readonly
from rmbsq.eval.benchmark import ONCE, TILED, build_tiled_db, tiled_spec
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.compiler import compile, execute
from rmbsq.semantic.spec import QuerySpec

COPIES = 3
TOL = 1e-9  # instruction 05 F 5.7
GOLD = {g["id"]: g for g in json.loads(
    (Path(__file__).parent / "fixtures" / "compiler_gold.json").read_text(encoding="utf-8"))}
TOTALS = ["balance_total", "loan_count"]


@pytest.fixture(scope="module")
def tiled_db(small_db, tmp_path_factory):
    db = tmp_path_factory.mktemp("tiled") / "rmbs_x3.duckdb"
    build_tiled_db(small_db, db, COPIES)
    return db


def counts(db) -> dict[str, int]:
    con = connect_readonly(db)
    try:
        return {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                for t in [*TILED, *ONCE, "agg_deal_month"]}
    finally:
        con.close()


def run(spec, db, route):
    con = connect_readonly(db)
    try:
        df = execute(compile(spec, load_catalog(), route), con)
    finally:
        con.close()
    keys = [*spec.group_by, "period_label"]
    return df.sort_values(keys).reset_index(drop=True), keys


def test_tiled_row_count(small_db, tiled_db):
    src, tiled = counts(small_db), counts(tiled_db)
    print(src, tiled)
    for t in [*TILED, "agg_deal_month"]:
        assert tiled[t] == COPIES * src[t], t
    for t in ONCE:
        assert tiled[t] == src[t], t
    con = connect_readonly(tiled_db)
    try:
        ids = con.execute("SELECT DISTINCT left(deal_id, 4) FROM fact_loan_month ORDER BY 1").fetchall()
        names = con.execute("SELECT deal_name FROM dim_deal WHERE deal_id = 'C02-' || "
                            "(SELECT min(deal_id) FROM dim_deal WHERE deal_id LIKE 'C00-%')[5:]").fetchall()
    finally:
        con.close()
    assert [r[0] for r in ids] == ["C00-", "C01-", "C02-"]
    assert len(names) == 1 and names[0][0].startswith("C02-")


@pytest.mark.parametrize("route", ["auto", "fact"])
@pytest.mark.parametrize("sid", ["S01", "S12"])
def test_tiled_specs_match_1x(small_db, tiled_db, sid, route):
    spec = QuerySpec.model_validate(GOLD[sid]["spec"])
    one, keys = run(spec, small_db, route)
    many, _ = run(spec, tiled_db, route)
    assert len(one) >= 1 and one[keys].equals(many[keys])
    for m in spec.metrics:
        assert (one[m] - many[m]).abs().max() <= TOL, m

    # balance_total and loan_count on the same group_by, filters and time are 3 x
    totals = spec.model_copy(update={"metrics": TOTALS})
    one, _ = run(totals, small_db, route)
    many, _ = run(totals, tiled_db, route)
    assert one[keys].equals(many[keys])
    for m in TOTALS:
        want = COPIES * one[m].astype(float)
        assert ((many[m].astype(float) - want).abs() <= TOL * want.abs()).all(), m


def test_tiled_spec_rewrites_deal_filters():
    spec = QuerySpec.model_validate({"intent": "answer", "metrics": ["cpr"],
                                     "filters": {"deal_name": ["HARB 2019-1"], "state": ["NSW"]}})
    assert tiled_spec(spec).filters == {"deal_name": ["C00-HARB 2019-1"], "state": ["NSW"]}
    assert spec.filters["deal_name"] == ["HARB 2019-1"]


def test_connect_readonly_threads(small_db):
    default = duckdb.connect(":memory:").execute("SELECT current_setting('threads')").fetchone()[0]
    for threads, want in [(1, 1), (0, default)]:
        con = connect_readonly(small_db, threads)
        try:
            assert con.execute("SELECT current_setting('threads')").fetchone()[0] == want
        finally:
            con.close()
    con = connect_readonly(small_db)
    try:
        assert con.execute("SELECT current_setting('threads')").fetchone()[0] == 1
    finally:
        con.close()
