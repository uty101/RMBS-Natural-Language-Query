"""Time aggregation of stock and flow metrics (kickoff 6.4; instruction 03 B.5, B.6). Step 3.3.

The monthly parts of instruction 03 B.2 become 1 value per output row:

- stock metrics take the parts at the latest period in the bucket with loan_count > 0 for
  that group (O-17);
- flow metrics compound the monthly rate m = num / den over the n months with den > 0:
  p = 1 if any m >= 1, else 1 - exp(sum ln(1 - m)); then smm_vol = 1 - (1 - p)^(1 / n),
  cpr and cdr = 1 - (1 - p)^(12 / n). n = 0 gives NULL.

`stock_cte` and `flow_cte` build those 2 steps as sqlglot trees over the CTE `b` (D.1),
using only the Oracle-safe constructs of D.3. `flow_value` is the final select's
expression for 1 flow metric. `aggregate` is the same arithmetic on a pandas frame of
monthly parts, so it runs without SQL (B.8).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sqlglot import exp

# flow metric -> (rate prefix, exponent numerator); the rate's parts are <prefix>_num and <prefix>_den
FLOW = {"smm_vol": ("smm", 1), "cpr": ("smm", 12), "cdr": ("mdr", 12)}


def _col(name: str, table: str | None = None) -> exp.Column:
    return exp.column(name, table=table)


def _num(value) -> exp.Literal:
    return exp.Literal.number(value)


def _double(e: exp.Expression) -> exp.Cast:
    return exp.cast(e, "DOUBLE")


def _ratio(num: str, den: str) -> exp.Expression:
    return exp.Div(this=_double(_col(num)), expression=_double(_col(den)))


def _case(cond: exp.Expression, then: exp.Expression, default: exp.Expression | None = None) -> exp.Case:
    case = exp.Case().when(cond, then)
    return case if default is None else case.else_(default)


def stock_value(metric) -> exp.Expression:
    """A stock metric from its parts (B.5): the numerator alone, or numerator / denominator."""
    if not metric.denominator:
        return _col(metric.numerator)
    return _ratio(metric.numerator, metric.denominator)


def stock_cte(keys: list[str], metrics: list) -> exp.Select:
    """B.5 over `b`: the row at the latest period with loan_count > 0 per key, by
    ROW_NUMBER() OVER (PARTITION BY keys ORDER BY period DESC)."""
    rn = exp.Window(
        this=exp.RowNumber(),
        partition_by=[_col(k) for k in keys],
        order=exp.Order(expressions=[exp.Ordered(this=_col("period"), desc=True)]),
    )
    ranked = (
        exp.select(exp.column(exp.Star(), table="b"), exp.alias_(rn, "rn"))
        .from_("b")
        .where(exp.GT(this=_col("loan_count"), expression=_num(0)))
    )
    return (
        exp.select(*[_col(k) for k in keys], *[exp.alias_(stock_value(m), m.name) for m in metrics])
        .from_(ranked.subquery("r"))
        .where(exp.EQ(this=_col("rn"), expression=_num(1)))
    )


def flow_cte(keys: list[str], prefixes: list[str]) -> exp.Select:
    """B.6 over `b`, per key and rate prefix (smm, mdr): <prefix>_p, the compounded rate
    over the months with den > 0, and <prefix>_n, the number of those months."""
    cols = []
    for p in prefixes:
        num, den = f"{p}_num", f"{p}_den"
        has = exp.GT(this=_col(den), expression=_num(0))
        n = exp.Sum(this=_case(has, _num(1), _num(0)))
        m = _ratio(num, den)
        top = exp.Max(this=_case(has, m.copy(), _num(0)))
        below = exp.and_(has.copy(), exp.LT(this=_col(num), expression=_col(den)))
        logs = exp.Sum(this=_case(below, exp.Ln(this=exp.Sub(this=_num(1), expression=m.copy())), _num(0)))
        p_value = (
            exp.Case()
            .when(exp.EQ(this=n.copy(), expression=_num(0)), exp.null())
            .when(exp.GTE(this=top, expression=_num(1)), _num("1.0"))
            .else_(exp.Sub(this=_num(1), expression=exp.Exp(this=logs)))
        )
        cols += [exp.alias_(p_value, f"{p}_p"), exp.alias_(n, f"{p}_n")]
    return exp.select(*[_col(k) for k in keys], *cols).from_("b").group_by(*[_col(k) for k in keys])


def flow_value(name: str, table: str) -> exp.Expression:
    """B.6: 1 - (1 - p)^(k / n) for n > 0, else NULL; k is 1 for smm_vol and 12 otherwise."""
    prefix, k = FLOW[name]
    n = _col(f"{prefix}_n", table)
    power = exp.Pow(
        this=exp.Sub(this=_num(1), expression=_col(f"{prefix}_p", table)),
        expression=exp.Div(this=_num(f"{k}.0"), expression=n.copy()),
    )
    return _case(exp.GT(this=n, expression=_num(0)), exp.Sub(this=_num(1), expression=power))


def aggregate(parts: pd.DataFrame, group_by: list[str], metrics: list) -> pd.DataFrame:
    """B.4 to B.6 on a frame of monthly parts, without SQL. `parts` has the group_by
    columns, `period`, `period_label` and the B.2 parts; `metrics` are catalogue Metric
    entries. Returns 1 row per (group values, period_label), sorted by them, with the
    group_by columns, period_label and 1 column per metric."""
    keys = [*group_by, "period_label"]
    out = parts[keys].drop_duplicates().sort_values(keys).reset_index(drop=True)
    stocked = parts[parts["loan_count"] > 0].sort_values("period").groupby(keys, sort=False).tail(1)
    out = out.merge(stocked.set_index(keys), left_on=keys, right_index=True, how="left")
    result = out[keys].copy()
    for m in metrics:
        if m.kind == "stock":
            value = out[m.numerator].astype(float)
            if m.denominator:
                value = value / out[m.denominator].astype(float)
            result[m.name] = value
            continue
        prefix, k = FLOW[m.name]
        den = parts[f"{prefix}_den"].astype(float)
        rates = parts.loc[den > 0, keys].assign(m=parts[f"{prefix}_num"].astype(float)[den > 0] / den[den > 0])
        by_key = {key: g["m"].to_numpy(dtype=float) for key, g in rates.groupby(keys, sort=False)}
        values = []
        for key in out[keys].itertuples(index=False, name=None):
            ms = by_key.get(key, np.empty(0))
            n = len(ms)
            if n == 0:
                values.append(np.nan)
                continue
            p = 1.0 if (ms >= 1).any() else 1 - np.exp(np.log(1 - ms).sum())
            values.append(1 - (1 - p) ** (k / n))
        result[m.name] = values
    return result
