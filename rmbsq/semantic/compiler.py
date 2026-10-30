"""QuerySpec to sqlglot tree, DuckDB and Oracle SQL (kickoff 6.7; instruction 03 B, D).
Steps 3.3 to 3.5.

The statement is 1 sqlglot tree with the CTEs of D.1: `parts` (B.2), `b` (B.3), `keys`,
`stock` (B.5), `flow` (B.6) and a final select (B.7). Every value from the spec is a
literal node. Only the Oracle-safe constructs of D.3 are used: conditional aggregates as
SUM(CASE ...), period labels from a join to `dim_period`, labels as CASE expressions, and
EXP, LN, POWER and ROW_NUMBER for the math. The fixed SQL fragments below hold no spec
values; they are the B.2 part definitions and are parsed once.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import duckdb
import pandas as pd
import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel

from rmbsq.semantic.catalog import load_catalog
from rmbsq.semantic.timeagg import FLOW, flow_cte, flow_value, stock_cte

# instruction 03 B.2, the 13 monthly parts over fact_loan_month f joined to dim_loan l
_S = "f.closing_balance > 0"
_F = "f.opening_balance > 0"
_ARREARS = "NOT f.hardship_flag"
FACT_PARTS = {
    "loan_count": f"SUM(CASE WHEN {_S} THEN 1 ELSE 0 END)",
    "bal": f"SUM(CASE WHEN {_S} THEN f.closing_balance ELSE 0 END)",
    "a30_bal": f"SUM(CASE WHEN {_S} AND f.dpd_bucket >= 2 AND {_ARREARS} THEN f.closing_balance ELSE 0 END)",
    "a90_bal": f"SUM(CASE WHEN {_S} AND f.dpd_bucket = 4 AND {_ARREARS} THEN f.closing_balance ELSE 0 END)",
    "a90_cnt": f"SUM(CASE WHEN {_S} AND f.dpd_bucket = 4 AND {_ARREARS} THEN 1 ELSE 0 END)",
    "hard_bal": f"SUM(CASE WHEN {_S} AND f.hardship_flag THEN f.closing_balance ELSE 0 END)",
    "orig_ltv_x_bal": f"SUM(CASE WHEN {_S} THEN CAST(f.closing_balance AS DOUBLE) * l.orig_ltv ELSE 0 END)",
    "idx_ltv_x_bal": f"SUM(CASE WHEN {_S} THEN CAST(f.closing_balance AS DOUBLE) * f.indexed_ltv ELSE 0 END)",
    "rate_x_bal": f"SUM(CASE WHEN {_S} THEN CAST(f.closing_balance AS DOUBLE) * f.interest_rate ELSE 0 END)",
    "smm_num": f"SUM(CASE WHEN {_F} THEN f.curtailment ELSE 0 END)"
               f" + SUM(CASE WHEN {_F} AND f.exit_reason = 'prepaid' THEN f.exit_balance ELSE 0 END)",
    "smm_den": f"SUM(CASE WHEN {_F} AND (f.exit_reason IS NULL OR f.exit_reason = 'prepaid')"
               " THEN f.opening_balance - f.scheduled_principal ELSE 0 END)",
    "mdr_num": f"SUM(CASE WHEN {_F} AND f.exit_reason = 'defaulted' THEN f.exit_balance ELSE 0 END)",
    "mdr_den": f"SUM(CASE WHEN {_F} THEN f.opening_balance ELSE 0 END)",
}
PARTS = list(FACT_PARTS)

# instruction 03 B.7: output labels for the flag and dpd dimensions; years are integers
FLAGS = {"io_flag", "lmi_flag"}
YEARS = {"issue_year", "vintage_year"}
METRICS = set(load_catalog().metrics)

Route = Literal["auto", "fact", "agg"]


@dataclass(frozen=True)
class CompiledQuery:
    sql_duckdb: str
    sql_oracle: str
    route: str


def _col(name: str, table: str | None = None) -> exp.Column:
    return exp.column(name, table=table)


def _literal(value) -> exp.Literal:
    return exp.Literal.number(value) if isinstance(value, int) else exp.Literal.string(str(value))


def _month_start(month: str) -> exp.Expression:
    """'YYYY-MM' as the first-of-month DATE; Oracle renders it as TO_DATE."""
    return exp.DateStrToDate(this=exp.Literal.string(f"{month}-01"))


def _dim_expr(dim, fact_alias: str) -> exp.Expression:
    """A dimension's output value (B.7) over the parts CTE's sources."""
    alias = {"fact_loan_month": fact_alias, "dim_loan": "l", "dim_deal": "d"}[dim.table]
    col = _col(dim.column, alias)
    if dim.name in FLAGS:
        return exp.Case().when(col, exp.Literal.string("yes")).else_(exp.Literal.string("no"))
    if dim.name == "dpd_bucket":
        case = exp.Case(this=col)
        for i, label in enumerate(dim.labels[:-1]):
            case = case.when(exp.Literal.number(i), exp.Literal.string(label))
        return case.else_(exp.Literal.string(dim.labels[-1]))
    return col


def _filter_value(name: str, value) -> exp.Literal:
    return exp.Literal.number(int(value)) if name in YEARS else exp.Literal.string(str(value))


def choose_route(spec, catalog) -> str:
    """D.2: agg when every group_by and filter dimension is deal level, including none."""
    deal = set(catalog.deal_level)
    return "agg" if set(spec.group_by) <= deal and set(spec.filters) <= deal else "fact"


def _parts_cte(spec, catalog, route: str) -> exp.Select:
    """B.1 and B.2: the monthly parts per group and period, from fact_loan_month (route
    fact) or agg_deal_month (route agg)."""
    a = "a" if route == "agg" else "f"
    dims = [_dim_expr(catalog.dimensions[g], a) for g in spec.group_by]
    if route == "agg":
        parts = [exp.alias_(exp.Sum(this=_col(p, "a")), p) for p in PARTS]
        q = exp.select(*[exp.alias_(d, g) for d, g in zip(dims, spec.group_by)], _col("period", a), *parts).from_(
            "agg_deal_month AS a").join("dim_deal AS d", on="d.deal_id = a.deal_id")
    else:
        parts = [exp.alias_(sqlglot.parse_one(sql, read="duckdb"), p) for p, sql in FACT_PARTS.items()]
        q = (exp.select(*[exp.alias_(d, g) for d, g in zip(dims, spec.group_by)], _col("period", a), *parts)
             .from_("fact_loan_month AS f")
             .join("dim_loan AS l", on="l.loan_id = f.loan_id")
             .join("dim_deal AS d", on="d.deal_id = f.deal_id"))
    where = exp.Between(this=_col("period", a), low=_month_start(spec.time.start), high=_month_start(spec.time.end))
    for name, values in spec.filters.items():
        expr = _dim_expr(catalog.dimensions[name], a)
        where = exp.and_(where, exp.In(this=expr, expressions=[_filter_value(name, v) for v in values]))
    return q.where(where).group_by(*[d.copy() for d in dims], _col("period", a))


def _b_cte(spec) -> exp.Select:
    """B.3: period_label from dim_period for a series, a literal for a point."""
    t = spec.time
    star = exp.column(exp.Star(), table="parts")
    if t.shape == "series":
        return (exp.select(star, exp.alias_(_col(f"{t.grain}_label", "p"), "period_label"))
                .from_("parts").join("dim_period AS p", on="p.period = parts.period"))
    label = t.start if t.start == t.end else "range"
    return exp.select(star, exp.alias_(exp.Literal.string(label), "period_label")).from_("parts")


def _on(keys: list[str], left: str, right: str) -> exp.Expression:
    return exp.and_(*[exp.EQ(this=_col(k, right), expression=_col(k, left)) for k in keys])


def build_tree(spec, catalog, route: str) -> exp.Select:
    keys = [*spec.group_by, "period_label"]
    metrics = [catalog.metrics[m] for m in spec.metrics]
    stock = [m for m in metrics if m.kind == "stock"]
    flows = [m for m in metrics if m.kind == "flow"]
    prefixes = list(dict.fromkeys(FLOW[m.name][0] for m in flows))

    # O-37: stock metrics in spec order, then flow metrics in spec order, as the gold hand
    # SQL orders them (S11); B.7's text says spec order, which differs only when a flow
    # metric comes before a stock metric
    outputs = [_col(m.name, "s") for m in stock] + [exp.alias_(flow_value(m.name, "w"), m.name) for m in flows]
    q = exp.select(*[_col(k, "k") for k in keys], *outputs).from_("keys AS k")
    if stock:
        q = q.join("stock AS s", on=_on(keys, "k", "s"), join_type="left")
    if flows:
        q = q.join("flow AS w", on=_on(keys, "k", "w"), join_type="left")

    order = [exp.Ordered(this=_col(k, "k")) for k in keys]
    if spec.order is not None:
        by = exp.Ordered(this=_col(spec.order.metric), desc=spec.order.direction == "desc", nulls_first=False)
        q = q.order_by(by, *order).limit(exp.Literal.number(spec.order.limit))
    else:
        q = q.order_by(*order)

    q = q.with_("parts", as_=_parts_cte(spec, catalog, route)).with_("b", as_=_b_cte(spec))
    q = q.with_("keys", as_=exp.select(*[_col(k) for k in keys]).distinct().from_("b"))
    if stock:
        q = q.with_("stock", as_=stock_cte(keys, stock))
    if flows:
        q = q.with_("flow", as_=flow_cte(keys, prefixes))
    return q


def compile(spec, catalog, route: Route = "auto") -> CompiledQuery:  # noqa: A001 (kickoff 7 name)
    """Kickoff 6.7: the spec's statement as DuckDB and Oracle SQL from 1 sqlglot tree."""
    if spec.intent != "answer":
        raise ValueError(f"only answer specs compile, got intent {spec.intent}")
    if route == "auto":
        route = choose_route(spec, catalog)
    elif route == "agg" and choose_route(spec, catalog) != "agg":
        raise ValueError("route agg needs every group_by and filter dimension to be deal level")
    tree = build_tree(spec, catalog, route)
    return CompiledQuery(
        sql_duckdb=tree.sql(dialect="duckdb", pretty=True, unsupported_level=ErrorLevel.RAISE),
        # step 3.5: the same tree for Oracle; anything sqlglot can't render raises
        sql_oracle=tree.sql(dialect="oracle", pretty=True, unsupported_level=ErrorLevel.RAISE),
        route=route,
    )


def execute(compiled: CompiledQuery, con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Runs the DuckDB SQL. Decimals become float only here (kickoff 6.7): metric columns
    are float64 and loan_count is Int64 (B.7); year dimensions are int64."""
    cur = con.execute(compiled.sql_duckdb)
    names = [d[0] for d in cur.description]
    df = pd.DataFrame(cur.fetchall(), columns=names)
    for c in names:
        if c == "loan_count":
            df[c] = pd.array([None if v is None else int(v) for v in df[c]], dtype="Int64")
        elif c in METRICS:
            df[c] = pd.to_numeric(df[c].map(lambda v: None if v is None else float(v)), errors="raise").astype("float64")
        elif c in YEARS:
            df[c] = df[c].astype("int64")
    return df
