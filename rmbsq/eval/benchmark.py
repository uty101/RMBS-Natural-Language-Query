"""Tiled database and scale benchmark (kickoff 6.12; instruction 05 E, O-23 (a)). Step 5.7.

`build_tiled_db` copies the canonical database `copies` times: copy c prefixes loan_id
and deal_id in `fact_loan_month` and `dim_loan`, and deal_id and deal_name in
`dim_deal`, with `C{c:02d}-`. `dim_period`, `hpi` and `cash_rate` are copied once, and
`agg_deal_month` is rebuilt from the tiled fact with the Section 2 statement. Like
`build_canonical`, it runs on 1 thread.

`run_benchmark` times `execute` on every answer item's compiled gold spec, on the 1x and
tiled databases, routes auto and fact, and each `thread_settings` value: `warmup`
untimed runs, then `repeats` runs timed with `time.perf_counter`. On the tiled database
deal_id and deal_name filter values are rewritten to copy `C00-`.
"""

from __future__ import annotations

import statistics
import time
from pathlib import Path

import duckdb
import pandas as pd

from rmbsq.canonical.build import AGG_SQL
from rmbsq.db import connect_readonly
from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.compiler import compile, execute

TILED = {"fact_loan_month": ["loan_id", "deal_id"], "dim_loan": ["loan_id", "deal_id"],
         "dim_deal": ["deal_id", "deal_name"]}
ONCE = ["dim_period", "hpi", "cash_rate"]
DEAL_FILTERS = ("deal_id", "deal_name")
ROUTES = ("auto", "fact")
COLUMNS = ["item_id", "db", "db_rows", "route", "threads", "median_s", "max_s"]


def prefix(c: int) -> str:
    return f"C{c:02d}-"


def _quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def build_tiled_db(src: Path, dst: Path, copies: int) -> None:
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    con = duckdb.connect(str(dst))
    try:
        con.execute("SET threads = 1")
        con.execute(f"ATTACH {_quote(src)} AS src (READ_ONLY)")
        for table, cols in TILED.items():
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM src.{table} LIMIT 0")
            for c in range(copies):
                swaps = ", ".join(f"'{prefix(c)}' || {col} AS {col}" for col in cols)
                con.execute(f"INSERT INTO {table} SELECT * REPLACE ({swaps}) FROM src.{table}")
        for table in ONCE:
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM src.{table}")
        con.execute("DETACH src")
        con.execute(AGG_SQL)
        con.execute("CHECKPOINT")
    finally:
        con.close()


def tiled_spec(spec):
    """O-23 (a): deal filters point at copy C00 on the tiled database."""
    filters = {k: [prefix(0) + str(v) for v in vals] if k in DEAL_FILTERS else vals
               for k, vals in spec.filters.items()}
    return spec.model_copy(update={"filters": filters})


def run_benchmark(items, src_db: Path, tiled_db: Path, cfg) -> pd.DataFrame:
    bench = cfg.benchmark
    catalog = load_catalog()
    answers = [i for i in items if i.gold_spec is not None]
    dbs = [("1x", Path(src_db)), (f"{bench.copies}x", Path(tiled_db))]
    rows = []
    for d, (label, path) in enumerate(dbs):
        for t, threads in enumerate(bench.thread_settings):
            con = connect_readonly(path, threads)
            try:
                db_rows = con.execute("SELECT count(*) FROM fact_loan_month").fetchone()[0]
                for r, route in enumerate(ROUTES):
                    for n, item in enumerate(answers):
                        spec = item.gold_spec if d == 0 else tiled_spec(item.gold_spec)
                        compiled = compile(spec, catalog, route)
                        for _ in range(bench.warmup):
                            execute(compiled, con)
                        times = []
                        for _ in range(bench.repeats):
                            t0 = time.perf_counter()
                            execute(compiled, con)
                            times.append(time.perf_counter() - t0)
                        rows.append(((n, d, r, t), [item.id, label, db_rows, route, threads,
                                                    statistics.median(times), max(times)]))
            finally:
                con.close()
    return pd.DataFrame([row for _, row in sorted(rows, key=lambda x: x[0])], columns=COLUMNS)
